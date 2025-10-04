"""User management API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's profile.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        UserResponse: User profile information
    """
    return current_user


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile.

    Args:
        name: New name for the user
        current_user: Current authenticated user
        db: Database session

    Returns:
        UserResponse: Updated user profile
    """
    current_user.name = name
    db.commit()
    db.refresh(current_user)
    return current_user
