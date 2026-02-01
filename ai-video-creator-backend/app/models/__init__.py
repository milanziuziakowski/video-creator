"""Pydantic models package for API schemas."""

from app.models.generation import (
    CameraCommand,
    FL2VGenerateRequest,
    FL2VGenerateResponse,
    FL2VResolution,
    GeneratePlanRequest,
    GenerateSegmentRequest,
    GenerationStatus,
    GenerationStatusResponse,
    VideoPlanResponse,
    VideoPlanSegment,
)
from app.models.project import (
    ProjectBase,
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
    SegmentSummary,
)
from app.models.segment import (
    SegmentBase,
    SegmentResponse,
    SegmentUpdate,
)
from app.models.user import UserResponse
from app.models.voice import (
    AssignVoiceRequest,
    VoiceBase,
    VoiceCreate,
    VoiceListResponse,
    VoiceResponse,
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
