"""Auth token schemas."""

from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    typ: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str