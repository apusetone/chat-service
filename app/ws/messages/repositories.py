import json
from typing import AsyncIterator

import boto3
from boto3.session import Session as AwsSession
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.commons.logging import logger
from app.commons.types import NotificationType, PlatformType
from app.models import Chat, ChatParticipants, Session, User
from app.settings import settings


class ChatRepository:
    def __init__(self, session: AsyncSession):
        self.async_session = session

    async def verify_chat_participant(
        self, chat_id: int, user_id: int
    ) -> tuple[Chat | None, bool]:
        async with self.async_session() as session:
            chat = await session.execute(select(Chat).where(Chat.id == chat_id))
            chat = chat.scalars().first()
            participant = await session.execute(
                select(ChatParticipants).where(
                    ChatParticipants.chat_id == chat_id,
                    ChatParticipants.user_id == user_id,
                )
            )
            participant = participant.scalars().first()

            result = chat or participant
            if not result:
                return (None, False)

            return (chat, result)


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.async_session = session

    async def get_user(self, user_id: int) -> User | None:
        async with self.async_session() as session:
            return await User.read_by_id(session, user_id)


class ChatParticipantsRepository:
    def __init__(self, session: AsyncSession):
        self.async_session = session

    async def get_all(self, chat_id: int) -> AsyncIterator[ChatParticipants]:
        async with self.async_session() as session:
            async for (
                participant
            ) in ChatParticipants.read_all_active_notification_users(session, chat_id):
                yield participant


class SessionRepository:
    def __init__(self, session: AsyncSession):
        self.async_session = session

    async def get_all(self, user_ids: list[int]) -> AsyncIterator[Session]:
        async with self.async_session() as a_session:
            async for session in Session.read_all_mobile(a_session, user_ids):
                yield session


class AwsClientRepository:
    def __init__(self):
        pass

    def get_ses_sns_client(self) -> tuple[AwsSession | None, AwsSession | None]:
        return (
            (
                None
                if settings.ENV == "local"
                else boto3.client("ses", region_name="ap-northeast-1")
            ),
            (
                None
                if settings.ENV == "local"
                else boto3.client("sns", region_name="ap-northeast-1")
            ),
        )


class NotificationRepository:
    def __init__(self):
        self.filter_by_user_id = lambda data, user_id: [
            entry for entry in data if entry.get("user_id") == user_id
        ]

    def send_notifications(
        self,
        posted_user: User,
        content: str,
        chat_participants: list[ChatParticipants],
        mail_client: AwsSession | None,
        push_client: AwsSession | None,
        sessions: list[dict[str, int | Session]],
    ) -> None:
        # Chat参加者に通知
        for participant in chat_participants:
            user = participant.user
            message_payload = f"{posted_user.username}: {content}"
            if user.notification_type == NotificationType.EMAIL:
                # send email
                body = {
                    "Text": {
                        "Data": message_payload,
                        "Charset": "UTF-8",
                    }
                }
                if mail_client:
                    response = mail_client.send_email(
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
                filtered_sessions = self.filter_by_user_id(sessions, user.id)
                for session in filtered_sessions:
                    if (
                        session.user_id == user.id
                        and session.platform_type != PlatformType.UNKNOWN
                    ):
                        if session.platform_type == PlatformType.ANDROID:
                            message_body = {"GCM": json.dumps(message_payload)}
                        elif session.platform_type == PlatformType.IOS:
                            message_body = {
                                "APNS": json.dumps({"aps": {"alert": message_payload}})
                            }

                        if push_client:
                            response = push_client.publish(
                                TargetArn=session.device_token,  # device_tokenをTargetArnに設定
                                MessageStructure="json",
                                Message=json.dumps(message_body),
                            )
                            logger.info(response)
                        else:
                            logger.info(message_payload)
