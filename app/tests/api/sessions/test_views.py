from datetime import UTC, datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from pytest_mock import MockFixture
from sqlalchemy.ext.asyncio import AsyncSession

from app.commons.redis_cache import RedisCache
from app.commons.types import NotificationType, PlatformType
from app.models import Session, User

now_datetime = datetime(2023, 3, 5, 10, 52, 33)


async def setup_data(a_session: AsyncSession) -> None:

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
async def test_sessions_update(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Update"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    # execute
    response = await ac.put(
        "/api/sessions",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={
            "refresh_token": "refresh_token_1",
            "device_token": "5dcaed99-e1e0-44dc-bde2-b96188b99e9e",
            "platform_type": "ios",
        },
    )

    assert 204 == response.status_code

    # Retrieve the latest session to compare with the request body
    latest_session = await Session.read_by_refresh_token(session, "refresh_token_1")
    assert latest_session is not None, "No session was found."
    assert (
        latest_session.refresh_token != "invalid_refresh_token"
    ), "The refresh token should not have been updated with invalid data."
    assert (
        latest_session.device_token == "5dcaed99-e1e0-44dc-bde2-b96188b99e9e"
    ), "The device token should remain unchanged."
    assert (
        latest_session.platform_type == PlatformType.IOS
    ), "The platform type should remain unchanged."


@pytest.mark.anyio
async def test_sessions_update_refresh_token_too_long(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Update failure due to refresh token being too long"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    session_instance = Session(
        user_id=1,
        device_token="5dcaed99-e1e0-44dc-bde2-b96188b99e9e",
        platform_type=PlatformType.IOS,
        refresh_token="refresh_token_1",
        refresh_token_expired_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    session.add(session_instance)
    await session.flush()

    # execute
    long_refresh_token = "a" * 256  # too long
    response = await ac.put(
        "/api/sessions",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={
            "refresh_token": long_refresh_token,
            "device_token": "5dcaed99-e1e0-44dc-bde2-b96188b99e9e",
            "platform_type": "ios",
        },
    )

    # verify
    assert 400 == response.status_code
    expected_error_response = {
        "error_code": "BAD_REQUEST",
        "message": "Request parameters validation failed",
        "detail": [],
    }
    assert expected_error_response == response.json()


@pytest.mark.anyio
async def test_sessions_update_device_token_too_long(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Update failure due to device token being too long"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    session_instance = Session(
        user_id=1,
        device_token="5dcaed99-e1e0-44dc-bde2-b96188b99e9e",
        platform_type=PlatformType.IOS,
        refresh_token="refresh_token_1",
        refresh_token_expired_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    session.add(session_instance)
    await session.flush()

    # execute
    long_device_token = "a" * 256  # too long
    response = await ac.put(
        "/api/sessions",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={
            "refresh_token": "valid_refresh_token",
            "device_token": long_device_token,
            "platform_type": "ios",
        },
    )

    # verify
    assert 400 == response.status_code
    expected_error_response = {
        "error_code": "BAD_REQUEST",
        "message": "Request parameters validation failed",
        "detail": [],
    }
    assert expected_error_response == response.json()


@pytest.mark.anyio
async def test_sessions_update_platform_type_too_short(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Update failure due to platform type being too short"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    session_instance = Session(
        user_id=1,
        device_token="5dcaed99-e1e0-44dc-bde2-b96188b99e9e",
        platform_type=PlatformType.IOS,
        refresh_token="refresh_token_1",
        refresh_token_expired_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    session.add(session_instance)
    await session.flush()

    # execute
    response = await ac.put(
        "/api/sessions",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={
            "refresh_token": "valid_refresh_token",
            "device_token": "5dcaed99-e1e0-44dc-bde2-b96188b99e9e",
            "platform_type": "",  # too short
        },
    )

    # verify
    assert 400 == response.status_code
    expected_error_response = {
        "error_code": "BAD_REQUEST",
        "message": "Request parameters validation failed",
        "detail": [],
    }
    assert expected_error_response == response.json()


@pytest.mark.anyio
async def test_sessions_update_platform_type_too_long(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Update failure due to platform type being too long"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    session_instance = Session(
        user_id=1,
        device_token="5dcaed99-e1e0-44dc-bde2-b96188b99e9e",
        platform_type=PlatformType.IOS,
        refresh_token="refresh_token_1",
        refresh_token_expired_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    session.add(session_instance)
    await session.flush()

    # execute
    long_platform_type = "a" * 256  # too long
    response = await ac.put(
        "/api/sessions",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={
            "refresh_token": "valid_refresh_token",
            "device_token": "5dcaed99-e1e0-44dc-bde2-b96188b99e9e",
            "platform_type": long_platform_type,
        },
    )

    # verify
    assert 400 == response.status_code
    expected_error_response = {
        "error_code": "BAD_REQUEST",
        "message": "Request parameters validation failed",
        "detail": [],
    }
    assert expected_error_response == response.json()
