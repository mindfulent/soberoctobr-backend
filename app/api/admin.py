"""Admin API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List
from app.core.database import get_db
from app.core.security import get_current_admin_user
from app.models.user import User
from app.models.habit import Habit
from app.models.challenge import Challenge
from app.models.daily_entry import DailyEntry
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
    habits_created: int = Field(..., serialization_alias="habitsCreated")
    habits_completed: int = Field(..., serialization_alias="habitsCompleted")


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
    total_habits = db.query(func.count(Habit.id)).filter(Habit.is_active == True).scalar()

    # Build user info with habit statistics
    user_stats = []
    for user in users:
        # Count habits created by this user (active habits only)
        habits_created = (
            db.query(func.count(Habit.id))
            .join(Challenge, Habit.challenge_id == Challenge.id)
            .filter(Challenge.user_id == user.id)
            .filter(Habit.is_active == True)
            .scalar()
        ) or 0

        # Count completed daily entries for this user's habits
        # For binary habits: completed=True
        # For counted habits: count > 0
        habits_completed = (
            db.query(func.count(DailyEntry.id))
            .join(Habit, DailyEntry.habit_id == Habit.id)
            .join(Challenge, Habit.challenge_id == Challenge.id)
            .filter(Challenge.user_id == user.id)
            .filter(
                or_(
                    DailyEntry.completed == True,
                    DailyEntry.count > 0
                )
            )
            .scalar()
        ) or 0

        user_stats.append(AdminUserInfo(
            id=user.id,
            name=user.name,
            email=user.email,
            picture=user.picture,
            created_at=user.created_at,
            habits_created=habits_created,
            habits_completed=habits_completed
        ))

    return AdminStatsResponse(
        total_users=len(users),
        total_habits=total_habits or 0,
        users=user_stats
    )
