"""Admin API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.core.database import get_db
from app.core.security import get_current_admin_user
from app.models.user import User
from app.models.habit import Habit
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class AdminUserInfo(BaseModel):
    """Admin view of user information."""
    id: str
    name: str
    email: str
    picture: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class AdminStatsResponse(BaseModel):
    """Admin statistics response."""
    total_users: int
    total_habits: int
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
