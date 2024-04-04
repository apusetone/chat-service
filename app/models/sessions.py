from __future__ import annotations

import os
from typing import AsyncIterator

from sqlalchemy import Column, DateTime, ForeignKey, Integer, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, relationship

from app.commons.type_decorators import PGPString
from app.commons.types import PlatformType

from .base import TimestampedEntity

secret = os.environ["SECRET"]


class Session(TimestampedEntity):
    __tablename__ = "sessions"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = Column(ForeignKey("users.id"), nullable=False)
    device_token: Mapped[PGPString] = Column(PGPString, nullable=True)
    platform_type: Mapped[PlatformType] = Column(Integer, nullable=True)
    refresh_token: Mapped[PGPString] = Column(PGPString, nullable=False)
    refresh_token_expired_at: Mapped[DateTime] = Column(
        DateTime(timezone=True), nullable=False
    )

    user = relationship("User", back_populates="sessions")

    @classmethod
    async def read_all(cls, session: AsyncSession) -> AsyncIterator[Session]:
        stmt = select(cls)
        stream = await session.stream_scalars(stmt.order_by(cls.id))
        async for row in stream:
            yield row

    @classmethod
    async def read_all_mobile(
        cls, session: AsyncSession, user_ids: list[int]
    ) -> AsyncIterator[Session]:
        stmt = (
            select(cls)
            .where(cls.device_token.isnot(None))
            .where(cls.user_id.in_(user_ids), cls.platform_type != PlatformType.UNKNOWN)
        )
        stream = await session.stream_scalars(stmt.order_by(cls.id))
        async for row in stream:
            yield row

    @classmethod
    async def read_by_user_id_and_refresh_token(
        cls, session: AsyncSession, user_id: int, refresh_token: str
    ) -> Session | None:
        stmt = select(cls).where(
            cls.user_id == user_id,
            func.pgp_sym_decrypt(cls.refresh_token, secret) == refresh_token,
        )
        return await session.scalar(stmt.order_by(cls.id))

    @classmethod
    async def read_by_id(cls, session: AsyncSession, session_id: int) -> Session | None:
        stmt = select(cls).where(cls.id == session_id)
        return await session.scalar(stmt.order_by(cls.id))

    @classmethod
    async def read_by_refresh_token(
        cls, session: AsyncSession, refresh_token: str
    ) -> Session | None:
        stmt = select(cls).where(
            func.pgp_sym_decrypt(cls.refresh_token, secret) == refresh_token
        )
        return await session.scalar(stmt.order_by(cls.id))

    @classmethod
    async def create(cls, session: AsyncSession, **kwargs) -> Session:
        session_instance = cls(**kwargs)
        session.add(session_instance)
        await session.flush()
        return session_instance

    async def update(self, session: AsyncSession, **kwargs) -> None:
        platform_type = kwargs.pop("platform_type", None)
        if platform_type is not None:
            platform_value = PlatformType[platform_type.upper()].value
            setattr(self, "platform_type", platform_value)
        for key, value in kwargs.items():
            setattr(self, key, value)
        await session.flush()

    @classmethod
    async def delete(
        cls, session: AsyncSession, user_id: int, refresh_token: str
    ) -> None:
        await session.execute(
            delete(cls).where(
                cls.user_id == user_id,
                func.pgp_sym_decrypt(cls.refresh_token, secret) == refresh_token,
            )
        )
