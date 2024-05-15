from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models import MessageSchema


class CreateMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=1024)


class CreateMessageResponse(MessageSchema):
    @field_validator("created_at", mode="before")
    def convert_created_at(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v
