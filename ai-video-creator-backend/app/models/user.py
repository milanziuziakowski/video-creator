"""User Pydantic models for API."""

from datetime import datetime
from app.models.base import APIModel


class UserResponse(APIModel):
    """Schema for user response."""

    id: str
    email: str
    name: str | None = None
    created_at: datetime

    class Config(APIModel.Config):
        from_attributes = True
