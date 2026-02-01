"""Generation-related Pydantic models."""

from enum import Enum

from pydantic import Field

from app.models.base import APIModel


class GenerationStatus(str, Enum):
    """Status of a generation task."""

    SUBMITTED = "submitted"
    PROCESSING = "processing"
    SUCCESS = "Success"
    FAIL = "Fail"


class VideoPlanSegment(APIModel):
    """Single segment in a video plan."""

    segment_index: int
    video_prompt: str
    narration_text: str
    end_frame_prompt: str


class VideoPlanResponse(APIModel):
    """Response from AI video plan generation."""

    title: str
    segments: list[VideoPlanSegment]
    continuity_notes: str


class GeneratePlanRequest(APIModel):
    """Request to generate AI video plan."""

    project_id: str
    story_prompt: str


class GenerateSegmentRequest(APIModel):
    """Request to generate a single segment."""

    segment_id: str


class GenerationStatusResponse(APIModel):
    """Response for generation status polling."""

    task_id: str
    status: GenerationStatus
    file_id: str | None = None
    download_url: str | None = None
    error: str | None = None
    progress: int | None = None  # 0-100


class FL2VResolution(str, Enum):
    """Supported resolutions for First & Last Frame video generation."""

    RES_768P = "768P"
    RES_1080P = "1080P"
    # Note: 512P is NOT supported for FL2V


class CameraCommand(str, Enum):
    """Camera movement commands for MiniMax video generation prompts."""

    TRUCK_LEFT = "[Truck left]"
    TRUCK_RIGHT = "[Truck right]"
    PAN_LEFT = "[Pan left]"
    PAN_RIGHT = "[Pan right]"
    PUSH_IN = "[Push in]"
    PULL_OUT = "[Pull out]"
    PEDESTAL_UP = "[Pedestal up]"
    PEDESTAL_DOWN = "[Pedestal down]"
    TILT_UP = "[Tilt up]"
    TILT_DOWN = "[Tilt down]"
    ZOOM_IN = "[Zoom in]"
    ZOOM_OUT = "[Zoom out]"
    SHAKE = "[Shake]"
    TRACKING_SHOT = "[Tracking shot]"
    STATIC_SHOT = "[Static shot]"


class FL2VGenerateRequest(APIModel):
    """Request to generate First & Last Frame video (FL2V).

    Uses MiniMax Hailuo API endpoint: POST /v1/video_generation

    Image Requirements:
        - Formats: JPG, JPEG, PNG, WebP
        - Size: < 20MB each
        - Dimensions: Short side > 300px, Aspect ratio 2:5 to 5:2
    """

    segment_id: str
    prompt: str = Field(
        default="",
        max_length=2000,
        description="Video description. Can include camera commands like [Zoom in], [Pan left]",
    )
    first_frame_image: str | None = Field(
        default=None,
        description="URL or base64 data URL (data:image/jpeg;base64,...) of first frame",
    )
    last_frame_image: str = Field(..., description="Required. URL or base64 data URL of last frame")
    duration: int = Field(default=6, ge=6, le=10, description="Video duration in seconds (6 or 10)")
    resolution: FL2VResolution = Field(
        default=FL2VResolution.RES_768P,
        description="Video resolution (768P or 1080P - 512P not supported for FL2V)",
    )
    prompt_optimizer: bool = Field(
        default=True, description="Auto-optimize prompt. Set False for precise control"
    )
    camera_commands: list[CameraCommand] | None = Field(
        default=None,
        max_length=3,
        description="Camera commands to append to prompt (max 3 simultaneous)",
    )

    def get_prompt_with_commands(self) -> str:
        """Get prompt with camera commands appended."""
        if not self.camera_commands:
            return self.prompt
        commands = ",".join([cmd.value.strip("[]") for cmd in self.camera_commands])
        return f"{self.prompt} [{commands}]"


class FL2VGenerateResponse(APIModel):
    """Response from FL2V video generation task creation."""

    task_id: str
    segment_id: str
    status: str = "submitted"
    model: str = "MiniMax-Hailuo-02"
