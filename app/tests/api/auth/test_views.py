import random
import string
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from pytest_mock import MockFixture
from sqlalchemy.ext.asyncio import AsyncSession

from app.commons.redis_cache import RedisCache
from app.commons.types import NotificationType, PlatformType
from app.models import Session, User
from app.settings import settings


async def setup_data(a_session: AsyncSession) -> None:

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
    await setup_data(session)

    mocker.patch(
        "app.commons.utils.secrets.choice",
        return_value="a",
    )
    mocker.patch("app.commons.utils.random.randint", return_value=0)

    # execute
    response = await ac.post("/api/auth/login", json={"email": "user1@example.com"})

    assert 201 == response.status_code
    expected = {
        "token": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_auth_two_fa(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """TwoFa"""

    # setup
    await setup_data(session)

    mocker.patch(
        "app.commons.utils.secrets.choice",
        return_value="a",
    )
    mocker.patch("app.commons.utils.random.randint", return_value=0)

    # add to redis
    response = await ac.post("/api/auth/login", json={"email": "user1@example.com"})

    # execute
    response = await ac.post(
        "/api/auth/2fa",
        json={"code": "000000", "token": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
    )

    assert 201 == response.status_code
    expected = {
        "access_token": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "id": 1,
        "refresh_token": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "token_type": "access_token",
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_auth_refresh(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Refresh"""

    # setup
    await setup_data(session)

    mocker.patch(
        "app.commons.utils.secrets.choice",
        return_value="b",
    )
    mocker.patch("app.commons.utils.random.randint", return_value=0)

    # execute
    response = await ac.post(
        "/api/auth/refresh", headers={"Authorization": "Bearer refresh_token_1"}
    )

    assert 201 == response.status_code
    expected = {
        "access_token": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "token_type": "refresh_token",
        "id": 1,
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_auth_logout(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Logout"""

    # setup
    await setup_data(session)

    mocker.patch(
        "app.commons.utils.secrets.choice",
        return_value="a",
    )
    mocker.patch("app.commons.utils.random.randint", return_value=0)

    # auth
    response = await ac.post("/api/auth/login", json={"email": "user1@example.com"})
    response = await ac.post(
        "/api/auth/2fa",
        json={"code": "000000", "token": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
    )

    # execute
    response = await ac.post(
        "/api/auth/logout",
        headers={"Authorization": "Bearer aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
        json={
            "refresh_token": "refresh_token_1",
        },
    )

    assert 201 == response.status_code


@pytest.mark.anyio
async def test_auth_unregister(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Unregister"""

    # setup
    await setup_data(session)

    mocker.patch(
        "app.commons.utils.secrets.choice",
        return_value="a",
    )
    mocker.patch("app.commons.utils.random.randint", return_value=0)

    # auth
    response = await ac.post("/api/auth/login", json={"email": "user1@example.com"})
    response = await ac.post(
        "/api/auth/2fa",
        json={"code": "000000", "token": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
    )

    # execute
    response = await ac.delete(
        "/api/auth/unregister",
        headers={"Authorization": "Bearer aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
    )

    assert 204 == response.status_code
