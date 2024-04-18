from fastapi import WebSocket, WebSocketDisconnect, status

from app.db import AsyncSessionLocal, PubSubSession, ws_clients
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

        # Chatのクライアント
        client_id = f"{chat_id}:{user_id}"
        ws_clients[client_id] = websocket

        try:
            while True:
                data = await websocket.receive_text()
                request = CreateMessageRequest(content=data)
                # websocket接続中のユーザーがいる場合既読扱い
                current_participants = [
                    participant_id
                    for key, _ in ws_clients.items()
                    if (participant_id := int(key.split(":")[1])) != user_id
                    and int(key.split(":")[0]) == chat_id
                ]
                response = await self.use_case.execute(
                    user_id, chat_id, current_participants, request
                )

                # 通知送信処理
                self.notification_repo.send_notifications(
                    user,
                    request.content,
                    chat_participants,
                    mail_client,
                    push_client,
                    sessions,
                )

                # 同じChat内にのみブロードキャスト
                # TODO: インスタンス1つのときのみ有効、Bidirectional Redis PubSub対応必要
                for key, client in ws_clients.items():
                    if int(key.split(":")[0]) == chat_id:
                        await client.send_json(response.model_dump())
        except Exception:
            del ws_clients[client_id]


class WebsocketEndpointView2:
    def __init__(self) -> None:
        self.async_session = AsyncSessionLocal
        self.pubsub_session = PubSubSession
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

        redis_instance = await self.pubsub_session()
        pubsub = redis_instance.pubsub()
        channel_name = f"chat_messages_{chat_id}"
        await pubsub.subscribe(channel_name)

        try:
            while True:
                data = await websocket.receive_text()
                request = CreateMessageRequest(content=data)

                # Redisチャネルからメッセージを受信してWebSocketクライアントに送信
                async for message in pubsub.listen():
                    if (
                        message["type"] == "message"
                        and message["channel"] == channel_name
                    ):
                        await websocket.send_text(message["data"])

                # websocket接続中のユーザーがいる場合既読扱い
                current_participants = await redis_instance.smembers(
                    f"active_users_{chat_id}"
                )
                current_participants = [
                    int(pid) for pid in current_participants if int(pid) != user_id
                ]
                response = await self.use_case.execute(
                    user_id, chat_id, current_participants, request
                )

                # 通知送信処理
                self.notification_repo.send_notifications(
                    user,
                    request.content,
                    chat_participants,
                    mail_client,
                    push_client,
                    sessions,
                )

                # 同じChat内にのみブロードキャスト
                await pubsub.publish(channel_name, response.model_dump())

        except WebSocketDisconnect:
            await pubsub.unsubscribe(channel_name)
            websocket.close()
