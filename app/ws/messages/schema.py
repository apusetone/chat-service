from pydantic import BaseModel, Field, validator
from datetime import datetime
from app.models import MessageSchema


class CreateMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=1024)


class CreateMessageResponse(MessageSchema):
    @validator("created_at", pre=True, always=True)
    def convert_created_at(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v
