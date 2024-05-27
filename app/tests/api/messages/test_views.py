from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from pytest_mock import MockFixture
from sqlalchemy.ext.asyncio import AsyncSession

from app.commons.redis_cache import RedisCache
from app.commons.types import ChatType, NotificationType, PlatformType
from app.models import Chat, ChatParticipants, Message, Session, User

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

    # Chat.read_allを使用して最初のチャットを取得
    first_chat = None
    async for chat in Chat.read_all(session, user_id=1, offset=0, limit=1, desc=True):
        first_chat = chat
        break

    assert first_chat is not None, "No chat was found."

    chat_id = first_chat.id

    # execute
    response = await ac.get(
        f"/api/messages/chat/{chat_id}?offset=0&limit=10",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
    )

    # Message.read_allを使用して最初のメッセージを取得
    messages = []

    # Message.read_allを使用してメッセージを取得し、messagesリストに追加
    async for message in Message.read_all(session, chat_id=chat_id, offset=0, limit=10):
        messages.append(
            {
                "id": message.id,
                "sender_id": message.sender_id,
                "content": message.content,
                "created_at": message.created_at.isoformat(),
                "read_by_list": message.read_by_list,
            }
        )

    assert 200 == response.status_code
    expected = {"messages": messages}
    response_data = response.json()
    assert expected == response_data


