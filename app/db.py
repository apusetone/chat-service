import logging
from typing import Annotated, AsyncGenerator, AsyncIterator, Callable

from fastapi import Depends
from redis.asyncio import Redis, from_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.commons.types import CacheType
from app.settings import settings

logger = logging.getLogger(__name__)

async_engine = create_async_engine(
    settings.DB_URI,
    pool_pre_ping=True,
    echo=settings.ECHO_SQL,
)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    autoflush=False,
    future=True,
)

ws_clients = {}


async def get_session() -> AsyncIterator[async_sessionmaker]:
    try:
        yield AsyncSessionLocal
    except SQLAlchemyError as e:
        logger.exception(e)


AsyncSession = Annotated[async_sessionmaker, Depends(get_session)]


async def get_pubsub() -> AsyncGenerator[Redis, None]:
    redis_instance = from_url(
        f"{settings.REDIS_URI}/{CacheType.PUBSUB}",
        encoding="utf-8",
        decode_responses=True,
    )
    try:
        yield redis_instance
    finally:
        await redis_instance.close()


PubSubSession = Annotated[AsyncGenerator[Redis, None], Depends(get_pubsub)]
