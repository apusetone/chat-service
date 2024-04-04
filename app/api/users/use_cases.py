import boto3
from fastapi import HTTPException, status

from app.api.auth.schema import TwoFaRequest
from app.commons.logging import logger
from app.commons.redis_cache import RedisCache
from app.commons.types import CacheType
from app.commons.utils import generate_two_fa_code
from app.db import AsyncSession
from app.models import User, UserSchema
from app.models.schema import AccessTokenSchema
from app.settings import settings

from .schema import PartialUpdateUserRequest, UpdateUserRequest


class ReadUser:
    def __init__(self, session: AsyncSession) -> None:
        self.async_session = session

    async def execute(self, user_id: int) -> UserSchema:
        async with self.async_session() as session:
            user = await User.read_by_id(session, user_id)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
            return UserSchema.model_validate(user)


class UpdateUser:
    def __init__(self, session: AsyncSession) -> None:
        self.async_session = session
        self.redis_cache = RedisCache(cache_type=CacheType.TWO_FA)
        self.client = (
            None
            if settings.ENV == "local"
            else boto3.client("ses", region_name="ap-northeast-1")
        )

    async def execute(
        self, schema: AccessTokenSchema, request: UpdateUserRequest
    ) -> UserSchema:
        async with self.async_session.begin() as session:
            user = await User.read_by_id(session, schema.user_id)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
            new_email = request.new_email

            await user.update(session, **request.model_dump())
            await session.refresh(user)

            if new_email:
                generated_two_fa_code = generate_two_fa_code(6)

                await self.redis_cache.set(
                    key=schema.access_token,
                    value={"code": generated_two_fa_code},
                    expiry=120,
                )
                body = {"Text": {"Data": generated_two_fa_code, "Charset": "UTF-8"}}

                if self.client:
                    response = self.client.send_email(
                        Source="{} <{}>".format("SENDER", "from-address@test.com"),
                        Destination={
                            "ToAddresses": [new_email],
                        },
                        Message={
                            "Subject": {
                                "Data": "[chat-service] 2fa",
                                "Charset": "UTF-8",
                            },
                            "Body": body,
                        },
                    )
                    logger.info(response)
                else:
                    logger.info(body)

            return UserSchema.model_validate(user)


class PartialUpdateUser:
    def __init__(self, session: AsyncSession) -> None:
        self.async_session = session
        self.get_redis_cache = RedisCache(cache_type=CacheType.TWO_FA)

    async def execute(
        self, schema: AccessTokenSchema, request: PartialUpdateUserRequest
    ) -> UserSchema:
        two_fa_dict = await self.get_redis_cache.get(schema.access_token)

        if two_fa_dict is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid code",
            )

        two_fa_dict.update({"token": schema.access_token})
        two_fa = TwoFaRequest(**two_fa_dict)
        if two_fa.code != request.code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid code",
            )

        async with self.async_session.begin() as session:
            user = await User.read_by_id(session, schema.user_id)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

            new_email = user.new_email

            await user.update(session, email=new_email, new_email=None)
            await session.refresh(user)

            return UserSchema.model_validate(user)
