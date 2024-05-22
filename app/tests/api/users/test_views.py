from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from pytest_mock import MockFixture
from sqlalchemy.ext.asyncio import AsyncSession

from app.commons.redis_cache import RedisCache

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
        new_email="new-user1@example.com",
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
async def test_users_read(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Read"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    # execute
    response = await ac.get(
        "/api/users",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
    )

    assert 200 == response.status_code
    expected = {
        "id": 1,
        "created_at": now_datetime.isoformat(),
        "updated_at": now_datetime.isoformat(),
        "is_name_visible": True,
        "username": "user1",
        "first_name": "User",
        "last_name": "One",
        "email": "user1@example.com",
        "new_email": "new-user1@example.com",
        "notification_type": "disabled",
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_users_read_failure(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Read failure"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value=None,
    )

    # execute
    response = await ac.get(
        "/api/users",
        headers={"Authorization": "Bearer invalid_or_expired_token"},
    )

    # verify
    assert 401 == response.status_code
    expected = {
        "detail": ["Invalid authentication credentials"],
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_users_update(
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
        "/api/users",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={
            "is_name_visible": False,
            "username": "testuser12345",
            "first_name": "John",
            "last_name": "Smith",
            "new_email": None,
            "notification_type": "mobile_push",
        },
    )

    assert 204 == response.status_code


@pytest.mark.anyio
async def test_users_update_failure(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Update failure due to invalid token"""

    # setup
    await setup_data(session)

    # execute
    response = await ac.put(
        "/api/users",
        headers={"Authorization": "Bearer invalid_or_expired_token"},
        json={
            "is_name_visible": False,
            "username": "testuser12345",
            "first_name": "John",
            "last_name": "Smith",
            "new_email": None,
            "notification_type": "mobile_push",
        },
    )

    # verify
    assert 401 == response.status_code
    expected = {
        "detail": ["Invalid authentication credentials"],
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_users_update_first_name_anonymous(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Update with first_name as 'ANONYMOUS'"""
    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    # execute
    response = await ac.put(
        "/api/users",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={
            "is_name_visible": False,
            "username": "testuser12345",
            "first_name": "ANONYMOUS",  # first_nameが"ANONYMOUS"
            "last_name": "Smith",
            "new_email": None,
            "notification_type": "mobile_push",
        },
    )
    # verify
    assert 400 == response.status_code
    expected = {
        "error_code": "BAD_REQUEST",
        "message": "Request parameters validation failed",
        "detail": [],
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_users_update_last_name_anonymous(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Update with last_name as 'ANONYMOUS'"""
    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    # execute
    response = await ac.put(
        "/api/users",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={
            "is_name_visible": False,
            "username": "testuser12345",
            "first_name": "John",
            "last_name": "ANONYMOUS",  # last_nameが"ANONYMOUS"
            "new_email": None,
            "notification_type": "mobile_push",
        },
    )
    # verify
    assert 400 == response.status_code
    expected = {
        "error_code": "BAD_REQUEST",
        "message": "Request parameters validation failed",
        "detail": [],
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_users_update_invalid_request_format(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Update failure due to invalid request format"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    # execute
    response = await ac.put(
        "/api/users",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={
            "is_name_visible": "not_a_boolean",
            "username": 123,  # should be a string
            "first_name": "John",
            "last_name": "Smith",
            "new_email": None,
            "notification_type": "mobile_push",
        },
    )

    # verify
    assert 400 == response.status_code
    expected = {
        "detail": [],
        "error_code": "BAD_REQUEST",
        "message": "Request parameters validation failed",
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_users_update_username_too_long(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Update failure due to username being too long"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    # execute
    long_username = "a" * 256  # Assuming the max length allowed is less than 256
    response = await ac.put(
        "/api/users",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={
            "is_name_visible": True,
            "username": long_username,
            "first_name": "John",
            "last_name": "Smith",
            "new_email": None,
            "notification_type": "mobile_push",
        },
    )

    # verify
    assert 400 == response.status_code
    expected = {
        "detail": [],
        "error_code": "BAD_REQUEST",
        "message": "Request parameters validation failed",
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_users_update_first_name_too_long(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Update failure due to first name being too long"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    # execute
    long_first_name = "a" * 256  # Assuming the max length allowed is less than 256
    response = await ac.put(
        "/api/users",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={
            "is_name_visible": True,
            "username": "valid_username",
            "first_name": long_first_name,
            "last_name": "Smith",
            "new_email": None,
            "notification_type": "mobile_push",
        },
    )

    # verify
    assert 400 == response.status_code
    expected = {
        "detail": [],
        "error_code": "BAD_REQUEST",
        "message": "Request parameters validation failed",
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_users_update_first_name_wrong_type(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Update failure due to first name being an array"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    # execute
    response = await ac.put(
        "/api/users",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={
            "is_name_visible": True,
            "username": "valid_username",
            "first_name": ["John"],  # should be a string
            "last_name": "Smith",
            "new_email": None,
            "notification_type": "mobile_push",
        },
    )

    # verify
    assert 400 == response.status_code
    expected = {
        "detail": [],
        "error_code": "BAD_REQUEST",
        "message": "Request parameters validation failed",
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_users_update_last_name_too_long(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Update failure due to last name being too long"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    # execute
    long_last_name = "a" * 256  # Assuming the max length allowed is less than 256
    response = await ac.put(
        "/api/users",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={
            "is_name_visible": True,
            "username": "valid_username",
            "first_name": "John",
            "last_name": long_last_name,
            "new_email": None,
            "notification_type": "mobile_push",
        },
    )

    # verify
    assert 400 == response.status_code
    expected = {
        "detail": [],
        "error_code": "BAD_REQUEST",
        "message": "Request parameters validation failed",
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_users_update_last_name_wrong_type(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Update failure due to last name being a boolean"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    # execute
    response = await ac.put(
        "/api/users",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={
            "is_name_visible": True,
            "username": "valid_username",
            "first_name": "John",
            "last_name": True,  # should be a string
            "new_email": None,
            "notification_type": "mobile_push",
        },
    )

    # verify
    assert 400 == response.status_code
    expected = {
        "detail": [],
        "error_code": "BAD_REQUEST",
        "message": "Request parameters validation failed",
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_users_update_new_email_wrong_type(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Update failure due to new email being an integer"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    # execute
    response = await ac.put(
        "/api/users",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={
            "is_name_visible": True,
            "username": "valid_username",
            "first_name": "John",
            "last_name": "Smith",
            "new_email": 123,  # should be a string or None
            "notification_type": "mobile_push",
        },
    )

    # verify
    assert 400 == response.status_code
    expected = {
        "detail": [],
        "error_code": "BAD_REQUEST",
        "message": "Request parameters validation failed",
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_users_update_notification_type_too_long(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Update failure due to notification type being too long"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    # execute
    long_notification_type = (
        "a" * 256
    )  # Assuming the max length allowed is less than 256
    response = await ac.put(
        "/api/users",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={
            "is_name_visible": True,
            "username": "valid_username",
            "first_name": "John",
            "last_name": "Smith",
            "new_email": None,
            "notification_type": long_notification_type,
        },
    )

    # verify
    assert 400 == response.status_code
    expected = {
        "detail": [],
        "error_code": "BAD_REQUEST",
        "message": "Request parameters validation failed",
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_users_update_notification_type_wrong_type(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Update failure due to notification type being an integer"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    # execute
    response = await ac.put(
        "/api/users",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={
            "is_name_visible": True,
            "username": "valid_username",
            "first_name": "John",
            "last_name": "Smith",
            "new_email": None,
            "notification_type": 123,  # should be a string
        },
    )

    # verify
    assert 400 == response.status_code
    expected = {
        "detail": [],
        "error_code": "BAD_REQUEST",
        "message": "Request parameters validation failed",
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_users_update_is_name_visible_wrong_type(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Update failure due to is_name_visible being a string"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    # execute
    response = await ac.put(
        "/api/users",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={
            "is_name_visible": "OK",  # should be a boolean
            "username": "valid_username",
            "first_name": "John",
            "last_name": "Smith",
            "new_email": None,
            "notification_type": "mobile_push",
        },
    )

    # verify
    assert 400 == response.status_code
    expected = {
        "detail": [],
        "error_code": "BAD_REQUEST",
        "message": "Request parameters validation failed",
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_users_partial_update(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """PartialUpdate"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )
    mocker.patch.object(
        RedisCache,
        "get",
        return_value={"code": "123456"},
    )

    # execute
    response = await ac.patch(
        "/api/users/verify_email",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={"code": "123456"},
    )

    assert 204 == response.status_code


@pytest.mark.anyio
async def test_users_partial_update_invalid_code(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """PartialUpdate with invalid code"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )
    mocker.patch.object(
        RedisCache,
        "get",
        return_value={"code": "123456"},
    )

    # execute
    response = await ac.patch(
        "/api/users/verify_email",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={"code": "wrong_code"},
    )

    # verify
    assert 400 == response.status_code
    expected = {
        "detail": [],
        "error_code": "BAD_REQUEST",
        "message": "Request parameters validation failed",
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_users_partial_update_expired_token(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """PartialUpdate with expired or invalid token"""

    # setup
    await setup_data(session)

    # execute
    response = await ac.patch(
        "/api/users/verify_email",
        headers={"Authorization": "Bearer expired_or_invalid_token"},
        json={"code": "123456"},
    )

    # verify
    assert 401 == response.status_code
    expected = {
        "detail": ["Invalid authentication credentials"],
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_users_partial_update_code_wrong_type(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """PartialUpdate failure due to code being an integer"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )
    mocker.patch.object(
        RedisCache,
        "get",
        return_value={"code": "123456"},
    )

    # execute
    response = await ac.patch(
        "/api/users/verify_email",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={"code": 123},  # should be a string
    )

    # verify
    assert 400 == response.status_code
    expected = {
        "detail": [],
        "error_code": "BAD_REQUEST",
        "message": "Request parameters validation failed",
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_users_partial_update_code_too_short(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """PartialUpdate failure due to code being too short"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )
    mocker.patch.object(
        RedisCache,
        "get",
        return_value={"code": "123456"},
    )

    # execute
    response = await ac.patch(
        "/api/users/verify_email",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={"code": "12"},  # too short
    )

    # verify
    assert 400 == response.status_code
    expected = {
        "detail": [],
        "error_code": "BAD_REQUEST",
        "message": "Request parameters validation failed",
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_users_partial_update_code_too_long(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """PartialUpdate failure due to code being too long"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )
    mocker.patch.object(
        RedisCache,
        "get",
        return_value={"code": "123456"},
    )

    # execute
    response = await ac.patch(
        "/api/users/verify_email",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={"code": "1234567"},  # too long
    )

    # verify
    assert 400 == response.status_code
    expected = {
        "detail": [],
        "error_code": "BAD_REQUEST",
        "message": "Request parameters validation failed",
    }
    assert expected == response.json()
