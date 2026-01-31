"""Segment Pydantic models for API."""

from datetime import datetime
from typing import Optional
from app.models.base import APIModel

from app.db.models.segment import SegmentStatus


class SegmentBase(APIModel):
    """Base segment schema."""

    video_prompt: Optional[str] = None
    narration_text: Optional[str] = None
    end_frame_prompt: Optional[str] = None


class SegmentUpdate(APIModel):
    """Schema for updating a segment."""

    video_prompt: Optional[str] = None
    narration_text: Optional[str] = None
    end_frame_prompt: Optional[str] = None


class SegmentResponse(SegmentBase):
    """Schema for segment response."""

    id: str
    project_id: str
    index: int
    first_frame_url: Optional[str] = None
    last_frame_url: Optional[str] = None
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    video_duration_sec: Optional[float] = None
    status: SegmentStatus
    approved: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config(APIModel.Config):
        from_attributes = True
