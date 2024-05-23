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
async def test_user_read_functions(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Test the read functions of the User model"""

    # Set up test data
    await setup_data(session)

    # Test the read_all function
    all_users = [user async for user in User.read_all(session)]
    assert len(all_users) == 2

    # Test the read_all_by_ids function
    first_user, second_user = all_users[0], all_users[1]
    users_by_ids = [
        user
        async for user in User.read_all_by_ids(session, [first_user.id, second_user.id])
    ]
    assert len(users_by_ids) == 2

    # Test the read_by_email function
    user_by_email = await User.read_by_email(session, "user1@example.com")
    assert user_by_email is not None
    assert user_by_email.username == "user1"


@pytest.mark.anyio
async def test_user_create_and_update_functions(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Test the create and update functions of the User model"""

    # Set up test data
    await setup_data(session)

    # Test the create function
    new_user = await User.create(
        session,
        username="new_user",
        email="new_user@example.com",
        first_name="New",
        last_name="User",
        notification_type=NotificationType.EMAIL,
    )

    # Verify the new user creation
    created_user = await User.read_by_id(session, new_user.id)
    assert created_user is not None
    assert created_user.username == "new_user"

    # Test the update function
    await created_user.update(session, first_name="UpdatedNew")

    # Verify the update
    updated_user = await User.read_by_id(session, new_user.id)
    assert updated_user is not None
    assert updated_user.first_name == "UpdatedNew"


@pytest.mark.anyio
async def test_user_delete_function(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Test the delete function of the User model"""

    # Set up test data
    await setup_data(session)

    # Test the create function
    new_user = await User.create(
        session,
        username="new_user_delete",
        email="new_user_delete@example.com",
        first_name="New",
        last_name="User",
        notification_type=NotificationType.EMAIL,
    )

    # Verify the new user creation
    created_user = await User.read_by_id(session, new_user.id)
    assert created_user is not None
    assert created_user.username == "new_user_delete"
    created_user_id = created_user.id

    # Logically Delete the user
    await User.delete(session, created_user_id)

    # Verify the deletion
    deleted_user = await User.read_by_id(session, created_user_id)
    assert deleted_user is not None
    assert deleted_user.deleted_at is not None
