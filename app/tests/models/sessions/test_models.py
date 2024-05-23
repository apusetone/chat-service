from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from pytest_mock import MockFixture
from sqlalchemy.ext.asyncio import AsyncSession

from app.commons.types import NotificationType, PlatformType
from app.models import Session, User

now_datetime = datetime(2023, 3, 5, 10, 52, 33)


async def setup_data(a_session: AsyncSession) -> None:
    # Userモデルのインスタンスを作成
    user1 = User(
        username="user1",
        email="user1@example.com",
        new_email="new-user1@example.com",
        notification_type=NotificationType.DISABLED,
        first_name="User",
        last_name="One",
        is_name_visible=True,
        deleted_at=None,
        created_at=now_datetime,
        updated_at=now_datetime,
    )
    user2 = User(
        username="user2",
        email="user2@example.com",
        new_email=None,
        notification_type=NotificationType.EMAIL,
        first_name="User",
        last_name="Two",
        is_name_visible=True,
        deleted_at=None,
        created_at=now_datetime,
        updated_at=now_datetime,
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
        created_at=now_datetime,
        updated_at=now_datetime,
    )
    session2 = Session(
        user_id=user1.id,
        device_token="device_token_ios",
        platform_type=PlatformType.IOS,
        refresh_token="refresh_token_2",
        refresh_token_expired_at=datetime.now(UTC) + timedelta(days=30),
        created_at=now_datetime,
        updated_at=now_datetime,
    )
    session3 = Session(
        user_id=user2.id,
        device_token="device_token_android",
        platform_type=PlatformType.ANDROID,
        refresh_token="refresh_token_3",
        refresh_token_expired_at=datetime.now(UTC) + timedelta(days=30),
        created_at=now_datetime,
        updated_at=now_datetime,
    )
    a_session.add_all([session1, session2, session3])
    await a_session.flush()

    await a_session.commit()


@pytest.mark.anyio
async def test_session_read_functions(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Test the read functions of the Session model"""

    # Set up test data
    await setup_data(session)

    # Test the read_all function
    all_users = [user async for user in User.read_all(session)]
    assert len(all_users) == 2

    # Test the read_all_mobile function
    first_user, second_user = all_users[0], all_users[1]
    mobile_sessions = [
        session
        async for session in Session.read_all_mobile(
            session, [first_user.id, second_user.id]
        )
    ]
    assert len(mobile_sessions) == 2

    # Test the read_by_user_id_and_refresh_token function
    user1 = await User.read_by_email(session, "user1@example.com")
    assert user1 is not None
    user1_session = await Session.read_by_user_id_and_refresh_token(
        session, user_id=user1.id, refresh_token="refresh_token_1"
    )
    assert user1_session is not None
    assert user1_session.device_token is None
    first_session = mobile_sessions[0]

    # Test the read_by_id function
    session_by_id = await Session.read_by_id(session, session_id=first_session.id)
    assert session_by_id is not None
    assert session_by_id.platform_type == PlatformType.IOS


@pytest.mark.anyio
async def test_session_create_and_update_functions(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Test the create and update functions of the Session model"""

    # Set up test data
    await setup_data(session)

    # Test the create function
    user1 = await User.read_by_email(session, "user1@example.com")
    assert user1 is not None
    new_session = await Session.create(
        session,
        user_id=user1.id,
        device_token="new_device_token",
        platform_type=PlatformType.ANDROID,
        refresh_token="new_refresh_token",
        refresh_token_expired_at=datetime.now(UTC) + timedelta(days=30),
    )

    # Verify the new session creation
    created_session = await Session.read_by_id(session, session_id=new_session.id)
    assert created_session is not None
    assert created_session.device_token == "new_device_token"

    # Test the update function
    await created_session.update(session, device_token="updated_device_token")

    # Verify the update
    updated_session = await Session.read_by_id(session, session_id=new_session.id)
    assert updated_session is not None
    assert updated_session.device_token == "updated_device_token"


@pytest.mark.anyio
async def test_session_delete_function(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Test the delete function of the Session model"""

    # Set up test data
    await setup_data(session)

    # Test the create function
    user1 = await User.read_by_email(session, "user1@example.com")
    assert user1 is not None
    new_session = await Session.create(
        session,
        user_id=user1.id,
        device_token="new_device_token",
        platform_type=PlatformType.ANDROID,
        refresh_token="new_refresh_token",
        refresh_token_expired_at=datetime.now(UTC) + timedelta(days=30),
    )

    # Verify the new session creation
    created_session = await Session.read_by_id(session, session_id=new_session.id)
    assert created_session is not None
    assert created_session.device_token == "new_device_token"
    new_session_id = new_session.id

    # Test the delete function
    user1_id = user1.id
    await Session.delete(session, user_id=user1_id, refresh_token="new_refresh_token")

    # Verify the deletion
    deleted_session = await Session.read_by_id(session, session_id=new_session_id)
    assert deleted_session is None
