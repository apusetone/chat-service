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
    from app.models import Chat, ChatParticipants, Session, User

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
    user3 = User(
        id=3,
        username="user3",
        email="user3@example.com",
        new_email=None,
        notification_type=NotificationType.MOBILE_PUSH,
        first_name="User",
        last_name="Three",
        is_name_visible=False,
        deleted_at=None,
        created_at=now,
        updated_at=now,
    )
    a_session.add_all([user1, user2, user3])
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

    await a_session.commit()


@pytest.mark.anyio
async def test_chats_read_all(
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
        "/api/chats?offset=0&limit=10&desc=true",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
    )

    assert 200 == response.status_code
    expected = {
        "chats": [
            {
                "id": 1,
                "created_at": now_datetime.isoformat(),
                "updated_at": now_datetime.isoformat(),
                "chat_type": "direct",
                "name": "Chat name 1",
            }
        ]
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_chats_create(
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

    # # execute
    # response = await ac.post(
    #     "/api/chats",
    #     headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
    #     json={
    #         "name": "New room",
    #         "participant_names": ["user2", "user3"],
    #     },
    # )

    # assert 201 == response.status_code
    # expected = {
    #     "id": 2,
    #     "created_at": now_datetime.isoformat(),
    #     "updated_at": now_datetime.isoformat(),
    #     "chat_type": "direct",
    #     "name": "New room",
    # }
    # assert expected == response.json()

    # TODO: skip test due to using dependencies=[Depends(RateLimiter(times=3, seconds=10))],
    pass


@pytest.mark.anyio
async def test_chats_read_all_participants(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """ReadAllParticipants"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    # execute
    response = await ac.get(
        "/api/chats/1/participants",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
    )

    assert 200 == response.status_code
    expected = {
        "participants": [
            {
                "id": 1,
                "created_at": now_datetime.isoformat(),
                "updated_at": now_datetime.isoformat(),
                "first_name": "User",
                "last_name": "One",
                "username": "user1",
                "is_name_visible": True,
            },
            {
                "id": 2,
                "created_at": now_datetime.isoformat(),
                "updated_at": now_datetime.isoformat(),
                "first_name": "ANONYMOUS",
                "last_name": "ANONYMOUS",
                "username": "user2",
                "is_name_visible": False,
            },
        ]
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_chats_delete(
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
        "/api/chats/1",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
    )

    assert 204 == response.status_code