from datetime import datetime, timedelta, timezone

import boto3
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.commons.logging import logger
from app.commons.redis_cache import RedisCache
from app.commons.types import CacheType, TokenType
from app.commons.utils import generate_random_token, generate_two_fa_code
from app.db import AsyncSession
from app.models import Session, User
from app.settings import settings

from .schema import LoginResponse, RefreshResponse, TwoFaRequest, TwoFaResponse


class Login:
    def __init__(self) -> None:
        self.redis_cache = RedisCache(cache_type=CacheType.TWO_FA)
        self.client = (
            None
            if settings.ENV == "local"
            else boto3.client("ses", region_name="ap-northeast-1")
        )

    async def execute(self, email: str) -> LoginResponse:
        generated_random_token = generate_random_token(32)
        generated_two_fa_code = generate_two_fa_code(6)

        await self.redis_cache.set(
            key=generated_random_token,
            value={"code": generated_two_fa_code, "email": email},
            expiry=120,
        )
        body = {"Text": {"Data": generated_two_fa_code, "Charset": "UTF-8"}}

        if self.client:
            response = self.client.send_email(
                Source="{} <{}>".format("SENDER", "from-address@test.com"),
                Destination={
                    "ToAddresses": [email],
                },
                Message={
                    "Subject": {"Data": "[chat-service] 2fa", "Charset": "UTF-8"},
                    "Body": body,
                },
            )
            logger.info(response)
        else:
            logger.info(body)

        return LoginResponse(token=generated_random_token)


class TwoFa:
    def __init__(self, session: AsyncSession) -> None:
        self.async_session = session
        self.get_redis_cache = RedisCache(cache_type=CacheType.TWO_FA)
        self.set_redis_cache = RedisCache(cache_type=CacheType.ACCESS_TOKEN)

    async def execute(self, token: str, code: str) -> TwoFaResponse:
        two_fa_dict = await self.get_redis_cache.get(token)

        if two_fa_dict is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=["Invalid code"],
            )

        two_fa_dict.update({"token": token})
        two_fa = TwoFaRequest(**two_fa_dict)
        if two_fa.code != code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=["Invalid code"],
            )

        async with self.async_session.begin() as session:
            email = two_fa_dict["email"]

            # Attempt to retrieve the user by the provided email
            user = await User.read_by_email(session, email)

            # If the user does not exist, create a new user
            if user is None:
                try:
                    # Attempt to create a new user
                    user = await User.create(session, email=email)
                except IntegrityError:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=["Email already exists."],
                    )

            user_id = user.id

            # Create a new session for the user
            refresh_token = generate_random_token(32)
            await Session.create(
                session,
                user_id=user_id,
                refresh_token=refresh_token,
                refresh_token_expired_at=datetime.now(timezone.utc)
                + timedelta(days=90),
            )

        # Set a new accsess_token for the user
        access_token = generate_random_token(32)
        await self.set_redis_cache.set(
            f"{user_id}:{access_token}",
            {"user_id": user_id},
        )

        return TwoFaResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type=TokenType.ACCESS_TOKEN,
            id=user_id,
        )


class Refresh:
    def __init__(self, session: AsyncSession) -> None:
        self.async_session = session
        self.redis_cache = RedisCache(cache_type=CacheType.ACCESS_TOKEN)

    async def execute(self, refresh_token: str) -> RefreshResponse:
        async with self.async_session() as session:
            session_instance = await Session.read_by_refresh_token(
                session, refresh_token
            )
            if not session_instance:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=["Session not found or expired"],
                )

            user_id = session_instance.user_id

            # Remove old access_tokens
            await self.redis_cache.delete_with_prefix(str(user_id))

            new_access_token = generate_random_token(32)
            await self.redis_cache.set(
                f"{user_id}:{new_access_token}",
                {"user_id": user_id},
            )

            return RefreshResponse(
                access_token=new_access_token,
                token_type=TokenType.REFRESH_TOKEN,
                id=user_id,
            )


class Logout:
    def __init__(self, session: AsyncSession) -> None:
        self.async_session = session
        self.redis_cache = RedisCache(cache_type=CacheType.ACCESS_TOKEN)

    async def execute(
        self, user_id: int, access_token: str, refresh_token: str
    ) -> None:
        async with self.async_session.begin() as session:
            await Session.delete(session, user_id, refresh_token)

            # Remove the old access_token
            await self.redis_cache.delete(f"{user_id}:{access_token}")

            return None


class Unregister:
    def __init__(self, session: AsyncSession) -> None:
        self.async_session = session
        self.redis_cache = RedisCache(cache_type=CacheType.ACCESS_TOKEN)

    async def execute(self, user_id: int) -> None:
        async with self.async_session.begin() as session:
            await User.delete(session, user_id)

            # Remove all the old access_tokens
            await self.redis_cache.delete_with_prefix(str(user_id))

            return None
