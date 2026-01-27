"""Data models for video segment."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SegmentStatus(BaseModel):
    """Status and metadata for a single video segment."""
    
    segment_index: int = Field(..., description="0-indexed segment number")
    prompt: str = Field(..., description="Video generation prompt")
    narration_text: str = Field(..., description="Text for audio narration")
    
    # Frame references
    first_frame_image_url: Optional[str] = Field(None, description="Local path to first frame image")
    last_frame_image_url: Optional[str] = Field(None, description="Local path to last frame image")
    
    # Generated artifacts
    video_task_id: Optional[str] = Field(None, description="FL2V task ID for video generation")
    segment_video_url: Optional[str] = Field(None, description="Local path to generated segment video")
    segment_audio_url: Optional[str] = Field(None, description="Local path to generated segment audio")
    
    # Status tracking
    approved: bool = Field(False, description="Whether segment is approved by user")
    approval_timestamp: Optional[datetime] = Field(None, description="When segment was approved")
    
    # Generation metadata
    video_duration_sec: Optional[float] = Field(None, description="Actual duration of generated video")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "segment_index": 0,
                "prompt": "A beautiful sunset over mountains...",
                "narration_text": "Narrator: Once upon a time...",
                "first_frame_image_url": "storage/projects/project_1/segment_0_first_frame.jpg",
                "last_frame_image_url": "storage/projects/project_1/segment_0_last_frame.jpg",
                "video_task_id": "task_abc123",
                "segment_video_url": "storage/projects/project_1/segment_0_video.mp4",
                "segment_audio_url": "storage/projects/project_1/segment_0_audio.mp3",
                "approved": True,
            }
        }
