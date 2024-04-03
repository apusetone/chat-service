from pydantic import BaseModel, EmailStr, Field

from app.commons.types import TokenType


class LoginRequest(BaseModel):
    email: EmailStr


class LoginResponse(BaseModel):
    token: str


class TwoFaRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)
    token: str = Field(..., min_length=32, max_length=32)


class TwoFaResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: TokenType
    id: int


class RefreshResponse(BaseModel):
    access_token: str
    token_type: TokenType
    id: int


class LogoutRequest(BaseModel):
    refresh_token: str
