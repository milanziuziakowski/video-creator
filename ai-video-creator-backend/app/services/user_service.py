"""User service for user management."""

import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.user import User


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

    async def get_by_entra_id(self, entra_id: str) -> Optional[User]:
        """Get user by Azure Entra ID.

        Args:
            entra_id: Azure Entra object ID

        Returns:
            User if found, None otherwise
        """
        result = await self.db.execute(select(User).where(User.entra_id == entra_id))
        return result.scalar_one_or_none()

    async def create_user(
        self,
        entra_id: str,
        email: str,
        name: Optional[str] = None,
    ) -> User:
        """Create a new user.

        Args:
            entra_id: Azure Entra object ID
            email: User email
            name: User display name

        Returns:
            Created user
        """
        user = User(
            id=str(uuid.uuid4()),
            entra_id=entra_id,
            email=email,
            name=name,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def get_or_create_user(
        self,
        entra_id: str,
        email: Optional[str],
        name: Optional[str] = None,
    ) -> User:
        """Get existing user or create new one.

        Args:
            entra_id: Azure Entra object ID
            email: User email
            name: User display name

        Returns:
            User (existing or newly created)
        """
        user = await self.get_by_entra_id(entra_id)

        if user is None:
            user = await self.create_user(
                entra_id=entra_id,
                email=email or f"{entra_id}@unknown.local",
                name=name,
            )

        # Update user info if changed
        if user.email != email and email:
            user.email = email
        if user.name != name and name:
            user.name = name

        return user
