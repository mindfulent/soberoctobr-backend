"""Challenge management API routes."""

import uuid
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.challenge import Challenge, ChallengeStatus
from app.models.habit import Habit
from app.models.daily_entry import DailyEntry
from app.schemas.challenge import ChallengeCreate, ChallengeResponse, ChallengeUpdate
from app.schemas.progress import ChallengeProgressResponse, DayProgress, HabitProgress
from app.utils.habit_templates import get_template_by_id

router = APIRouter()


@router.get("", response_model=List[ChallengeResponse])
async def get_challenges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all challenges for the current user.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        List[ChallengeResponse]: List of user's challenges
    """
    challenges = db.query(Challenge).filter(
        Challenge.user_id == current_user.id
    ).order_by(Challenge.created_at.desc()).all()
    return challenges


@router.post("", response_model=ChallengeResponse, status_code=status.HTTP_201_CREATED)
async def create_challenge(
    challenge_data: ChallengeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new 30-day challenge.

    Args:
        challenge_data: Challenge creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        ChallengeResponse: Created challenge
    """
    # Calculate end date (30 days from start)
    end_date = challenge_data.start_date + timedelta(days=30)

    challenge = Challenge(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        start_date=challenge_data.start_date,
        end_date=end_date,
        status=ChallengeStatus.ACTIVE
    )

    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return challenge


@router.get("/{challenge_id}", response_model=ChallengeResponse)
async def get_challenge(
    challenge_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific challenge by ID.

    Args:
        challenge_id: Challenge ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        ChallengeResponse: Challenge details

    Raises:
        HTTPException: If challenge not found or not owned by user
    """
    challenge = db.query(Challenge).filter(
        Challenge.id == challenge_id,
        Challenge.user_id == current_user.id
    ).first()

    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found"
        )

    return challenge


@router.put("/{challenge_id}", response_model=ChallengeResponse)
async def update_challenge(
    challenge_id: str,
    challenge_update: ChallengeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a challenge's status.

    Args:
        challenge_id: Challenge ID
        challenge_update: Challenge update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        ChallengeResponse: Updated challenge

    Raises:
        HTTPException: If challenge not found or not owned by user
    """
    challenge = db.query(Challenge).filter(
        Challenge.id == challenge_id,
        Challenge.user_id == current_user.id
    ).first()

    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found"
        )

    if challenge_update.status:
        challenge.status = ChallengeStatus(challenge_update.status)

    db.commit()
    db.refresh(challenge)
    return challenge


