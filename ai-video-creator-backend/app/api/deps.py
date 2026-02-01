"""FastAPI dependencies for route injection."""

from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_auth import TokenData, get_current_user_token
from app.db.models.user import User
from app.db.session import get_db_session
from app.services.user_service import UserService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async for session in get_db_session():
        yield session


async def get_current_user(
    token: TokenData = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current user from JWT token.

    This validates the token and retrieves the user from the database.
    """
    service = UserService(db)

    user = await service.get_by_username(token.username)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    return user
