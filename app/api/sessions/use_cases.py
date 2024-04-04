from fastapi import HTTPException, status

from app.db import AsyncSession
from app.models import Session, SessionSchema


class UpdateSession:
    def __init__(self, session: AsyncSession) -> None:
        self.async_session = session

    async def execute(
        self, user_id: int, refresh_token: str, device_token: str, platform_type: str
    ) -> SessionSchema:
        async with self.async_session.begin() as session:
            session_instance = await Session.read_by_user_id_and_refresh_token(
                session, user_id, refresh_token
            )
            if not session_instance:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

            await session_instance.update(
                session, device_token=device_token, platform_type=platform_type
            )
            await session.refresh(session_instance)
            return SessionSchema.model_validate(session_instance)


class DeleteSession:
    def __init__(self, session: AsyncSession) -> None:
        self.async_session = session

    async def execute(self, session_instance_id: int) -> None:
        async with self.async_session.begin() as session:
            session_instance = await Session.read_by_id(session, session_instance_id)
            if not session_instance:
                return
            await Session.delete(session, session_instance)
