from typing import Literal

from pydantic import BaseModel, Field


class SessionRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1, max_length=32)
    device_token: str = Field(..., min_length=1, max_length=32)
    platform_type: Literal["unknown", "ios", "android"]
