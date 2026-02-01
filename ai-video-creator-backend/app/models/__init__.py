"""Pydantic models package for API schemas."""

from app.models.user import UserResponse
from app.models.project import (
    ProjectBase,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    SegmentSummary,
)
from app.models.segment import (
    SegmentBase,
    SegmentUpdate,
    SegmentResponse,
)
from app.models.generation import (
    GenerationStatus,
    VideoPlanSegment,
    VideoPlanResponse,
    GeneratePlanRequest,
    GenerateSegmentRequest,
    GenerationStatusResponse,
    FL2VResolution,
    CameraCommand,
    FL2VGenerateRequest,
    FL2VGenerateResponse,
)
from app.models.voice import (
    VoiceBase,
    VoiceCreate,
    VoiceResponse,
    VoiceListResponse,
    AssignVoiceRequest,
)

__all__ = [
    "UserResponse",
    "ProjectBase",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectListResponse",
    "SegmentSummary",
    "SegmentBase",
    "SegmentUpdate",
    "SegmentResponse",
    "GenerationStatus",
    "VideoPlanSegment",
    "VideoPlanResponse",
    "GeneratePlanRequest",
    "GenerateSegmentRequest",
    "GenerationStatusResponse",
    "FL2VResolution",
    "CameraCommand",
    "FL2VGenerateRequest",
    "FL2VGenerateResponse",
    "VoiceBase",
    "VoiceCreate",
    "VoiceResponse",
    "VoiceListResponse",
    "AssignVoiceRequest",
]
