import json
import logging

import redis
import redis.asyncio as aredis
import yaml

from app.settings import settings

from .types import CacheType

logger = logging.getLogger(__name__)


class RedisCache:

    cache_type: CacheType

    def __init__(self, cache_type: CacheType, expiry=60 * 60 * 24 * 1):
        self.uri = settings.REDIS_URI
        self.cache_type = cache_type
        self.expiry = expiry

    async def get(self, key: str) -> dict | None:
        try:
            cache = aredis.from_url(
                f"{self.uri}/{self.cache_type}", encoding="utf-8", decode_responses=True
            )
            json_str = await cache.get(key)
            if json_str:
                return yaml.load(json_str, Loader=yaml.SafeLoader)
            return None
        except redis.exceptions.RedisError:
            return None

    async def scan_with_suffix(self, suffix: str) -> dict | None:
        try:
            cache = aredis.from_url(
                f"{self.uri}/{self.cache_type}", encoding="utf-8", decode_responses=True
            )
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
        try:
            cache = aredis.from_url(
                f"{self.uri}/{self.cache_type}", encoding="utf-8", decode_responses=True
            )
            json_str = json.dumps(value, ensure_ascii=False)
            result = await cache.set(
                key, json_str, ex=expiry if expiry else self.expiry
            )
            return bool(result)
        except redis.exceptions.RedisError:
            logger.warning("RedisCache failed to set.", exc_info=True)
            return False

    async def delete(self, key: str) -> bool:
        try:
            cache = aredis.from_url(
                f"{self.uri}/{self.cache_type}", encoding="utf-8", decode_responses=True
            )
            result = await cache.delete(key)
            return bool(result)
        except redis.exceptions.RedisError:
            return False

    async def delete_with_prefix(self, prefix: str) -> int | None:
        try:
            cache = aredis.from_url(
                f"{self.uri}/{self.cache_type}", encoding="utf-8", decode_responses=True
            )
            cursor = "0"
            deleted_count = 0
            while cursor != 0:
                cursor, scan_keys = await cache.scan(cursor=cursor, match=f"{prefix}*")
                for key in scan_keys:
                    deleted_count += await cache.delete(key)
            return deleted_count
        except redis.exceptions.RedisError:
            return None