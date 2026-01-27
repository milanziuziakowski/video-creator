"""Video plan and project state models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .segment import SegmentStatus


class VideoPlan(BaseModel):
    """Complete plan for video generation with segments."""
    
    project_id: str = Field(..., description="Unique project identifier")
    target_duration_sec: int = Field(..., description="Target video duration (≤60)")
    segment_len_sec: int = Field(..., description="Segment length (6 or 10)")
    segment_count: int = Field(..., description="Number of segments")
    voice_id: Optional[str] = Field(None, description="MiniMax cloned voice ID")
    
    # Segments list
    segments: list[SegmentStatus] = Field(default_factory=list, description="Array of segment states")
    
    # Final artifacts
    assembled_video_url: Optional[str] = Field(None, description="URL to concatenated video before audio mux")
    assembled_audio_url: Optional[str] = Field(None, description="URL to concatenated audio")
    final_video_url: Optional[str] = Field(None, description="URL to final muxed video")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "proj_12345",
                "target_duration_sec": 60,
                "segment_len_sec": 6,
                "segment_count": 10,
                "voice_id": "voice_xyz",
                "segments": [
                    {
                        "segment_index": 0,
                        "prompt": "A beautiful sunset...",
                        "narration_text": "Once upon a time...",
                        "approved": True,
                    }
                ],
                "final_video_url": None,
            }
        }


class ProjectMetadata(BaseModel):
    """Project metadata for storage and tracking."""
    
    project_id: str
    user_id: str
    story_prompt: str
    start_frame_image_url: str
    voice_sample_audio_url: str
    
    # Configuration
    target_duration_sec: int
    segment_len_sec: int
    
    # State
    status: str = Field("planning", description="planning, in_progress, completed, failed")
    video_plan: Optional[VideoPlan] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
