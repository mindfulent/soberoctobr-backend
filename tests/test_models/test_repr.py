"""Tests for model __repr__ methods."""

from datetime import datetime
from app.models.user import User
from app.models.challenge import Challenge, ChallengeStatus
from app.models.habit import Habit, HabitType
from app.models.daily_entry import DailyEntry


def test_user_repr():
    """Test User __repr__ method."""
    user = User(
        id="user-123",
        email="test@example.com",
        name="Test User",
        google_id="google-123"
    )
    result = repr(user)
    assert result == "<User(id=user-123, email=test@example.com, name=Test User)>"


def test_challenge_repr():
    """Test Challenge __repr__ method."""
    challenge = Challenge(
        id="challenge-123",
        user_id="user-123",
        start_date=datetime(2024, 10, 1),
        end_date=datetime(2024, 10, 31),
        status=ChallengeStatus.ACTIVE
    )
    result = repr(challenge)
    assert result == "<Challenge(id=challenge-123, user_id=user-123, status=ChallengeStatus.ACTIVE)>"


def test_habit_repr():
    """Test Habit __repr__ method."""
    habit = Habit(
        id="habit-123",
        challenge_id="challenge-123",
        name="Test Habit",
        type=HabitType.BINARY
    )
    result = repr(habit)
    assert result == "<Habit(id=habit-123, name=Test Habit, type=HabitType.BINARY)>"


def test_daily_entry_repr():
    """Test DailyEntry __repr__ method."""
    entry_date = datetime(2024, 10, 1)
    entry = DailyEntry(
        id="entry-123",
        habit_id="habit-123",
        date=entry_date,
        completed=True
    )
    result = repr(entry)
    assert result == f"<DailyEntry(id=entry-123, habit_id=habit-123, date={entry_date}, completed=True)>"
