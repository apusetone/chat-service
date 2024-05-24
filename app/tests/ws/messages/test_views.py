import time
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import Header, WebSocket
from fastapi.testclient import TestClient
from httpx import AsyncClient
from pytest_mock import MockFixture
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.testclient import TestClient

from app.commons.authentication import AccessTokenSchema
from app.commons.redis_cache import RedisCache
from app.commons.types import ChatType, NotificationType, PlatformType
from app.models import Chat, ChatParticipants, Message, Session, User
from app.models.schema import AccessTokenSchema

now_datetime = datetime(2023, 3, 5, 10, 52, 33)


async def setup_data(a_session: AsyncSession) -> None:

    now = datetime(2023, 3, 5, 10, 52, 33)

    # Userモデルのインスタンスを作成
    user1 = User(
        username="user1",
        email="user1@example.com",
        new_email=None,
        notification_type=NotificationType.DISABLED,
        first_name="User",
        last_name="One",
        is_name_visible=True,
        deleted_at=None,
        created_at=now,
        updated_at=now,
    )
    user2 = User(
        username="user2",
        email="user2@example.com",
        new_email=None,
        notification_type=NotificationType.EMAIL,
        first_name="User",
        last_name="Two",
        is_name_visible=False,
        deleted_at=None,
        created_at=now,
        updated_at=now,
    )
    a_session.add_all([user1, user2])
    await a_session.flush()

    # Sessionモデルのインスタンスを作成
    session1 = Session(
        user_id=user1.id,
        device_token=None,
        platform_type=None,
        refresh_token="refresh_token_1",
        refresh_token_expired_at=datetime.now(UTC) + timedelta(days=30),
        created_at=now,
        updated_at=now,
    )
    session2 = Session(
        user_id=user1.id,
        device_token="device_token_ios",
        platform_type=PlatformType.IOS,
        refresh_token="refresh_token_2",
        refresh_token_expired_at=datetime.now(UTC) + timedelta(days=30),
        created_at=now,
        updated_at=now,
    )
    session3 = Session(
        user_id=user2.id,
        device_token="device_token_android",
        platform_type=PlatformType.ANDROID,
        refresh_token="refresh_token_3",
        refresh_token_expired_at=datetime.now(UTC) + timedelta(days=30),
        created_at=now,
        updated_at=now,
    )
    a_session.add_all([session1, session2, session3])
    await a_session.flush()

    # Chatモデルのインスタンスを作成
    chat1 = Chat(
        created_by=user1.id,
        chat_type=ChatType.DIRECT,
        name="Chat name 1",
        created_at=now,
        updated_at=now,
    )
    a_session.add_all([chat1])
    await a_session.flush()

    # ChatParticipantsモデルのインスタンスを作成
    chat_participant1 = ChatParticipants(
        chat_id=chat1.id,
        user_id=user1.id,
        created_at=now,
        updated_at=now,
    )
    chat_participant2 = ChatParticipants(
        chat_id=chat1.id,
        user_id=user2.id,
        created_at=now,
        updated_at=now,
    )
    a_session.add_all([chat_participant1, chat_participant2])
    await a_session.flush()

    # Messageモデルのインスタンスを作成
    message1 = Message(
        sender_id=user1.id,
        chat_id=chat1.id,
        content="Message content 1",
        read_by_list=[user2.id],
        created_at=now,
        updated_at=now,
    )
    message2 = Message(
        sender_id=user2.id,
        chat_id=chat1.id,
        content="Message content 2",
        read_by_list=[user1.id],
        created_at=now,
        updated_at=now,
    )
    a_session.add_all([message1, message2])
    await a_session.flush()

    await a_session.commit()


# テスト関数内でモックを設定
@pytest.mark.anyio
async def test_messages_create(
    mocker: MockFixture, session: AsyncSession, ac: AsyncClient, client: TestClient
) -> None:
    """Create"""

    # setup
    await setup_data(session)

    # RedisCacheのscan_with_suffixメソッドをモック
    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    # Chat.read_allを使用して最初のチャットを取得
    user = await User.read_by_email(session, "user1@example.com")
    assert user is not None
    first_chat = None
    async for chat in Chat.read_all(
        session, user_id=user.id, offset=0, limit=1, desc=True
    ):
        first_chat = chat
        break

    assert first_chat is not None, "No chat was found."

    chat_id = first_chat.id

    # execute
    with client.websocket_connect(
        f"/ws/messages/chat/{chat_id}",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        session=session,
    ) as ws:
        # メッセージを投稿する
        ws.send("Hello world!")

        # サーバーからのレスポンスを受け取る
        # TODO: 現在のセッションに結びついたサーバプロセスのプロセスIDを共有できないため、setup_dataでinsertしたデータが存在できない
        response = ws.receive()

        # レスポンスが期待通りであることを確認する
        assert response == {
            "id": 40,
            "sender_id": user.id,
            "content": "Hello world!",
            "created_at": "2024-05-23T13:37:23.004184",
            "read_by_list": [],
        }
