from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.commons.types import ChatType, NotificationType, PlatformType


class TwoFaSchema(BaseModel):
    token: str
    code: str

    model_config = ConfigDict(from_attributes=True)


class AccessTokenSchema(BaseModel):
    user_id: int
    access_token: str

    model_config = ConfigDict(from_attributes=True)


class RefreshTokenSchema(BaseModel):
    refresh_token: str

    model_config = ConfigDict(from_attributes=True)


class UserSchema(BaseModel):
    id: int | None = Field(None, description="The unique identifier for the user.")
    created_at: datetime | None = Field(
        None, description="The time when the user was created."
    )
    updated_at: datetime | None = Field(
        None, description="The time when the user was last updated."
    )
    is_name_visible: bool = Field(
        True, description="Flag to indicate if the user's name is visible."
    )
    username: str | None = Field(
        None, max_length=32, description="The user's username."
    )
    email: str = Field(..., max_length=255, description="The user's email address.")
    first_name: str | None = Field(
        None, max_length=30, description="The user's first name."
    )
    last_name: str | None = Field(
        None, max_length=30, description="The user's last name."
    )
    notification_type: str = Field(
        "DISABLED", description="The type of notification settings for the user."
    )
    new_email: str | None = Field(
        None,
        max_length=255,
        description="The user's new email address if they have requested to change it.",
    )

    model_config = ConfigDict(from_attributes=True)

    @field_validator("notification_type", mode="before")
    def convert_notification_type(cls, v):
        if isinstance(v, int):
            return NotificationType(v).name.lower()
        return v


class MaskedUserSchema(BaseModel):
    id: int | None = Field(None, description="The unique identifier for the user.")
    created_at: datetime | None = Field(
        None, description="The time when the user was created."
    )
    updated_at: datetime | None = Field(
        None, description="The time when the user was last updated."
    )
    first_name: str | None = Field(
        None, max_length=30, description="The user's first name."
    )
    last_name: str | None = Field(
        None, max_length=30, description="The user's last name."
    )
    username: str | None = Field(
        None, max_length=32, description="The user's username."
    )
    is_name_visible: bool = Field(
        True, description="Flag to indicate if the user's name is visible."
    )

    model_config = ConfigDict(from_attributes=True)


class SessionSchema(BaseModel):
    id: int = Field(..., description="The unique identifier for the session.")
    created_at: datetime | None = Field(
        None, description="The time when the session was created."
    )
    updated_at: datetime | None = Field(
        None, description="The time when the session was last updated."
    )
    user_id: int = Field(
        ..., description="The ID of the user associated with this session."
    )
    device_token: str | None = Field(None, description="The device token.")
    platform_type: str | None = Field("IOS", description="The type of platform.")
    refresh_token: str = Field(..., description="The refresh token.")
    refresh_token_expired_at: datetime = Field(
        ...,
        description="The time when the refresh token expires. Valid for 90 days from issuance by default.",
    )

    model_config = ConfigDict(from_attributes=True)

    @field_validator("platform_type", mode="before")
    def convert_platform_type(cls, v):
        if isinstance(v, int):
            return PlatformType(v).name.lower()
        return v


class ChatSchema(BaseModel):
    id: int | None = Field(None, description="The unique identifier for the chat.")
    created_at: datetime | None = Field(
        None, description="The time when the chat was created."
    )
    updated_at: datetime | None = Field(
        None, description="The time when the chat was last updated."
    )
    chat_type: str | None = Field("DIRECT", description="The type of chat.")
    name: str = Field(..., max_length=255, description="The name of the chat.")

    model_config = ConfigDict(from_attributes=True)

    @field_validator("chat_type", mode="before")
    def convert_chat_type(cls, v):
        if isinstance(v, int):
            return ChatType(v).name.lower()
        return v


class MessageSchema(BaseModel):
    id: int = Field(None, description="The unique identifier for the message.")
    sender_id: int = Field(None, description="The unique identifier for the sender.")
    content: str = Field(
        ..., max_length=1024, description="The content of the message."
    )
    created_at: datetime | str = Field(
        None, description="The time when the message was created."
    )
    read_by_list: list[int] = Field(
        [], description="List of user IDs who have read the message."
    )

    model_config = ConfigDict(from_attributes=True)
