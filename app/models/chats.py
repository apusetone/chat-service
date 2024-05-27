from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy import Column, ForeignKey, Index, Integer, String, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, relationship

from app.commons.types import ChatType

from .base import TimestampedEntity
from .chat_participants import ChatParticipants
from .users import User


class Chat(TimestampedEntity):
    __tablename__ = "chats"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True, autoincrement=True)  # type: ignore
    created_by: Mapped[int] = Column(ForeignKey("users.id"), nullable=False)  # type: ignore
    chat_type: Mapped[ChatType] = Column(Integer, nullable=False)  # type: ignore
    name: Mapped[str] = Column(String(length=255), nullable=False)  # type: ignore

    messages = relationship("Message", back_populates="chat", cascade="all, delete")
    participants = relationship(
        "ChatParticipants", back_populates="chat", cascade="all, delete"
    )
    creator = relationship("User", back_populates="created_chats")

    __table_args__ = (
        Index("ix_chats_created_at", "created_at"),
        Index("ix_chats_created_by", "created_by"),
        Index("ix_chats_name", "name"),
        Index("ix_chats_updated_at", "updated_at"),
    )

    @classmethod
    async def read_all(
        cls, session: AsyncSession, user_id: int, offset: int, limit: int, desc: bool
    ) -> AsyncIterator[Chat]:
        # CTE (Common Table Expression) を定義
        user_chats_cte = (
            select(ChatParticipants.chat_id)
            .where(ChatParticipants.user_id == user_id)
            .cte("user_chats")
        )

        # メインクエリでCTEを使用
        stmt = (
            select(cls)
            .where(
                or_(
                    cls.id.in_(select(user_chats_cte.c.chat_id)),
                    cls.created_by == user_id,
                )
            )
            .order_by(cls.id.desc() if desc else cls.id)
            .offset(offset)
            .limit(limit)
        )
        stream = await session.stream_scalars(stmt)

        async for row in stream:
            yield row

    @classmethod
    async def read_by_id(cls, session: AsyncSession, chat_id: int) -> Chat | None:
        stmt = select(cls).where(cls.id == chat_id)
        return await session.scalar(stmt.order_by(cls.id))

    @classmethod
    async def read_by_id_and_user_id(
        cls, session: AsyncSession, chat_id: int, user_id: int
    ) -> Chat | None:
        stmt = select(cls).where(cls.id == chat_id, cls.created_by == user_id)
        return await session.scalar(stmt.order_by(cls.id))

    @classmethod
    async def create(cls, session: AsyncSession, **kwargs) -> Chat:
        session_instance = cls(**kwargs)
        session.add(session_instance)
        await session.flush()
        return session_instance

    @classmethod
    async def get_user_ids_by_names(
        cls, session: AsyncSession, names: list[str]
    ) -> list[int]:
        stmt = select(User.id).where(User.username.in_(names))
        result = await session.execute(stmt)
        return list(result.scalars())

    async def update(self, session: AsyncSession, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)
        await session.flush()

    @classmethod
    async def delete(cls, session: AsyncSession, chat_id: int, user_id: int) -> None:
        session_instance = await cls.read_by_id_and_user_id(session, chat_id, user_id)
        if session_instance:
            await session.delete(session_instance)
            await session.flush()
