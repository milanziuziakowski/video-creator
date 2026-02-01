"""Pydantic models for Voice API."""

from datetime import datetime

from app.models.base import APIModel


class VoiceBase(APIModel):
    """Base voice schema."""

    name: str
    description: str | None = None


class VoiceCreate(VoiceBase):
    """Schema for creating a new voice."""

    voice_id: str  # MiniMax voice ID


class VoiceResponse(VoiceBase):
    """Schema for voice response."""

    id: str
    voice_id: str
    created_at: datetime
    updated_at: datetime


class VoiceListResponse(APIModel):
    """Schema for list of voices."""

    voices: list[VoiceResponse]
    total: int


class AssignVoiceRequest(APIModel):
    """Schema for assigning an existing voice to a project."""

    project_id: str
    voice_id: str  # MiniMax voice ID
