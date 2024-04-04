from fastapi import (
    Depends,
    Header,
    HTTPException,
    WebSocket,
    WebSocketException,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.commons.redis_cache import RedisCache
from app.commons.types import CacheType
from app.models.schema import AccessTokenSchema, RefreshTokenSchema, TwoFaSchema

UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid authentication credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


class AccessTokenAuthentication:

    @classmethod
    async def get_current_user(
        cls,
        cred: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    ) -> AccessTokenSchema:
        if not cred:
            raise UNAUTHORIZED

        redis = RedisCache(cache_type=CacheType.ACCESS_TOKEN)
        result = await redis.scan_with_suffix(cred.credentials)
        if not result:
            raise UNAUTHORIZED

        return AccessTokenSchema(
            access_token=cred.credentials, user_id=result["user_id"]
        )


class TwoFaAuthentication:

    @classmethod
    async def get_current_user(
        cls,
        cred: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    ) -> TwoFaSchema:
        if not cred:
            raise UNAUTHORIZED

        redis = RedisCache(cache_type=CacheType.TWO_FA)
        result = await redis.get(cred.credentials)
        if not result:
            raise UNAUTHORIZED

        return TwoFaSchema(**result)


class RefreshTokenAuthentication:

    @classmethod
    async def get_current_user(
        cls,
        cred: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    ) -> RefreshTokenSchema:
        if not cred:
            raise UNAUTHORIZED

        return RefreshTokenSchema(refresh_token=cred.credentials)


async def websoket_headers(
    websocket: WebSocket,
    authorization: str | None = Header(default=None),
) -> RefreshTokenSchema:
    try:
        token = authorization[len("Bearer ") :]
    except:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Invalid authentication credentials",
        )

    if not token:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    redis = RedisCache(cache_type=CacheType.ACCESS_TOKEN)
    result = await redis.scan_with_suffix(token)
    if not result:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    return AccessTokenSchema(access_token=token, user_id=result["user_id"])
