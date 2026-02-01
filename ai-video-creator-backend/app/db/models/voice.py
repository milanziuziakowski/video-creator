"""Voice database model for storing cloned voices."""

import uuid
from sqlalchemy import Column, String, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class Voice(Base, TimestampMixin):
    """Voice database model for storing cloned voices that can be reused."""

    __tablename__ = "voices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    # MiniMax voice ID (the actual ID used for TTS)
    voice_id = Column(String(255), nullable=False, unique=True)
    
    # User-friendly name for the voice
    name = Column(String(255), nullable=False)
    
    # Optional description
    description = Column(Text)

    # Relationships
    user = relationship("User", back_populates="voices")

    def __repr__(self) -> str:
        return f"<Voice {self.name} ({self.voice_id})>"
