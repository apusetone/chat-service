from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    Integer,
    String,
    delete,
    func,
    select,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.commons.types import NotificationType

from .base import TimestampedEntity
from .sessions import Session


class User(TimestampedEntity):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        "id", Integer, autoincrement=True, nullable=False, unique=True, primary_key=True
    )
    username: Mapped[str] = mapped_column(
        "username", String(length=32), nullable=True, unique=True
    )
    email: Mapped[str] = mapped_column(
        "email", String(length=255), nullable=False, unique=True
    )
    new_email: Mapped[str] = mapped_column(
        "new_email", String(length=255), nullable=True
    )
    notification_type: Mapped[NotificationType] = mapped_column(
        "notification_type", Integer, nullable=False, default=NotificationType.DISABLED
    )
    first_name: Mapped[str] = mapped_column(
        "first_name", String(length=30), nullable=True
    )
    last_name: Mapped[str] = mapped_column(
        "last_name", String(length=30), nullable=True
    )
    is_name_visible: Mapped[bool] = mapped_column(
        "is_name_visible", Boolean, default=True
    )
    deleted_at: Mapped[DateTime] = mapped_column(
        "deleted_at", DateTime(timezone=True), default=None, nullable=True
    )

    sessions = relationship("Session", back_populates="user")
    created_chats = relationship("Chat", back_populates="creator")
    sent_messages = relationship("Message", back_populates="sender")
    chats = relationship("ChatParticipants", back_populates="user")

    __table_args__ = (
        Index("ix_users_username", "username"),
        Index("ix_users_first_name", "first_name"),
        Index("ix_users_last_name", "last_name"),
    )

    @classmethod
    async def read_all(cls, session: AsyncSession) -> AsyncIterator[User]:
        stmt = select(cls)
        stream = await session.stream_scalars(stmt.order_by(cls.id))
        async for row in stream:
            yield row

    @classmethod
    async def read_all_by_ids(
        cls, session: AsyncSession, user_ids: list[int]
    ) -> AsyncIterator[User]:
        stmt = select(cls).where(cls.id.in_(user_ids))
        stream = await session.stream_scalars(stmt.order_by(cls.id))
        async for row in stream:
            yield row

    @classmethod
    async def read_by_id(cls, session: AsyncSession, user_id: int) -> User | None:
        stmt = select(cls).where(cls.id == user_id)
        return await session.scalar(stmt.order_by(cls.id))

    @classmethod
    async def read_by_email(cls, session: AsyncSession, email: str) -> User | None:
        # flake8: noqa: E711
        stmt = select(cls).where(cls.email == email, cls.deleted_at == None)
        return await session.scalar(stmt.order_by(cls.id))

    @classmethod
    async def create(cls, session: AsyncSession, **kwargs) -> User:
        user = cls(**kwargs)
        session.add(user)
        await session.flush()
        return user

    async def update(self, session: AsyncSession, **kwargs) -> None:
        notification_type = kwargs.pop("notification_type", None)
        if notification_type is not None:
            notification_value = NotificationType[notification_type.upper()].value
            setattr(self, "notification_type", notification_value)
        for key, value in kwargs.items():
            setattr(self, key, value)
        await session.flush()

    @classmethod
    async def delete(cls, session: AsyncSession, user_id: int) -> None:
        # Userを論理削除し、new_emailをNone、notification_typeをDISABLED、updated_atを更新
        await session.execute(
            update(cls)
            .where(cls.id == user_id)
            .values(
                deleted_at=func.now(),
                new_email=None,
                updated_at=func.now(),
                notification_type=NotificationType.DISABLED,
            )
        )
        # 関連するSessionを物理削除
        await session.execute(
            delete(Session).where(
                Session.user_id == user_id,
            )
        )
        await session.commit()
