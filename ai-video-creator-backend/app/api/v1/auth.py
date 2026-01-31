"""Auth API endpoints."""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.db.models.user import User
from app.models.user import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get current authenticated user info."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        created_at=current_user.created_at,
    )
