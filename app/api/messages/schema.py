from pydantic import BaseModel, Field, conint

from app.models import MessageSchema


class ReadAllMessageRequest(BaseModel):
    offset: int = conint(ge=0, le=50)
    limit: int = conint(ge=0, le=10)


class ReadMessageResponse(MessageSchema):
    pass


class ReadAllMessageResponse(BaseModel):
    messages: list[ReadMessageResponse]


class CreateMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=1024)


class CreateMessageResponse(MessageSchema):
    pass
