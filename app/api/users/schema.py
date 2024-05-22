from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


class ReadUserResponse(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    is_name_visible: bool
    username: str | None
    first_name: str | None
    last_name: str | None
    email: str
    new_email: str | None
    notification_type: str


class UpdateUserRequest(BaseModel):
    is_name_visible: bool
    username: str | None = Field(..., min_length=8, max_length=32)
    first_name: str | None = Field(..., max_length=30)
    last_name: str | None = Field(..., max_length=30)
    new_email: EmailStr | None
    notification_type: Literal["disabled", "mobile_push", "email"]

    @field_validator("first_name", mode="before")
    def check_first_name(cls, v):
        if v == "ANONYMOUS":
            raise ValueError("First name cannot be 'ANONYMOUS'")
        return v

    @field_validator("last_name", mode="before")
    def check_last_name(cls, v):
        if v == "ANONYMOUS":
            raise ValueError("Last name cannot be 'ANONYMOUS'")
        return v


class PartialUpdateUserRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)