@router.delete("/{challenge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_challenge(
    challenge_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a challenge.

    Args:
        challenge_id: Challenge ID
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If challenge not found or not owned by user
    """
    challenge = db.query(Challenge).filter(
        Challenge.id == challenge_id,
        Challenge.user_id == current_user.id
    ).first()

    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found"
        )

    db.delete(challenge)
    db.commit()


def normalize_date(dt: datetime) -> datetime:
    """Normalize datetime to start of day (midnight UTC), removing timezone info."""
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


@router.get("/{challenge_id}/progress", response_model=ChallengeProgressResponse)
async def get_challenge_progress(
    challenge_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get progress statistics for a challenge.
    
    This endpoint calculates comprehensive progress metrics including:
    - Overall completion percentage
    - Current and longest streaks
    - Last 7 days activity
    - Per-habit completion rates
    
    Args:
        challenge_id: Challenge ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        ChallengeProgressResponse: Progress statistics
    
    Raises:
        HTTPException: If challenge not found or not owned by user
    """
    # Verify challenge ownership
    challenge = db.query(Challenge).filter(
        Challenge.id == challenge_id,
        Challenge.user_id == current_user.id
    ).first()
    
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found"
        )
    
    # Get all active habits for this challenge
    habits = db.query(Habit).filter(
        Habit.challenge_id == challenge_id,
        Habit.is_active == True
    ).order_by(Habit.order).all()
    
    if not habits:
        # Return empty progress if no habits
        return ChallengeProgressResponse(
            challenge_id=challenge_id,
            start_date=challenge.start_date,
            end_date=challenge.end_date,
            current_day=0,
            total_days=30,
            days_elapsed=0,
            total_habits_completed=0,
            total_possible_habits=0,
            overall_completion_percentage=0,
            current_streak=0,
            longest_streak=0,
            last_7_days=[],
            habit_progress=[]
        )
    
    habit_ids = [habit.id for habit in habits]
    
    # Calculate current day and days elapsed
    today = normalize_date(datetime.utcnow())
    start_date = normalize_date(challenge.start_date)
    end_date = normalize_date(challenge.end_date)
    
    days_elapsed = max(0, (today - start_date).days)
    current_day = min(days_elapsed + 1, 30)
    total_days = (end_date - start_date).days + 1
    
    # Get all entries for this challenge within the relevant date range
    all_entries = db.query(DailyEntry).filter(
        DailyEntry.habit_id.in_(habit_ids),
        DailyEntry.date >= start_date,
        DailyEntry.date <= today
    ).all()
    
    # Calculate total habits completed and total possible habits
    # Account for when each habit was created
    total_habits_completed = sum(1 for entry in all_entries if entry.completed)
    total_possible_habits = 0

    for habit in habits:
        # Calculate how many days this habit has been active
        habit_created = normalize_date(habit.created_at)
        habit_start = max(habit_created, start_date)
        habit_days_active = min((today - habit_start).days + 1, current_day)
        total_possible_habits += max(0, habit_days_active)

    overall_completion_percentage = (
        round((total_habits_completed / total_possible_habits) * 100)
        if total_possible_habits > 0 else 0
    )
    
    # Helper function to get habits active on a given date
    def get_active_habits_for_date(check_date: datetime):
        """Return list of habits that were active on the given date."""
        return [h for h in habits if normalize_date(h.created_at) <= check_date]

    # Calculate streaks
    # A perfect day is when all habits active on that day are completed
    entries_by_date = {}
    for entry in all_entries:
        date_key = normalize_date(entry.date)
        if date_key not in entries_by_date:
            entries_by_date[date_key] = []
        entries_by_date[date_key].append(entry)

    # Calculate streaks by checking consecutive perfect days
    current_streak = 0
    longest_streak = 0
    temp_streak = 0

    # Check from start date to today
    check_date = start_date
    while check_date <= today:
        day_entries = entries_by_date.get(check_date, [])
        completed_count = sum(1 for e in day_entries if e.completed)
        active_habits = get_active_habits_for_date(check_date)

        if len(active_habits) > 0 and completed_count == len(active_habits):
            # Perfect day (all active habits completed)
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        else:
            temp_streak = 0

        check_date += timedelta(days=1)

    # Current streak is the streak of completed days leading up to (but not including) today
    # We start from yesterday because today might still be in progress
    check_date = today - timedelta(days=1)
    while check_date >= start_date:
        day_entries = entries_by_date.get(check_date, [])
        completed_count = sum(1 for e in day_entries if e.completed)
        active_habits = get_active_habits_for_date(check_date)

        if len(active_habits) > 0 and completed_count == len(active_habits):
            current_streak += 1
        else:
            break

        check_date -= timedelta(days=1)
    
    # Get last 7 days progress
    last_7_days = []
    for i in range(6, -1, -1):  # Last 7 days (6 days ago to today)
        check_date = today - timedelta(days=i)
        if check_date < start_date:
            continue

        day_entries = entries_by_date.get(check_date, [])
        completed_count = sum(1 for e in day_entries if e.completed)
        active_habits = get_active_habits_for_date(check_date)
        total_count = len(active_habits)
        is_perfect = total_count > 0 and completed_count == total_count
        completion_percentage = round((completed_count / total_count) * 100) if total_count > 0 else 0

        last_7_days.append(DayProgress(
            date=check_date,
            completed_count=completed_count,
            total_count=total_count,
            is_perfect=is_perfect,
            completion_percentage=completion_percentage
        ))
    
    # Calculate per-habit progress
    habit_progress = []
    for habit in habits:
        habit_entries = [e for e in all_entries if e.habit_id == habit.id]
        completed_count = sum(1 for e in habit_entries if e.completed)

        # Calculate days this habit has been active
        habit_created = normalize_date(habit.created_at)
        habit_start = max(habit_created, start_date)
        habit_days_active = min((today - habit_start).days + 1, current_day)
        habit_total_days = max(0, habit_days_active)

        completion_percentage = round((completed_count / habit_total_days) * 100) if habit_total_days > 0 else 0

        # Get icon from habit template if available
        icon = None
        if habit.template_id:
            template = get_template_by_id(habit.template_id)
            if template:
                icon = template.get('icon')

        habit_progress.append(HabitProgress(
            habit_id=habit.id,
            habit_name=habit.name,
            icon=icon,
            completed_count=completed_count,
            total_days=habit_total_days,
            completion_percentage=completion_percentage
        ))
    
    return ChallengeProgressResponse(
        challenge_id=challenge_id,
        start_date=challenge.start_date,
        end_date=challenge.end_date,
        current_day=current_day,
        total_days=total_days,
        days_elapsed=days_elapsed,
        total_habits_completed=total_habits_completed,
        total_possible_habits=total_possible_habits,
        overall_completion_percentage=overall_completion_percentage,
        current_streak=current_streak,
        longest_streak=longest_streak,
        last_7_days=last_7_days,
        habit_progress=habit_progress
    )
