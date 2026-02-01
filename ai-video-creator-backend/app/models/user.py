"""User Pydantic models for API."""

from datetime import datetime

from pydantic import EmailStr, Field

from app.models.base import APIModel


class UserCreate(APIModel):
    """Schema for user registration."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str | None = None


class UserLogin(APIModel):
    """Schema for user login (used with OAuth2PasswordRequestForm)."""

    username: str
    password: str


class UserResponse(APIModel):
    """Schema for user response."""

    id: str
    username: str
    email: str
    name: str | None = None
    is_active: bool = True
    created_at: datetime

    class Config(APIModel.Config):
        from_attributes = True


class Token(APIModel):
    """Schema for token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(APIModel):
    """Schema for token data."""

    username: str | None = None
    user_id: str | None = None
