"""Admin API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.core.database import get_db
from app.core.security import get_current_admin_user
from app.models.user import User
from app.models.habit import Habit
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

router = APIRouter()


class AdminUserInfo(BaseModel):
    """Admin view of user information."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    name: str
    email: str
    picture: str | None
    created_at: datetime = Field(..., serialization_alias="createdAt")


class AdminStatsResponse(BaseModel):
    """Admin statistics response."""
    model_config = ConfigDict(populate_by_name=True)

    total_users: int = Field(..., serialization_alias="totalUsers")
    total_habits: int = Field(..., serialization_alias="totalHabits")
    users: List[AdminUserInfo]


@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """
    Get admin statistics including all users and habit count.

    Requires admin authentication.
    """
    # Get all users ordered by creation date (newest first)
    users = db.query(User).order_by(User.created_at.desc()).all()

    # Get total habit count across all users
    total_habits = db.query(func.count(Habit.id)).scalar()

    return AdminStatsResponse(
        total_users=len(users),
        total_habits=total_habits or 0,
        users=[AdminUserInfo.model_validate(user) for user in users]
    )
