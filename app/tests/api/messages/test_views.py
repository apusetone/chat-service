from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from pytest_mock import MockFixture
from sqlalchemy.ext.asyncio import AsyncSession

from app.commons.redis_cache import RedisCache
from app.commons.types import ChatType

now_datetime = datetime(2023, 3, 5, 10, 52, 33)


async def setup_data(a_session: AsyncSession) -> None:
    from app.commons.types import NotificationType, PlatformType
    from app.models import Chat, ChatParticipants, Message, Session, User

    now = datetime(2023, 3, 5, 10, 52, 33)

    # Userモデルのインスタンスを作成
    user1 = User(
        id=1,
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
        id=2,
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
        id=1,
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
        user_id=user2.id,
        created_at=now,
        updated_at=now,
    )
    a_session.add_all([chat_participant1])
    await a_session.flush()

    # Messageモデルのインスタンスを作成
    message1 = Message(
        id=1,
        sender_id=user1.id,
        chat_id=chat1.id,
        content="Message content 1",
        read_by_list=[user2.id],
        created_at=now,
        updated_at=now,
    )
    message2 = Message(
        id=2,
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


@pytest.mark.anyio
async def test_messages_read_all(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """ReadAll"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    # execute
    response = await ac.get(
        "/api/messages/chat/1?offset=0&limit=10&desc=true",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
    )

    assert 200 == response.status_code
    expected = {
        "messages": [
            {
                "id": 2,
                "sender_id": 2,
                "content": "Message content 2",
                "created_at": now_datetime.isoformat(),
                "read_by_list": [1],
            },
            {
                "id": 1,
                "sender_id": 1,
                "content": "Message content 1",
                "created_at": now_datetime.isoformat(),
                "read_by_list": [2],
            },
        ]
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_messages_create(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Create"""

    # setup
    # await setup_data(session)

    # mocker.patch.object(
    #     RedisCache,
    #     "scan_with_suffix",
    #     return_value={"user_id": 1},
    # )

    # # # execute
    # response = await ac.post(
    #     "/api/messages/chat/1",
    #     headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
    #     json={"content": "Posted Message 1"},
    # )

    # assert 201 == response.status_code
    # expected = {
    #     "id": 3,
    #     "sender_id": 1,
    #     "content": "Posted Message 1",
    #     "created_at": now_datetime.isoformat(),
    #     "read_by_list": [],
    # }
    # assert expected == response.json()

    # TODO: skip test due to using dependencies=[Depends(RateLimiter(times=3, seconds=10))],
    pass


@pytest.mark.anyio
async def test_messages_delete(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Delete"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    # execute
    response = await ac.delete(
        "/api/messages/1",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
    )

    assert 204 == response.status_code