@pytest.mark.anyio
async def test_messages_read_all_unauthorized(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """ReadAll messages with unauthorized access"""

    # setup
    await setup_data(session)

    # Chat.read_allを使用して最初のチャットを取得
    first_chat = None
    async for chat in Chat.read_all(session, user_id=1, offset=0, limit=1, desc=True):
        first_chat = chat
        break

    assert first_chat is not None, "No chat was found."

    chat_id = first_chat.id

    # execute
    response = await ac.get(
        f"/api/messages/chat/{chat_id}?offset=0&limit=10",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
    )

    # verify
    assert 401 == response.status_code
    expected = {
        "detail": ["Invalid authentication credentials"],
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_messages_read_all_nonexistent_chat(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """ReadAll messages with nonexistent chat ID"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    # Chat.read_allを使用して最初のチャットを取得
    first_chat = None
    async for chat in Chat.read_all(session, user_id=1, offset=0, limit=1, desc=True):
        first_chat = chat
        break

    assert first_chat is not None, "No chat was found."

    chat_id = first_chat.id

    # execute
    response = await ac.get(
        "/api/messages/chat/9999?offset=0&limit=10",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
    )

    # Message.read_allを使用して最初のメッセージを取得
    messages = []

    # Message.read_allを使用してメッセージを取得し、messagesリストに追加
    async for message in Message.read_all(session, chat_id=chat_id, offset=0, limit=10):
        messages.append(
            {
                "id": message.id,
                "sender_id": message.sender_id,
                "content": message.content,
                "created_at": message.created_at.isoformat(),
                "read_by_list": message.read_by_list,
            }
        )

    # verify
    assert 403 == response.status_code
    expected = {"detail": ["Forbidden"]}
    assert expected == response.json()


@pytest.mark.anyio
async def test_messages_read_all_with_high_offset(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """ReadAll messages with high offset resulting in no messages"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    first_chat = None
    async for chat in Chat.read_all(session, user_id=1, offset=0, limit=1, desc=True):
        first_chat = chat
        break

    assert first_chat is not None, "No chat was found."

    chat_id = first_chat.id

    # execute
    response = await ac.get(
        f"/api/messages/chat/{chat_id}?offset=1000&limit=10&desc=true",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
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
async def test_messages_read_all_with_negative_offset(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """ReadAll messages with negative offset value"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    first_chat = None
    async for chat in Chat.read_all(session, user_id=1, offset=0, limit=1, desc=True):
        first_chat = chat
        break

    assert first_chat is not None, "No chat was found."

    chat_id = first_chat.id

    # execute
    response = await ac.get(
        f"/api/messages/chat/{chat_id}?offset=-1&limit=10&desc=true",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
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
async def test_messages_read_all_with_high_limit(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """ReadAll messages with high limit exceeding total messages"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    first_chat = None
    async for chat in Chat.read_all(session, user_id=1, offset=0, limit=1, desc=True):
        first_chat = chat
        break

    assert first_chat is not None, "No chat was found."

    chat_id = first_chat.id

    # execute
    response = await ac.get(
        f"/api/messages/chat/{chat_id}?offset=0&limit=1000&desc=true",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
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
async def test_messages_read_all_with_negative_limit(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """ReadAll messages with negative limit value"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    first_chat = None
    async for chat in Chat.read_all(session, user_id=1, offset=0, limit=1, desc=True):
        first_chat = chat
        break

    assert first_chat is not None, "No chat was found."

    chat_id = first_chat.id

    # execute
    response = await ac.get(
        f"/api/messages/chat/{chat_id}?offset=0&limit=-10&desc=true",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
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
async def test_messages_read_all_with_non_integer_offset(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """ReadAll messages with non-integer offset value"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    first_chat = None
    async for chat in Chat.read_all(session, user_id=1, offset=0, limit=1, desc=True):
        first_chat = chat
        break

    assert first_chat is not None, "No chat was found."

    chat_id = first_chat.id

    # execute
    response = await ac.get(
        f"/api/messages/chat/{chat_id}?offset=abc&limit=10&desc=true",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
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
async def test_messages_read_all_with_non_integer_limit(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """ReadAll messages with non-integer limit value"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    first_chat = None
    async for chat in Chat.read_all(session, user_id=1, offset=0, limit=1, desc=True):
        first_chat = chat
        break

    assert first_chat is not None, "No chat was found."

    chat_id = first_chat.id

    # execute
    response = await ac.get(
        f"/api/messages/chat/{chat_id}?offset=0&limit=abc&desc=true",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
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
async def test_messages_create(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Create"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    # Chat.read_allを使用して最初のチャットを取得
    first_chat = None
    async for chat in Chat.read_all(session, user_id=1, offset=0, limit=1, desc=True):
        first_chat = chat
        break

    assert first_chat is not None, "No chat was found."

    chat_id = first_chat.id

    # execute
    response = await ac.post(
        f"/api/messages/chat/{chat_id}",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={"content": "Posted Message 1"},
    )

    # Message.read_allを使用して最初のメッセージを取得
    first_message = None
    async for message in Message.read_all(session, chat_id=chat_id, offset=0, limit=1):
        first_message = message
        break

    assert first_message is not None, "No message was found."

    assert 201 == response.status_code
    expected = {
        "id": first_message.id,
        "sender_id": 1,
        "content": "Posted Message 1",
        "created_at": first_message.created_at.isoformat(),
        "read_by_list": [],
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_messages_create_unauthorized(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Create with expired or invalid token"""

    # setup
    await setup_data(session)

    # Chat.read_allを使用して最初のチャットを取得
    first_chat = None
    async for chat in Chat.read_all(session, user_id=1, offset=0, limit=1, desc=True):
        first_chat = chat
        break

    assert first_chat is not None, "No chat was found."

    chat_id = first_chat.id

    # execute
    response = await ac.post(
        f"/api/messages/chat/{chat_id}",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={"content": "Posted Message 1"},
    )

    # verify
    assert 401 == response.status_code
    expected = {
        "detail": ["Invalid authentication credentials"],
    }
    assert expected == response.json()


@pytest.mark.anyio
async def test_messages_create_nonexistent_chat(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Create with nonexistent chat ID"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    # execute
    response = await ac.post(
        f"/api/messages/chat/{999999999}",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={"content": "Posted Message 1"},
    )

    # verify
    assert 403 == response.status_code
    expected = {"detail": ["Forbidden"]}
    assert expected == response.json()


@pytest.mark.anyio
async def test_messages_create_with_empty_content(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Create message with empty content"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    first_chat = None
    async for chat in Chat.read_all(session, user_id=1, offset=0, limit=1, desc=True):
        first_chat = chat
        break

    assert first_chat is not None, "No chat was found."

    chat_id = first_chat.id

    # execute
    response = await ac.post(
        f"/api/messages/chat/{chat_id}",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={"content": ""},
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
async def test_messages_create_with_too_long_content(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Create message with content that is too long"""

    # setup
    await setup_data(session)

    mocker.patch.object(
        RedisCache,
        "scan_with_suffix",
        return_value={"user_id": 1},
    )

    first_chat = None
    async for chat in Chat.read_all(session, user_id=1, offset=0, limit=1, desc=True):
        first_chat = chat
        break

    assert first_chat is not None, "No chat was found."

    chat_id = first_chat.id

    long_content = "A" * 5001  # assuming the max length is 5000 characters

    # execute
    response = await ac.post(
        f"/api/messages/chat/{chat_id}",
        headers={"Authorization": "Bearer zT4ypB0BuzQRDJKkvPh1U2wQFStaH8tv"},
        json={"content": long_content},
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
