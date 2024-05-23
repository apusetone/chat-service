from datetime import datetime

import pytest
from httpx import AsyncClient
from pytest_mock import MockFixture
from sqlalchemy.ext.asyncio import AsyncSession

from app.commons.types import ChatType, NotificationType
from app.models import Chat, User

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

    await a_session.commit()


@pytest.mark.anyio
async def test_chat_read_functions(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Test the read functions of the Chat model"""

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

    # Test the read_by_id function
    chat_by_id = await Chat.read_by_id(session, chat_id=all_chats[0].id)
    assert chat_by_id is not None
    assert chat_by_id.name == "Chat 1"


@pytest.mark.anyio
async def test_chat_create_and_update_functions(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Test the create and update functions of the Chat model"""

    # Set up test data
    await setup_data(session)

    # Test the create function
    user = await User.read_by_email(session, "user1@example.com")
    assert user is not None
    new_chat = await Chat.create(
        session,
        created_by=user.id,
        chat_type=ChatType.DIRECT,
        name="New Chat",
    )

    # Verify the new chat creation
    created_chat = await Chat.read_by_id(session, chat_id=new_chat.id)
    assert created_chat is not None
    assert created_chat.name == "New Chat"

    # Test the update function
    await created_chat.update(session, name="Updated Chat")

    # Verify the update
    updated_chat = await Chat.read_by_id(session, chat_id=new_chat.id)
    assert updated_chat is not None
    assert updated_chat.name == "Updated Chat"


@pytest.mark.anyio
async def test_chat_delete_function(
    ac: AsyncClient, session: AsyncSession, mocker: MockFixture
) -> None:
    """Test the delete function of the Chat model"""

    # Set up test data
    await setup_data(session)

    # Test the create function
    user = await User.read_by_email(session, "user1@example.com")
    assert user is not None
    new_chat = await Chat.create(
        session,
        created_by=user.id,
        chat_type=ChatType.DIRECT,
        name="New Chat",
    )

    # Verify the new chat creation
    created_chat = await Chat.read_by_id(session, chat_id=new_chat.id)
    assert created_chat is not None
    assert created_chat.name == "New Chat"
    new_chat_id = new_chat.id

    # Test the delete function
    await Chat.delete(session, chat_id=new_chat_id, user_id=user.id)

    # Verify the deletion
    deleted_chat = await Chat.read_by_id(session, chat_id=new_chat_id)
    assert deleted_chat is None
