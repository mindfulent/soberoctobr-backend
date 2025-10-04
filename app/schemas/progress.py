"""Progress statistics Pydantic schemas."""

from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from pydantic.alias_generators import to_camel


class DayProgress(BaseModel):
    """Progress for a single day."""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )

    date: datetime
    completed_count: int
    total_count: int
    is_perfect: bool
    completion_percentage: int


class HabitProgress(BaseModel):
    """Progress for a single habit."""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )

    habit_id: str
    habit_name: str
    icon: Optional[str] = None
    completed_count: int
    total_days: int
    completion_percentage: int


class ChallengeProgressResponse(BaseModel):
    """Schema for challenge progress statistics."""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )

    challenge_id: str
    start_date: datetime
    end_date: datetime
    current_day: int
    total_days: int
    days_elapsed: int

    # Overall statistics
    total_habits_completed: int
    total_possible_habits: int
    overall_completion_percentage: int

    # Streak information
    current_streak: int
    longest_streak: int

    # Last 7 days
    last_7_days: List[DayProgress]

    # Per-habit breakdown
    habit_progress: List[HabitProgress]

