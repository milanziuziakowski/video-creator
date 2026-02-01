"""User database model."""

from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """User database model."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    name = Column(String(255))
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    voices = relationship("Voice", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User {self.username}>"
