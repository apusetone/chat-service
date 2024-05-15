import json
import logging
import threading
from contextlib import asynccontextmanager

import redis
import redis.asyncio as aredis
import yaml

from app.settings import settings

from .types import CacheType

logger = logging.getLogger(__name__)


class RedisCache:
    cache_type: CacheType
    _instances: dict[CacheType, "RedisCache"] = {}
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, cache_type: CacheType, expiry: int = 60 * 60 * 24 * 1):
        with cls._lock:
            if cache_type not in cls._instances:
                instance = super(RedisCache, cls).__new__(cls)
                instance.uri = settings.REDIS_URI
                instance.cache_type = cache_type
                instance.expiry = expiry
                cls._instances[cache_type] = instance
            return cls._instances[cache_type]

    def __init__(self, cache_type: CacheType, expiry: int = 60 * 60 * 24 * 1):
        # インスタンスが既に存在する場合は初期化をスキップ
        if type(self)._instances.get(self.cache_type) is not self.__class__:
            self.uri = settings.REDIS_URI
            self.cache_type = cache_type
            self.expiry = expiry

    @asynccontextmanager
    async def _get_redis_connection(self):
        cache = aredis.from_url(
            f"{self.uri}/{self.cache_type}", encoding="utf-8", decode_responses=True
        )
        try:
            yield cache
        finally:
            await cache.aclose()

    async def get(self, key: str) -> dict | None:
        async with self._get_redis_connection() as cache:
            try:
                json_str = await cache.get(key)
                if json_str:
                    return yaml.load(json_str, Loader=yaml.SafeLoader)
                return None
            except redis.exceptions.RedisError:
                return None

    async def scan_with_suffix(self, suffix: str) -> dict | None:
        async with self._get_redis_connection() as cache:
            try:
                cursor = "0"
                while cursor != 0:
                    cursor, scan_keys = await cache.scan(cursor=cursor, match=f"*{suffix}")
                    if scan_keys:
                        json_str = await cache.get(scan_keys[0])
                        if json_str:
                            return yaml.safe_load(json_str)
                return None
            except redis.exceptions.RedisError:
                return None

    async def set(self, key: str, value: object, expiry=None) -> bool:
        async with self._get_redis_connection() as cache:
            try:
                json_str = json.dumps(value, ensure_ascii=False)
                result = await cache.set(
                    key, json_str, ex=expiry if expiry else self.expiry
                )
                return bool(result)
            except redis.exceptions.RedisError:
                logger.warning("RedisCache failed to set.", exc_info=True)
                return False

    async def delete(self, key: str) -> bool:
        async with self._get_redis_connection() as cache:
            try:
                result = await cache.delete(key)
                return bool(result)
            except redis.exceptions.RedisError:
                return False

    async def delete_with_prefix(self, prefix: str) -> int | None:
        async with self._get_redis_connection() as cache:
            try:
                cursor = "0"
                deleted_count = 0
                while cursor != 0:
                    cursor, scan_keys = await cache.scan(cursor=cursor, match=f"{prefix}*")
                    for key in scan_keys:
                        deleted_count += await cache.delete(key)
                return deleted_count
            except redis.exceptions.RedisError:
                return None
