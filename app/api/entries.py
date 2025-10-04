"""Daily entry tracking API routes."""

import uuid
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.habit import Habit
from app.models.daily_entry import DailyEntry
from app.models.challenge import Challenge
from app.schemas.daily_entry import DailyEntryCreate, DailyEntryResponse, DailyEntryUpdate

router = APIRouter()


def normalize_date(dt: datetime) -> datetime:
    """Normalize datetime to start of day (midnight UTC), removing timezone info."""
    # Remove timezone info to make comparison possible
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


@router.get("/habits/{habit_id}/entries", response_model=List[DailyEntryResponse])
async def get_habit_entries(
    habit_id: str,
    start_date: datetime = None,
    end_date: datetime = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all daily entries for a specific habit.

    Args:
        habit_id: Habit ID
        start_date: Optional start date filter
        end_date: Optional end date filter
        current_user: Current authenticated user
        db: Database session

    Returns:
        List[DailyEntryResponse]: List of daily entries

    Raises:
        HTTPException: If habit not found or not owned by user
    """
    # Verify habit ownership
    habit = db.query(Habit).join(Challenge).filter(
        Habit.id == habit_id,
        Challenge.user_id == current_user.id
    ).first()

    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found"
        )

    query = db.query(DailyEntry).filter(DailyEntry.habit_id == habit_id)

    if start_date:
        query = query.filter(DailyEntry.date >= normalize_date(start_date))
    if end_date:
        query = query.filter(DailyEntry.date <= normalize_date(end_date))

    entries = query.order_by(DailyEntry.date.desc()).all()
    return entries


@router.post("/habits/{habit_id}/entries", response_model=DailyEntryResponse)
async def create_or_update_entry(
    habit_id: str,
    entry_data: DailyEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create or update a daily entry for a habit.

    Args:
        habit_id: Habit ID
        entry_data: Entry creation/update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        DailyEntryResponse: Created or updated entry

    Raises:
        HTTPException: If habit not found, not owned by user, date outside challenge period, or future date
    """
    # Verify habit ownership and get associated challenge
    habit = db.query(Habit).join(Challenge).filter(
        Habit.id == habit_id,
        Challenge.user_id == current_user.id
    ).first()

    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found"
        )

    # Get the challenge for date validation
    challenge = db.query(Challenge).filter(
        Challenge.id == habit.challenge_id
    ).first()

    # Normalize date to start of day
    entry_date = normalize_date(entry_data.date)
    today = normalize_date(datetime.utcnow())
    challenge_start = normalize_date(challenge.start_date)
    challenge_end = normalize_date(challenge.end_date)

    # Check if date is in the future
    if entry_date > today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create entries for future dates"
        )

    # Check if date is within challenge period
    if entry_date < challenge_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create entries before the challenge start date"
        )
    
    if entry_date > challenge_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create entries after the challenge end date"
        )

    # Check if entry already exists
    existing_entry = db.query(DailyEntry).filter(
        DailyEntry.habit_id == habit_id,
        DailyEntry.date == entry_date
    ).first()

    if existing_entry:
        # Update existing entry
        existing_entry.completed = entry_data.completed
        existing_entry.count = entry_data.count
        db.commit()
        db.refresh(existing_entry)
        return existing_entry
    else:
        # Create new entry
        entry = DailyEntry(
            id=str(uuid.uuid4()),
            habit_id=habit_id,
            date=entry_date,
            completed=entry_data.completed,
            count=entry_data.count
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry


@router.get("/challenges/{challenge_id}/entries/{date}", response_model=List[DailyEntryResponse])
async def get_daily_entries_for_challenge(
    challenge_id: str,
    date: datetime,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all entries for a specific date within a challenge.

    Args:
        challenge_id: Challenge ID
        date: Date to get entries for
        current_user: Current authenticated user
        db: Database session

    Returns:
        List[DailyEntryResponse]: List of entries for the date

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

    # Normalize date
    normalized_date = normalize_date(date)

    # Get all habits for the challenge
    habits = db.query(Habit).filter(
        Habit.challenge_id == challenge_id,
        Habit.is_active == True
    ).all()

    habit_ids = [habit.id for habit in habits]

    # Get entries for those habits on the specified date
    entries = db.query(DailyEntry).filter(
        DailyEntry.habit_id.in_(habit_ids),
        DailyEntry.date == normalized_date
    ).all()

    return entries


@router.put("/entries/{entry_id}", response_model=DailyEntryResponse)
async def update_entry(
    entry_id: str,
    entry_update: DailyEntryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a daily entry.

    Args:
        entry_id: Entry ID
        entry_update: Entry update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        DailyEntryResponse: Updated entry

    Raises:
        HTTPException: If entry not found or not owned by user
    """
    # Verify entry ownership through habit -> challenge -> user
    entry = db.query(DailyEntry).join(Habit).join(Challenge).filter(
        DailyEntry.id == entry_id,
        Challenge.user_id == current_user.id
    ).first()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found"
        )

    # Update fields if provided
    if entry_update.completed is not None:
        entry.completed = entry_update.completed
    if entry_update.count is not None:
        entry.count = entry_update.count

    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a daily entry.

    Args:
        entry_id: Entry ID
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If entry not found or not owned by user
    """
    # Verify entry ownership
    entry = db.query(DailyEntry).join(Habit).join(Challenge).filter(
        DailyEntry.id == entry_id,
        Challenge.user_id == current_user.id
    ).first()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found"
        )

    db.delete(entry)
    db.commit()
