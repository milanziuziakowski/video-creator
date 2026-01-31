"""FastAPI dependencies for route injection."""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.azure_auth import get_current_user_token, TokenPayload
from app.db.session import get_db_session
from app.db.models.user import User
from app.services.user_service import UserService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async for session in get_db_session():
        yield session


async def get_current_user(
    token: TokenPayload = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get or create user from Azure token.

    This automatically creates a user record on first login.
    """
    service = UserService(db)

    user = await service.get_or_create_user(
        entra_id=token.oid,
        email=token.email or token.preferred_username,
        name=token.name,
    )

    return user
