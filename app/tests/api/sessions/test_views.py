from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from pytest_mock import MockFixture
from sqlalchemy.ext.asyncio import AsyncSession

now_datetime = datetime(2023, 3, 5, 10, 52, 33)


async def setup_data(a_session: AsyncSession) -> None:
    from app.commons.types import NotificationType, PlatformType
    from app.models import Session, User

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
        is_name_visible=True,
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

    await a_session.commit()


@pytest.mark.anyio
async def test_sessions_read(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Update"""

    # setup
    # await setup_data(session)

    # mocker.patch.object(FastAPILimiter, "init", return_value=MagicMock())
    # mocker.patch.object(RateLimiter, "__call__", return_value=MagicMock())
    # mocker.patch.object(
    #     utils, "generate_random_token", return_value="zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"
    # )
    # mocker.patch.object(utils, "generate_two_fa_code", return_value="123456")
    # mocker.patch.object(
    #     RedisCache,
    #     "scan_with_suffix",
    #     return_value={"user_id": 1},
    # )

    # # execute
    # response = await ac.update(
    #     "/api/sessions",
    #     headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
    #     json={
    #         "refresh_token": "refresh_token_1",
    #         "device_token": "5dcaed99-e1e0-44dc-bde2-b96188b99e9e",
    #         "platform_type": "ios",
    #     },
    # )

    # assert 204 == response.status_code

    # TODO: skip test due to using dependencies=[Depends(RateLimiter(times=3, seconds=10))],
    pass
