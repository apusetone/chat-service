from typing import AsyncIterator

from fastapi import HTTPException, status
from sqlalchemy import select

from app.commons.types import ChatType
from app.db import AsyncSession
from app.models import Chat, ChatParticipants, User

from .schema import (
    CreateChatRequest,
    CreateChatResponse,
    ReadAllChatParticipantResponse,
    ReadAllChatRequest,
    ReadAllChatResponse,
    ReadChatParticipantResponse,
    ReadChatResponse,
)


class ReadAllChat:
    def __init__(self, session: AsyncSession) -> None:
        self.async_session = session

    async def execute(
        self, user_id: int, params: ReadAllChatRequest
    ) -> AsyncIterator[ReadAllChatResponse]:
        async with self.async_session() as session:
            async for chat in Chat.read_all(session, user_id, **params.model_dump()):
                yield ReadChatResponse.model_validate(chat)


class ReadAllChatParticipant:
    def __init__(self, session: AsyncSession) -> None:
        self.async_session = session

    async def execute(
        self,
        user_id: int,
        chat_id: int,
    ) -> AsyncIterator[ReadAllChatParticipantResponse]:
        async with self.async_session() as session:
            # チャットの関係者でない場合は403エラーを返却する
            if (
                not (
                    await session.execute(
                        select(Chat).where(
                            Chat.id == chat_id, Chat.created_by == user_id
                        )
                    )
                ).scalar()
                and not (
                    await session.execute(
                        select(ChatParticipants).where(
                            ChatParticipants.chat_id == chat_id,
                            ChatParticipants.user_id == user_id,
                        )
                    )
                ).scalar()
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail=["Forbidden"]
                )

            # Chatを取得
            chat = await Chat.read_by_id(session, chat_id)
            if not chat:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=["Chat not found."]
                )

            # ChatParticipants.read_allを利用してチャット参加者を取得
            participant_ids = []
            participants = ChatParticipants.read_all(session, chat_id, 0, 10, False)
            async for participant in participants:
                participant_ids.append(participant.user_id)
            participant_ids.append(chat.created_by)

            # User.read_by_idsを利用してユーザーオブジェクトを取得
            async for user in User.read_all_by_ids(session, participant_ids):
                # ReadChatParticipantResponse.model_validateにユーザーリストを渡す
                if not user.is_name_visible:
                    user.first_name = "ANONYMOUS"
                    user.last_name = "ANONYMOUS"
                yield ReadChatParticipantResponse.model_validate(user)


class CreateChat:
    def __init__(self, session: AsyncSession) -> None:
        self.async_session = session

    async def execute(
        self, user_id: int, request: CreateChatRequest
    ) -> CreateChatResponse:
        async with self.async_session.begin() as session:
            # ユーザー名が参加者名に含まれているかチェック
            user = await User.read_by_id(session, user_id)
            if not user.username or user.username in request.participant_names:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=[
                        "Creator cannot be included as a chat participant or you have no username."
                    ],
                )

            # チャットを作成
            chat = Chat(
                created_by=user_id,
                chat_type=(
                    ChatType.DIRECT
                    if len(request.participant_names) < 2
                    else ChatType.GROUP
                ),
                name=request.name,
            )
            session.add(chat)
            await session.flush()  # チャットIDを取得するためにflush

            if request.participant_names:
                # 参加者のユーザーIDを取得
                participant_ids = await Chat.get_user_ids_by_names(
                    session, request.participant_names
                )

                if not participant_ids:
                    await session.rollback()
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=["One or more participant names do not exist"],
                    )

                # チャット参加者を作成
                for user_id in participant_ids:
                    new_participant = ChatParticipants(chat_id=chat.id, user_id=user_id)
                    session.add(new_participant)

            return CreateChatResponse.model_validate(chat)


class DeleteChat:
    def __init__(self, session: AsyncSession) -> None:
        self.async_session = session

    async def execute(self, user_id: int, chat_id: int) -> None:
        async with self.async_session.begin() as session:
            chat = await Chat.read_by_id_and_user_id(session, chat_id, user_id)
            if not chat:
                return
            await Chat.delete(session, chat_id, user_id)
