from app.db import AsyncSession
from app.models import Message

from .schema import CreateMessageRequest, CreateMessageResponse


class CreateMessage:
    def __init__(self, session: AsyncSession) -> None:
        self.async_session = session

    async def execute(
        self,
        user_id: int,
        chat_id: int,
        current_participants: list[int],
        request: CreateMessageRequest,
    ) -> CreateMessageResponse:
        async with self.async_session.begin() as session:
            # Messageを作成
            message = await Message.create(
                session,
                chat_id=chat_id,
                sender_id=user_id,
                content=request.content,
                read_by_list=current_participants,
            )
            return CreateMessageResponse.model_validate(message)
