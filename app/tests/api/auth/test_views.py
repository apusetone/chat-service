from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from pytest_mock import MockFixture
from sqlalchemy.ext.asyncio import AsyncSession

from app.commons.redis_cache import RedisCache


async def setup_data(a_session: AsyncSession) -> None:
    from app.commons.types import NotificationType, PlatformType
    from app.models import Session, User

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
    )
    user2 = User(
        id=2,
        username="user2",
        email="user2@example.com",
        new_email=None,
        notification_type=NotificationType.DISABLED,
        first_name="User",
        last_name="Two",
        is_name_visible=True,
        deleted_at=None,
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
    )
    session2 = Session(
        user_id=user1.id,
        device_token="device_token_ios",
        platform_type=PlatformType.IOS,
        refresh_token="refresh_token_2",
        refresh_token_expired_at=datetime.now(UTC) + timedelta(days=30),
    )
    session3 = Session(
        user_id=user2.id,
        device_token="device_token_android",
        platform_type=PlatformType.ANDROID,
        refresh_token="refresh_token_3",
        refresh_token_expired_at=datetime.now(UTC) + timedelta(days=30),
    )
    a_session.add_all([session1, session2, session3])
    await a_session.flush()

    await a_session.commit()


@pytest.mark.anyio
async def test_auth_login(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Login"""

    # setup
    # await setup_data(session)

    # mocker.patch.object(FastAPILimiter, "init", return_value=MagicMock())
    # mocker.patch.object(RateLimiter, "__call__", return_value=MagicMock())
    # mocker.patch.object(
    #     utils, "generate_random_token", return_value="zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"
    # )
    # mocker.patch.object(utils, "generate_two_fa_code", return_value="123456")

    # # execute
    # response = await ac.post("/api/auth/login", json={"email": "test_email@email.com"})

    # assert 201 == response.status_code
    # expected = {
    #     "token": "zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv",
    # }
    # assert expected == response.json()

    # TODO: skip test due to using dependencies=[Depends(RateLimiter(times=3, seconds=10))],
    pass


@pytest.mark.anyio
async def test_auth_two_fa(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """TwoFa"""

    # setup
    # await setup_data(session)

    # mocker.patch.object(FastAPILimiter, "init", return_value=MagicMock())
    # mocker.patch.object(RateLimiter, "__call__", return_value=MagicMock())
    # mocker.patch.object(
    #     utils, "generate_random_token", return_value="zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"
    # )
    # mocker.patch.object(utils, "generate_two_fa_code", return_value="123456")

    # # execute
    # response = await ac.post("/api/auth/2fa", json={"code": "123456", "token": "zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"})

    # assert 201 == response.status_code
    # expected = {"token": "zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"}
    # assert expected == response.json()

    # TODO: skip test due to using dependencies=[Depends(RateLimiter(times=3, seconds=10))],
    pass


@pytest.mark.anyio
async def test_auth_refresh(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Refresh"""

    # setup
    # await setup_data(session)

    # mocker.patch.object(
    #     utils, "generate_random_token", return_value="zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"
    # )
    # mocker.patch.object(utils, "generate_two_fa_code", return_value="123456")

    # # execute
    # response = await ac.post(
    #     "/api/auth/refresh", headers={"Authorization": "Bearer refresh_token_1"}
    # )

    # assert 201 == response.status_code
    # expected = {
    #     "access_token": "zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv",
    #     "token_type": "refresh_token",
    #     "id": 1,
    # }
    # assert expected == response.json()

    # TODO: skip test due to using dependencies=[Depends(RateLimiter(times=3, seconds=10))],
    pass


@pytest.mark.anyio
async def test_auth_logout(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Logout"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    # execute
    response = await ac.post(
        "/api/auth/logout",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={
            "refresh_token": "refresh_token_1",
        },
    )

    assert 201 == response.status_code

    # TODO: skip test due to using dependencies=[Depends(RateLimiter(times=3, seconds=10))],
    pass


@pytest.mark.anyio
async def test_auth_unregister(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Unregister"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )
    mocker.patch.object(
        RedisCache,
        "delete_with_prefix",
        return_value=None,
    )

    # execute
    response = await ac.delete(
        "/api/auth/unregister",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
    )

    assert 204 == response.status_code

    # TODO: skip test due to using dependencies=[Depends(RateLimiter(times=3, seconds=10))],
    pass
