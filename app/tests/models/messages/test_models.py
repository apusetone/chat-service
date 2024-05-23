from datetime import datetime

import pytest
from httpx import AsyncClient
from pytest_mock import MockFixture
from sqlalchemy.ext.asyncio import AsyncSession

from app.commons.types import ChatType, NotificationType
from app.models import Chat, Message, User

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

    # Chatモデルのインスタンスを作成
    chat1 = Chat(
        created_by=user1.id,
        chat_type=ChatType.DIRECT,
        name="Chat 1",
        created_at=now_datetime,
        updated_at=now_datetime,
    )
    chat2 = Chat(
        created_by=user2.id,
        chat_type=ChatType.GROUP,
        name="Chat 2",
        created_at=now_datetime,
        updated_at=now_datetime,
    )
    a_session.add_all([chat1, chat2])
    await a_session.flush()

    # Messageモデルのインスタンスを作成
    message1 = Message(
        chat_id=chat1.id,
        sender_id=user1.id,
        content="Hello, this is message 1.",
        created_at=now_datetime,
        updated_at=now_datetime,
    )
    message2 = Message(
        chat_id=chat2.id,
        sender_id=user2.id,
        content="Hi, this is message 2.",
        created_at=now_datetime,
        updated_at=now_datetime,
    )
    a_session.add_all([message1, message2])
    await a_session.flush()

    await a_session.commit()


@pytest.mark.anyio
async def test_message_read_functions(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Test the read functions of the Message model"""

    # Set up test data
    await setup_data(session)

    # Test the read_all function
    user = await User.read_by_email(session, "user1@example.com")
    assert user is not None
    all_chats = [
        chat
        async for chat in Chat.read_all(
            session, user_id=user.id, offset=0, limit=10, desc=True
        )
    ]
    assert len(all_chats) == 1
    all_messages = [
        message
        async for message in Message.read_all(
            session, chat_id=all_chats[0].id, offset=0, limit=10
        )
    ]
    assert len(all_messages) == 1

    # Test the read_by_id function
    message_by_id = await Message.read_by_id(session, message_id=all_messages[0].id)
    assert message_by_id is not None
    assert message_by_id.content == "Hello, this is message 1."


@pytest.mark.anyio
async def test_message_create_and_update_functions(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Test the create and update functions of the Message model"""

    # Set up test data
    await setup_data(session)

    # Test the create function
    user = await User.read_by_email(session, "user1@example.com")
    assert user is not None
    all_chats = [
        chat
        async for chat in Chat.read_all(
            session, user_id=user.id, offset=0, limit=10, desc=True
        )
    ]
    new_message = await Message.create(
        session,
        chat_id=all_chats[0].id,
        sender_id=user.id,
        content="This is a new message.",
    )

    # Verify the new message creation
    created_message = await Message.read_by_id(session, message_id=new_message.id)
    assert created_message is not None
    assert created_message.content == "This is a new message."

    # Test the update function
    await created_message.update(session, content="Updated message.")

    # Verify the update
    updated_message = await Message.read_by_id(session, message_id=new_message.id)
    assert updated_message is not None
    assert updated_message.content == "Updated message."


@pytest.mark.anyio
async def test_message_delete_function(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Test the delete function of the Message model"""

    # Set up test data
    await setup_data(session)

    # Test the create function
    user = await User.read_by_email(session, "user1@example.com")
    assert user is not None
    all_chats = [
        chat
        async for chat in Chat.read_all(
            session, user_id=user.id, offset=0, limit=10, desc=True
        )
    ]
    new_message = await Message.create(
        session,
        chat_id=all_chats[0].id,
        sender_id=user.id,
        content="This is a new message.",
    )

    # Verify the new message creation
    created_message = await Message.read_by_id(session, message_id=new_message.id)
    assert created_message is not None
    assert created_message.content == "This is a new message."
    new_message_id = new_message.id

    # Test the delete function
    await Message.delete(session, message_id=new_message_id, user_id=user.id)

    # Verify the deletion
    deleted_message = await Message.read_by_id(session, message_id=new_message_id)
    assert deleted_message is None
