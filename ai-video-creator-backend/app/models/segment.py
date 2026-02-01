"""Segment Pydantic models for API."""

from datetime import datetime

from app.db.models.segment import SegmentStatus
from app.models.base import APIModel


class SegmentBase(APIModel):
    """Base segment schema."""

    video_prompt: str | None = None
    narration_text: str | None = None
    end_frame_prompt: str | None = None


class SegmentUpdate(APIModel):
    """Schema for updating a segment."""

    video_prompt: str | None = None
    narration_text: str | None = None
    end_frame_prompt: str | None = None


class SegmentResponse(SegmentBase):
    """Schema for segment response."""

    id: str
    project_id: str
    index: int
    first_frame_url: str | None = None
    last_frame_url: str | None = None
    video_url: str | None = None
    audio_url: str | None = None
    video_duration_sec: float | None = None
    status: SegmentStatus
    approved: bool
    created_at: datetime
    updated_at: datetime | None = None

    class Config(APIModel.Config):
        from_attributes = True
