"""User service for user management."""

import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.user import User
from app.auth.jwt_auth import get_password_hash, verify_password


class UserService:
    """Service for user management operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User if found, None otherwise
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username.

        Args:
            username: Username

        Returns:
            User if found, None otherwise
        """
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email.

        Args:
            email: User email

        Returns:
            User if found, None otherwise
        """
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        name: Optional[str] = None,
    ) -> User:
        """Create a new user.

        Args:
            username: Unique username
            email: User email
            password: Plain text password (will be hashed)
            name: User display name

        Returns:
            Created user
        """
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            name=name or username,
            is_active=True,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def authenticate_user(
        self,
        username: str,
        password: str,
    ) -> Optional[User]:
        """Authenticate user with username and password.

        Args:
            username: Username
            password: Plain text password

        Returns:
            User if authentication successful, None otherwise
        """
        user = await self.get_by_username(username)
        
        if user is None:
            return None
            
        if not verify_password(password, user.hashed_password):
            return None
            
        if not user.is_active:
            return None
            
        return user
