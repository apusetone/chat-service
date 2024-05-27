import json
from typing import AsyncIterator

import boto3
from fastapi import HTTPException, status
from sqlalchemy import select

from app.commons.logging import logger
from app.commons.types import NotificationType, PlatformType
from app.db import AsyncSession
from app.models import Chat, ChatParticipants, Message, Session, User
from app.settings import settings

from .schema import (
    CreateMessageRequest,
    CreateMessageResponse,
    ReadAllMessageRequest,
    ReadAllMessageResponse,
    ReadMessageResponse,
)


class ReadAllMessage:
    def __init__(self, session: AsyncSession) -> None:
        self.async_session = session

    async def execute(
        self, user_id: int, chat_id: int, params: ReadAllMessageRequest
    ) -> AsyncIterator[ReadAllMessageResponse]:
        async with self.async_session.begin() as session:
            # Messageの関係者でない場合は403エラーを返却する
            if (
                not (
                    await session.execute(
                        select(Chat).where(
                            Chat.id == chat_id, Chat.created_by == user_id
                        )
                    )
                ).scalar()
                and not (
                    await session.execute(
                        select(ChatParticipants).where(
                            ChatParticipants.chat_id == chat_id,
                            ChatParticipants.user_id == user_id,
                        )
                    )
                ).scalar()
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail=["Forbidden"]
                )

            stmt = (
                select(Message)
                .where(Message.chat_id == chat_id)
                .order_by(Message.id.desc())
                .offset(params.offset)
                .limit(params.limit)
            )
            result = await session.execute(stmt)
            messages = result.scalars().all()
            message_ids = []
            for message in messages:
                if message.sender_id != user_id and user_id not in message.read_by_list:
                    message.read_by_list.append(user_id)
                    message_ids.append(message.id)

            # 既読にしたメッセージを返す
            for message in messages:
                yield ReadMessageResponse.model_validate(message) # type: ignore

            if message_ids:
                await Message.update_read_by_list(session, message_ids, user_id)


class CreateMessage:
    def __init__(self, session: AsyncSession) -> None:
        self.async_session = session
        self.mail_client = (
            None
            if settings.ENV == "local"
            else boto3.client("ses", region_name="ap-northeast-1")
        )
        self.push_client = (
            None
            if settings.ENV == "local"
            else boto3.client("sns", region_name="ap-northeast-1")
        )

    async def execute(
        self, user_id: int, chat_id: int, request: CreateMessageRequest
    ) -> CreateMessageResponse:
        async with self.async_session() as a_session:
            # Messageの関係者でない場合は403エラーを返却する
            if (
                not (
                    await a_session.execute(
                        select(Chat).where(
                            Chat.id == chat_id, Chat.created_by == user_id
                        )
                    )
                ).scalar()
                and not (
                    await a_session.execute(
                        select(ChatParticipants).where(
                            ChatParticipants.chat_id == chat_id,
                            ChatParticipants.user_id == user_id,
                        )
                    )
                ).scalar()
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail=["Forbidden"]
                )

            # Chatを取得
            chat = await Chat.read_by_id(a_session, chat_id)
            if not chat:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=["Chat not found."]
                )

        async with self.async_session.begin() as a_session:
            # Messageを作成
            message = await Message.create(
                a_session, chat_id=chat_id, sender_id=user_id, content=request.content
            )

            posted_user = await User.read_by_id(a_session, user_id)
            if not posted_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=["User not found."]
                )

            # Chat参加者に通知
            async for (
                participant
            ) in ChatParticipants.read_all_active_notification_users(
                a_session, chat_id
            ):
                user = participant.user
                if not user:
                    continue

                message_payload = f"{posted_user.username}: {request.content}"
                if user.notification_type == NotificationType.EMAIL:
                    # send email
                    body = {
                        "Text": {
                            "Data": message_payload,
                            "Charset": "UTF-8",
                        }
                    }
                    if self.mail_client:
                        response = self.mail_client.send_email(
                            Source="{} <{}>".format("SENDER", "from-address@test.com"),
                            Destination={
                                "ToAddresses": [user.email],
                            },
                            Message={
                                "Subject": {
                                    "Data": "[chat-service] posted message",
                                    "Charset": "UTF-8",
                                },
                                "Body": body,
                            },
                        )
                        logger.info(response)
                    else:
                        logger.info(body)
                elif user.notification_type == NotificationType.MOBILE_PUSH:
                    pass
                    # read_all_mobileを呼び出し、device_tokenがnullでなく、UNKNOWNでないユーザーに絞る
                    async for session in Session.read_all_mobile(a_session, [user.id]):
                        if (
                            session.user_id == user.id
                            and session.platform_type != PlatformType.UNKNOWN
                        ):
                            if session.platform_type == PlatformType.ANDROID:
                                message_body = {"GCM": json.dumps(message_payload)}
                            elif session.platform_type == PlatformType.IOS:
                                message_body = {
                                    "APNS": json.dumps(
                                        {"aps": {"alert": message_payload}}
                                    )
                                }

                            if self.push_client:
                                response = self.push_client.publish(
                                    TargetArn=session.device_token,  # device_tokenをTargetArnに設定
                                    MessageStructure="json",
                                    Message=json.dumps(message_body),
                                )
                                logger.info(response)
                            else:
                                logger.info(message_payload)

            return CreateMessageResponse.model_validate(message)


class DeleteMessage:
    def __init__(self, session: AsyncSession) -> None:
        self.async_session = session

    async def execute(self, user_id: int, message_id: int) -> None:
        async with self.async_session.begin() as session:
            message = await Message.read_by_id_and_user_id(session, message_id, user_id)
            if not message:
                return
            await Message.delete(session, message_id, user_id)
