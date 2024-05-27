from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy import Column, ForeignKey, join, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, joinedload, relationship

from .base import TimestampedEntity
from .users import User


class ChatParticipants(TimestampedEntity):
    __tablename__ = "chat_participants"

    chat_id: Mapped[int] = Column(
        ForeignKey("chats.id", ondelete="CASCADE"), primary_key=True, nullable=False
    )  # type: ignore
    user_id: Mapped[int] = Column(
        ForeignKey("users.id"), primary_key=True, nullable=False
    )  # type: ignore

    chat = relationship("Chat", back_populates="participants")
    user = relationship("User", back_populates="chats")

    @classmethod
    async def read_all(
        cls, session: AsyncSession, chat_id: int, offset: int, limit: int, desc: bool
    ) -> AsyncIterator[ChatParticipants]:
        stmt = (
            select(cls)
            .where(cls.chat_id == chat_id)
            .order_by(cls.chat_id.desc() if desc else cls.chat_id)
            .offset(offset)
            .limit(limit)
        )
        stream = await session.stream_scalars(stmt)

        async for row in stream:
            yield row

    @classmethod
    async def read_all_active_notification_users(
        cls, session: AsyncSession, chat_id: int
    ) -> AsyncIterator[ChatParticipants]:
        stmt = (
            select(cls, User)
            .options(joinedload(ChatParticipants.user))
            .select_from(join(cls, User, cls.user_id == User.id))
            .where((cls.chat_id == chat_id) & (User.notification_type != 0))
        )
        stream = await session.stream_scalars(stmt)

        async for row in stream:
            yield row
