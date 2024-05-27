from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy import Column, ForeignKey, Index, Integer, String, select, update
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, relationship

from .base import TimestampedEntity


class Message(TimestampedEntity):
    __tablename__ = "messages"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True, autoincrement=True) # type: ignore
    chat_id: Mapped[int] = Column(ForeignKey("chats.id"), nullable=False) # type: ignore
    sender_id: Mapped[int] = Column(ForeignKey("users.id"), nullable=False) # type: ignore
    content: Mapped[str] = Column(String(length=1024), nullable=False) # type: ignore
    read_by_list: Mapped[list[int]] = Column(ARRAY(Integer), server_default="{}") # type: ignore

    chat = relationship("Chat", back_populates="messages")
    sender = relationship("User", back_populates="sent_messages")

    __table_args__ = (
        Index("ix_messages_sender_id", "sender_id"),
        Index("ix_messages_content", "content"),
        Index("ix_messages_created_at", "created_at"),
    )

    @classmethod
    async def read_all(
        cls, session: AsyncSession, chat_id: int, offset: int, limit: int
    ) -> AsyncIterator[Message]:
        stmt = (
            select(cls)
            .where(cls.chat_id == chat_id)
            .order_by(cls.id.desc())
            .offset(offset)
            .limit(limit)
        )
        stream = await session.stream_scalars(stmt.order_by(cls.id))
        async for row in stream:
            yield row

    @classmethod
    async def read_by_id(cls, session: AsyncSession, message_id: int) -> Message | None:
        stmt = select(cls).where(cls.id == message_id)
        return await session.scalar(stmt.order_by(cls.id))

    @classmethod
    async def read_by_id_and_user_id(
        cls, session: AsyncSession, message_id: int, user_id: int
    ) -> Message | None:
        stmt = select(cls).where(cls.id == message_id, cls.sender_id == user_id)
        return await session.scalar(stmt.order_by(cls.id))

    @classmethod
    async def create(cls, session: AsyncSession, **kwargs) -> Message:
        message = cls(**kwargs)
        session.add(message)
        await session.flush()
        return message

    async def update(self, session: AsyncSession, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)
        await session.flush()

    @classmethod
    async def update_read_by_list(
        cls, session: AsyncSession, message_ids: list[int], user_id: int
    ) -> None:
        stmt = (
            update(cls)
            .where(cls.id.in_(message_ids))
            .values({cls.read_by_list: cls.read_by_list.op("||")(user_id)})
            .where(~cls.read_by_list.any(user_id)) # type: ignore
            .returning(cls.id)
        )
        await session.execute(stmt)
        await session.flush()

    @classmethod
    async def delete(cls, session: AsyncSession, message_id: int, user_id: int) -> None:
        message = await cls.read_by_id_and_user_id(session, message_id, user_id)
        if message:
            await session.delete(message)
            await session.flush()
