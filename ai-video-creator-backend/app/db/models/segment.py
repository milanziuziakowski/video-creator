"""Segment database model."""

import uuid
from enum import Enum
from sqlalchemy import Column, String, Integer, Boolean, Enum as SQLEnum, ForeignKey, Text, Float
from sqlalchemy.orm import relationship, synonym

from app.db.base import Base, TimestampMixin


class SegmentStatus(str, Enum):
    """Segment workflow status."""

    PENDING = "pending"
    PROMPT_READY = "prompt_ready"
    APPROVED = "approved"
    GENERATING = "generating"
    GENERATED = "generated"
    SEGMENT_APPROVED = "segment_approved"
    FAILED = "failed"


class Segment(Base, TimestampMixin):
    """Segment database model."""

    __tablename__ = "segments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)

    index = Column(Integer, nullable=False)
    video_prompt = Column(Text)
    narration_text = Column(Text)
    end_frame_prompt = Column(Text)

    first_frame_url = Column(String(1024))
    last_frame_url = Column(String(1024))
    video_url = Column(String(1024))
    audio_url = Column(String(1024))

    video_duration_sec = Column(Float)
    duration_sec = synonym("video_duration_sec")

    # Task IDs for tracking generation
    video_task_id = Column(String(255))
    audio_task_id = Column(String(255))

    status = Column(SQLEnum(SegmentStatus), default=SegmentStatus.PENDING)
    approved = Column(Boolean, default=False)

    # Relationships
    project = relationship("Project", back_populates="segments")

    def __repr__(self) -> str:
        return f"<Segment {self.project_id}:{self.index}>"
