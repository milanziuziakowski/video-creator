"""Project Pydantic models for API."""

from datetime import datetime

from pydantic import Field

from app.db.models.project import ProjectStatus
from app.models.base import APIModel


class ProjectBase(APIModel):
    """Base project schema."""

    name: str = Field(..., min_length=1, max_length=255)
    story_prompt: str | None = None
    target_duration_sec: int = Field(60, ge=6, le=60)
    segment_len_sec: int = Field(6, ge=6, le=10, alias="segmentDurationSec")


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""

    pass


class ProjectUpdate(APIModel):
    """Schema for updating a project."""

    name: str | None = Field(None, min_length=1, max_length=255)
    story_prompt: str | None = None
    target_duration_sec: int | None = Field(None, ge=6, le=60)
    segment_len_sec: int | None = Field(None, ge=6, le=10, alias="segmentDurationSec")


class SegmentSummary(APIModel):
    """Brief segment info for project listing."""

    id: str
    index: int
    status: str
    approved: bool

    class Config(APIModel.Config):
        from_attributes = True


class ProjectResponse(ProjectBase):
    """Schema for project response."""

    id: str
    user_id: str = Field(alias="userId")
    segment_count: int = Field(alias="segmentCount")
    voice_id: str | None = Field(None, alias="voiceId")
    first_frame_url: str | None = Field(None, alias="firstFrameUrl")
    audio_sample_url: str | None = Field(None, alias="audioSampleUrl")
    final_video_url: str | None = Field(None, alias="finalVideoUrl")
    status: ProjectStatus
    segments: list[SegmentSummary] = []
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt")

    class Config(APIModel.Config):
        from_attributes = True
        populate_by_name = True


class ProjectListResponse(APIModel):
    """Schema for project list response."""

    projects: list[ProjectResponse]
    total: int
