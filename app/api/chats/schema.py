from pydantic import BaseModel, Field, conint, constr, field_validator

from app.models import ChatSchema, MaskedUserSchema


class ReadAllChatRequest(BaseModel):
    offset: conint(ge=0, le=50)  # type: ignore
    limit: conint(ge=0, le=10)  # type: ignore
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
    name: constr(min_length=1, max_length=50) = Field(...)  # type: ignore
    participant_names: list[constr(min_length=1, max_length=20)] = Field(...)  # type: ignore

    @field_validator("participant_names", mode="before")
    def check_participant_names(cls, v):
        # TODO: set upper limit
        if not len(v):
            raise ValueError("Participant names list cannot be empty")
        return v


class CreateChatResponse(ChatSchema):
    pass
