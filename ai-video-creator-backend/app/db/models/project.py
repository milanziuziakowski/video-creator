"""Project database model."""

import uuid
from enum import Enum
from sqlalchemy import Column, String, Integer, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class ProjectStatus(str, Enum):
    """Project workflow status."""

    DRAFT = "draft"
    PLANNED = "planned"
    CREATED = "created"
    MEDIA_UPLOADED = "media_uploaded"
    VOICE_CLONING = "voice_cloning"
    PLAN_GENERATING = "plan_generating"
    PLAN_READY = "plan_ready"
    GENERATING = "generating"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"


class Project(Base, TimestampMixin):
    """Project database model."""

    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    story_prompt = Column(Text)

    target_duration_sec = Column(Integer, default=60)
    segment_len_sec = Column(Integer, default=6)
    segment_count = Column(Integer, default=0)

    voice_id = Column(String(255))
    first_frame_url = Column(String(1024))
    audio_sample_url = Column(String(1024))
    final_video_url = Column(String(1024))

    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.CREATED)

    # Relationships
    user = relationship("User", back_populates="projects")
    segments = relationship(
        "Segment", back_populates="project", cascade="all, delete-orphan", order_by="Segment.index"
    )

    def __repr__(self) -> str:
        return f"<Project {self.name}>"
