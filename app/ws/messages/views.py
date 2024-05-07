import asyncio
import json

from fastapi import WebSocket, WebSocketDisconnect, status
from starlette.websockets import WebSocketState

from app.commons.logging import logger
from app.db import AsyncSessionLocal, PubSubSessionLocal
from app.models.schema import AccessTokenSchema

from .repositories import (
    AwsClientRepository,
    ChatParticipantsRepository,
    ChatRepository,
    NotificationRepository,
    SessionRepository,
    UserRepository,
)
from .schema import CreateMessageRequest
from .use_cases import CreateMessage


class WebsocketEndpointView:
    def __init__(self) -> None:
        self.async_session = AsyncSessionLocal
        self.pubsub_session = PubSubSessionLocal
        self.chat_repo = ChatRepository(self.async_session)
        self.user_repo = UserRepository(self.async_session)
        self.chat_participants_repo = ChatParticipantsRepository(self.async_session)
        self.session_repo = SessionRepository(self.async_session)
        self.aws_repo = AwsClientRepository()
        self.notification_repo = NotificationRepository()
        self.use_case = CreateMessage(self.async_session)

    async def execute(
        self,
        websocket: WebSocket,
        chat_id: int,
        schema: AccessTokenSchema,
    ):
        user_id = schema.user_id

        chat, result = await self.chat_repo.verify_chat_participant(chat_id, user_id)
        if not result:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Userの取得
        user = await self.user_repo.get_user(user_id)

        # ChatParticipantsの取得
        chat_participants = [
            row async for row in self.chat_participants_repo.get_all(chat_id)
        ]

        # Sessionの取得
        sessions = [
            {"user_id": row.user_id, "session": row}
            async for row in self.session_repo.get_all(
                [
                    participant.user_id
                    for participant in chat_participants
                    if participant.user_id != user_id
                ]
                + ([] if user_id == chat.created_by else [user_id])
            )
        ]

        # boto3クライアントの初期化
        mail_client, push_client = self.aws_repo.get_ses_sns_client()

        pubsub = self.pubsub_session.pubsub()
        channel_name = f"chat_messages_{chat_id}"
        await pubsub.subscribe(channel_name)
        await self.pubsub_session.sadd(f"active_users_{chat_id}", user_id)

        # 排他制御用のロックを作成
        lock = asyncio.Lock()

        # 独立した pubsub インスタンスを作成する関数
        async def create_pubsub_instance(session, channel_name):
            pubsub = session.pubsub()
            await pubsub.subscribe(channel_name)
            return pubsub

        async def listen_to_pubsub(pubsub, lock, websocket):
            while True:
                async with lock:
                    message = await pubsub.get_message(ignore_subscribe_messages=True)
                    if message and message["type"] == "message":
                        await websocket.send_text(message["data"])

        async def receive_from_websocket(websocket, lock, pubsub):
            while True:
                data = await websocket.receive_text()
                if not data.strip():
                    continue

                # メッセージを処理してレスポンスを生成
                request = CreateMessageRequest(content=data)

                # メッセージを処理してレスポンスを生成
                current_participants = await self.pubsub_session.smembers(
                    f"active_users_{chat_id}"
                )
                current_participants = [
                    int(pid) for pid in current_participants if int(pid) != user_id
                ]
                response = await self.use_case.execute(
                    user_id, chat_id, current_participants, request
                )

                async with lock:
                    # レスポンスをRedisチャネルにブロードキャスト
                    response_data = response.model_dump()
                    if isinstance(response_data, dict):
                        response_data = json.dumps(response_data, ensure_ascii=False)
                    await self.pubsub_session.publish(channel_name, response_data)

                # 通知送信処理
                self.notification_repo.send_notifications(
                    user,
                    request.content,
                    chat_participants,
                    mail_client,
                    push_client,
                    sessions,
                )

        # 独立した pubsub インスタンスを作成
        listen_pubsub = await create_pubsub_instance(
            self.pubsub_session, f"chat_messages_{chat_id}"
        )
        receive_pubsub = await create_pubsub_instance(
            self.pubsub_session, f"chat_messages_{chat_id}"
        )

        # Pub/SubのリッスンとWebSocketの受信を並行して実行
        listen_task = asyncio.create_task(
            listen_to_pubsub(listen_pubsub, lock, websocket)
        )
        receive_task = asyncio.create_task(
            receive_from_websocket(websocket, lock, receive_pubsub)
        )

        try:
            # 両方のタスクが完了するまで待機
            await asyncio.gather(listen_task, receive_task)
        except WebSocketDisconnect as e:
            # WebSocketの切断処理
            logger.info(f"WebSocket disconnected with code: {e.code}")
        finally:
            # タスクのキャンセルと購読解除
            listen_task.cancel()
            receive_task.cancel()
            await listen_pubsub.unsubscribe(channel_name)
            await receive_pubsub.unsubscribe(channel_name)
            # クライアントの状態を確認
            if websocket.client_state != WebSocketState.DISCONNECTED:
                # クライアントがまだ接続されている場合はクローズ
                await websocket.close()
