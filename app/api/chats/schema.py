from pydantic import BaseModel, conint

from app.models import ChatSchema, MaskedUserSchema


class ReadAllChatRequest(BaseModel):
    offset: int = conint(ge=0, le=50)
    limit: int = conint(ge=0, le=10)
    desc: bool


class ReadChatResponse(ChatSchema):
    pass


class ReadAllChatResponse(BaseModel):
    chats: list[ReadChatResponse]


class ReadChatParticipantResponse(MaskedUserSchema):
    pass


class ReadAllChatParticipantResponse(BaseModel):
    participants: list[ReadChatParticipantResponse]


class CreateChatRequest(BaseModel):
    name: str
    participant_names: list[str]


class CreateChatResponse(ChatSchema):
    pass
