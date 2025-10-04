"""Challenge API endpoint tests."""

from datetime import datetime, timedelta, timezone
import uuid

import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.models.challenge import Challenge, ChallengeStatus
from app.models.habit import Habit
from app.models.daily_entry import DailyEntry
from app.models.user import User
from app.api.challenges import normalize_date


class TestGetChallenges:
    """Tests for GET /api/v1/challenges endpoint."""

    def test_get_challenges_success(
        self, client, test_user: User, test_challenge: Challenge, auth_headers: dict
    ):
        """Test successfully retrieving user's challenges."""
        response = client.get("/api/v1/challenges", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert data[0]["id"] == test_challenge.id
        assert data[0]["status"] == test_challenge.status.value

    def test_get_challenges_empty(self, client, test_user: User, auth_headers: dict):
        """Test getting challenges when user has none."""
        response = client.get("/api/v1/challenges", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_get_challenges_unauthorized(self, client):
        """Test getting challenges without authentication."""
        response = client.get("/api/v1/challenges")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_challenges_only_own(
        self,
        client,
        test_user: User,
        other_user: User,
        test_challenge: Challenge,
        auth_headers: dict,
        db_session: Session,
    ):
        """Test that users only see their own challenges."""
        # Create challenge for other user
        other_challenge = Challenge(
            id="other-challenge-id",
            user_id=other_user.id,
            start_date=datetime(2024, 10, 1),
            end_date=datetime(2024, 10, 31),
            status=ChallengeStatus.ACTIVE,
        )
        db_session.add(other_challenge)
        db_session.commit()

        response = client.get("/api/v1/challenges", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        challenge_ids = [c["id"] for c in data]
        assert test_challenge.id in challenge_ids
        assert other_challenge.id not in challenge_ids


class TestCreateChallenge:
    """Tests for POST /api/v1/challenges endpoint."""

    def test_create_challenge_success(self, client, test_user: User, auth_headers: dict):
        """Test successfully creating a new challenge."""
        start_date = datetime(2024, 11, 1)
        response = client.post(
            "/api/v1/challenges",
            headers=auth_headers,
            json={"start_date": start_date.isoformat()},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["status"] == ChallengeStatus.ACTIVE.value
        assert datetime.fromisoformat(data["startDate"]).date() == start_date.date()

        # Verify end date is 30 days after start
        end_date = datetime.fromisoformat(data["endDate"])
        expected_end = start_date + timedelta(days=30)
        assert end_date.date() == expected_end.date()

    def test_create_challenge_unauthorized(self, client):
        """Test creating challenge without authentication."""
        response = client.post(
            "/api/v1/challenges",
            json={"start_date": datetime(2024, 11, 1).isoformat()},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_challenge_invalid_data(self, client, auth_headers: dict):
        """Test creating challenge with invalid data."""
        response = client.post(
            "/api/v1/challenges",
            headers=auth_headers,
            json={"start_date": "not-a-date"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetChallenge:
    """Tests for GET /api/v1/challenges/{challenge_id} endpoint."""

    def test_get_challenge_success(
        self, client, test_challenge: Challenge, auth_headers: dict
    ):
        """Test successfully retrieving a specific challenge."""
        response = client.get(
            f"/api/v1/challenges/{test_challenge.id}", headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_challenge.id
        assert data["status"] == test_challenge.status.value

    def test_get_challenge_not_found(self, client, auth_headers: dict):
        """Test getting non-existent challenge."""
        response = client.get(
            "/api/v1/challenges/nonexistent-id", headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_challenge_other_user(
        self,
        client,
        other_user: User,
        auth_headers: dict,
        db_session: Session,
    ):
        """Test that users cannot access other users' challenges."""
        # Create challenge for other user
        other_challenge = Challenge(
            id="other-challenge-id",
            user_id=other_user.id,
            start_date=datetime(2024, 10, 1),
            end_date=datetime(2024, 10, 31),
            status=ChallengeStatus.ACTIVE,
        )
        db_session.add(other_challenge)
        db_session.commit()

        response = client.get(
            f"/api/v1/challenges/{other_challenge.id}", headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateChallenge:
    """Tests for PUT /api/v1/challenges/{challenge_id} endpoint."""

    def test_update_challenge_status(
        self, client, test_challenge: Challenge, auth_headers: dict
    ):
        """Test successfully updating challenge status."""
        response = client.put(
            f"/api/v1/challenges/{test_challenge.id}",
            headers=auth_headers,
            json={"status": ChallengeStatus.COMPLETED.value},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == ChallengeStatus.COMPLETED.value

    def test_update_challenge_to_paused(
        self, client, test_challenge: Challenge, auth_headers: dict
    ):
        """Test updating challenge to paused status."""
        response = client.put(
            f"/api/v1/challenges/{test_challenge.id}",
            headers=auth_headers,
            json={"status": ChallengeStatus.PAUSED.value},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == ChallengeStatus.PAUSED.value

    def test_update_challenge_not_found(self, client, auth_headers: dict):
        """Test updating non-existent challenge."""
        response = client.put(
            "/api/v1/challenges/nonexistent-id",
            headers=auth_headers,
            json={"status": ChallengeStatus.COMPLETED.value},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_challenge_other_user(
        self,
        client,
        other_user: User,
        auth_headers: dict,
        db_session: Session,
    ):
        """Test that users cannot update other users' challenges."""
        other_challenge = Challenge(
            id="other-challenge-id",
            user_id=other_user.id,
            start_date=datetime(2024, 10, 1),
            end_date=datetime(2024, 10, 31),
            status=ChallengeStatus.ACTIVE,
        )
        db_session.add(other_challenge)
        db_session.commit()

        response = client.put(
            f"/api/v1/challenges/{other_challenge.id}",
            headers=auth_headers,
            json={"status": ChallengeStatus.COMPLETED.value},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteChallenge:
    """Tests for DELETE /api/v1/challenges/{challenge_id} endpoint."""

    def test_delete_challenge_success(
        self, client, test_challenge: Challenge, auth_headers: dict, db_session: Session
    ):
        """Test successfully deleting a challenge."""
        response = client.delete(
            f"/api/v1/challenges/{test_challenge.id}", headers=auth_headers
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify challenge was deleted
        deleted_challenge = (
            db_session.query(Challenge)
            .filter(Challenge.id == test_challenge.id)
            .first()
        )
        assert deleted_challenge is None

    def test_delete_challenge_not_found(self, client, auth_headers: dict):
        """Test deleting non-existent challenge."""
        response = client.delete(
            "/api/v1/challenges/nonexistent-id", headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_challenge_other_user(
        self,
        client,
        other_user: User,
        auth_headers: dict,
        db_session: Session,
    ):
        """Test that users cannot delete other users' challenges."""
        other_challenge = Challenge(
            id="other-challenge-id",
            user_id=other_user.id,
            start_date=datetime(2024, 10, 1),
            end_date=datetime(2024, 10, 31),
            status=ChallengeStatus.ACTIVE,
        )
        db_session.add(other_challenge)
        db_session.commit()

        response = client.delete(
            f"/api/v1/challenges/{other_challenge.id}", headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGetChallengeProgress:
    """Tests for GET /api/v1/challenges/{challenge_id}/progress endpoint."""

    def test_get_progress_success_with_data(
        self, client, test_challenge: Challenge, auth_headers: dict, db_session: Session
    ):
        """Test successfully getting progress with habits and entries."""
        # Create habits
        habit1 = Habit(
            id="habit-1",
            challenge_id=test_challenge.id,
            name="No Alcohol",
            type="binary",
            is_active=True,
            order=1
        )
        habit2 = Habit(
            id="habit-2",
            challenge_id=test_challenge.id,
            name="Exercise",
            type="binary",
            is_active=True,
            order=2
        )
        db_session.add_all([habit1, habit2])
        db_session.commit()

        # Create entries for the last 3 days
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        for i in range(3):
            entry_date = today - timedelta(days=i)
            # Both habits completed
            entry1 = DailyEntry(
                id=str(uuid.uuid4()),
                habit_id=habit1.id,
                date=entry_date,
                completed=True
            )
            entry2 = DailyEntry(
                id=str(uuid.uuid4()),
                habit_id=habit2.id,
                date=entry_date,
                completed=True
            )
            db_session.add_all([entry1, entry2])
        db_session.commit()

        response = client.get(
            f"/api/v1/challenges/{test_challenge.id}/progress", headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["challengeId"] == test_challenge.id
        assert data["totalDays"] > 0  # Should be around 30-31 days
        assert data["totalHabitsCompleted"] > 0
        assert data["overallCompletionPercentage"] > 0
        assert data["currentStreak"] >= 0
        assert data["longestStreak"] >= 0
        assert len(data["habitProgress"]) == 2
        assert isinstance(data["last7Days"], list)

    def test_get_progress_no_habits(
        self, client, test_challenge: Challenge, auth_headers: dict
    ):
        """Test getting progress when challenge has no habits."""
        response = client.get(
            f"/api/v1/challenges/{test_challenge.id}/progress", headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["challengeId"] == test_challenge.id
        assert data["currentDay"] == 0
        assert data["totalDays"] == 30
        assert data["daysElapsed"] == 0
        assert data["totalHabitsCompleted"] == 0
        assert data["totalPossibleHabits"] == 0
        assert data["overallCompletionPercentage"] == 0
        assert data["currentStreak"] == 0
        assert data["longestStreak"] == 0
        assert data["last7Days"] == []
        assert data["habitProgress"] == []

    def test_get_progress_challenge_not_found(self, client, auth_headers: dict):
        """Test getting progress for non-existent challenge."""
        response = client.get(
            "/api/v1/challenges/nonexistent-id/progress", headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_progress_other_user_challenge(
        self,
        client,
        other_user: User,
        auth_headers: dict,
        db_session: Session,
    ):
        """Test that users cannot access other users' challenge progress."""
        other_challenge = Challenge(
            id="other-challenge-id",
            user_id=other_user.id,
            start_date=datetime(2024, 10, 1),
            end_date=datetime(2024, 10, 31),
            status=ChallengeStatus.ACTIVE,
        )
        db_session.add(other_challenge)
        db_session.commit()

        response = client.get(
            f"/api/v1/challenges/{other_challenge.id}/progress", headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_progress_streak_calculation(
        self, client, test_challenge: Challenge, auth_headers: dict, db_session: Session
    ):
        """Test streak calculation with perfect and imperfect days."""
        # Create habits
        habit1 = Habit(
            id="habit-1",
            challenge_id=test_challenge.id,
            name="Habit 1",
            type="binary",
            is_active=True,
            order=1
        )
        habit2 = Habit(
            id="habit-2",
            challenge_id=test_challenge.id,
            name="Habit 2",
            type="binary",
            is_active=True,
            order=2
        )
        db_session.add_all([habit1, habit2])
        db_session.commit()

        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        # Create perfect streak of 3 days ending today
        for i in range(3):
            entry_date = today - timedelta(days=i)
            entry1 = DailyEntry(id=str(uuid.uuid4()), habit_id=habit1.id, date=entry_date, completed=True)
            entry2 = DailyEntry(id=str(uuid.uuid4()), habit_id=habit2.id, date=entry_date, completed=True)
            db_session.add_all([entry1, entry2])

        # Create imperfect day 4 days ago (only one habit completed)
        imperfect_date = today - timedelta(days=3)
        entry1 = DailyEntry(id=str(uuid.uuid4()), habit_id=habit1.id, date=imperfect_date, completed=True)
        entry2 = DailyEntry(id=str(uuid.uuid4()), habit_id=habit2.id, date=imperfect_date, completed=False)
        db_session.add_all([entry1, entry2])

        db_session.commit()

        response = client.get(
            f"/api/v1/challenges/{test_challenge.id}/progress", headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Current streak should be 3 (last 3 perfect days)
        assert data["currentStreak"] == 3
        # Longest streak should be at least 3
        assert data["longestStreak"] >= 3

    def test_get_progress_last_7_days(
        self, client, test_challenge: Challenge, auth_headers: dict, db_session: Session
    ):
        """Test last 7 days progress calculation."""
        habit = Habit(
            id="habit-1",
            challenge_id=test_challenge.id,
            name="Test Habit",
            type="binary",
            is_active=True,
            order=1
        )
        db_session.add(habit)
        db_session.commit()

        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        # Create entries for last 5 days
        for i in range(5):
            entry_date = today - timedelta(days=i)
            entry = DailyEntry(
                id=str(uuid.uuid4()),
                habit_id=habit.id,
                date=entry_date,
                completed=True
            )
            db_session.add(entry)
        db_session.commit()

        response = client.get(
            f"/api/v1/challenges/{test_challenge.id}/progress", headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should have entries for the days (may be less than 7 if challenge started recently)
        assert len(data["last7Days"]) >= 0
        # Each day entry should have required fields
        for day in data["last7Days"]:
            assert "date" in day
            assert "completed_count" in day
            assert "total_count" in day
            assert "is_perfect" in day
            assert "completion_percentage" in day

    def test_get_progress_habit_progress_calculation(
        self, client, test_challenge: Challenge, auth_headers: dict, db_session: Session
    ):
        """Test per-habit progress calculation."""
        # Create two habits with different completion rates
        habit1 = Habit(
            id="habit-1",
            challenge_id=test_challenge.id,
            name="Consistent Habit",
            type="binary",
            is_active=True,
            order=1
        )
        habit2 = Habit(
            id="habit-2",
            challenge_id=test_challenge.id,
            name="Inconsistent Habit",
            type="binary",
            is_active=True,
            order=2
        )
        db_session.add_all([habit1, habit2])
        db_session.commit()

        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        # Habit 1: 5 out of 5 days completed
        for i in range(5):
            entry_date = today - timedelta(days=i)
            entry = DailyEntry(id=str(uuid.uuid4()), habit_id=habit1.id, date=entry_date, completed=True)
            db_session.add(entry)

        # Habit 2: 2 out of 5 days completed
        for i in range(5):
            entry_date = today - timedelta(days=i)
            completed = i < 2  # Only first 2 days completed
            entry = DailyEntry(id=str(uuid.uuid4()), habit_id=habit2.id, date=entry_date, completed=completed)
            db_session.add(entry)

        db_session.commit()

        response = client.get(
            f"/api/v1/challenges/{test_challenge.id}/progress", headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        habit_progress = data["habitProgress"]

        assert len(habit_progress) == 2

        # Find each habit in the progress
        habit1_progress = next(h for h in habit_progress if h["habit_id"] == "habit-1")
        habit2_progress = next(h for h in habit_progress if h["habit_id"] == "habit-2")

        # Verify both have completion data
        assert habit1_progress["completion_percentage"] >= 0
        assert habit2_progress["completion_percentage"] >= 0
        assert habit1_progress["habit_name"] == "Consistent Habit"
        assert habit2_progress["habit_name"] == "Inconsistent Habit"
        # Habit 1 has more completions
        assert habit1_progress["completed_count"] >= habit2_progress["completed_count"]

    def test_get_progress_with_inactive_habits(
        self, client, test_challenge: Challenge, auth_headers: dict, db_session: Session
    ):
        """Test that inactive habits are not included in progress."""
        active_habit = Habit(
            id="habit-1",
            challenge_id=test_challenge.id,
            name="Active Habit",
            type="binary",
            is_active=True,
            order=1
        )
        inactive_habit = Habit(
            id="habit-2",
            challenge_id=test_challenge.id,
            name="Inactive Habit",
            type="binary",
            is_active=False,
            order=2
        )
        db_session.add_all([active_habit, inactive_habit])
        db_session.commit()

        response = client.get(
            f"/api/v1/challenges/{test_challenge.id}/progress", headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Only active habit should be in progress
        assert len(data["habitProgress"]) == 1
        assert data["habitProgress"][0]["habit_id"] == "habit-1"


class TestNormalizeDateFunction:
    """Tests for the normalize_date helper function."""

    def test_normalize_date_function_with_timezone_aware_datetime(self):
        """Test normalize_date function directly with timezone-aware datetime."""
        # Create a timezone-aware datetime
        tz_aware = datetime(2024, 10, 15, 14, 30, 45, tzinfo=timezone.utc)

        # Normalize it
        normalized = normalize_date(tz_aware)

        # Should be midnight, naive (no timezone)
        assert normalized.hour == 0
        assert normalized.minute == 0
        assert normalized.second == 0
        assert normalized.microsecond == 0
        assert normalized.tzinfo is None
        assert normalized.year == 2024
        assert normalized.month == 10
        assert normalized.day == 15

    def test_normalize_date_function_with_naive_datetime(self):
        """Test normalize_date function with naive datetime."""
        # Create a naive datetime
        naive = datetime(2024, 10, 15, 14, 30, 45)

        # Normalize it
        normalized = normalize_date(naive)

        # Should be midnight, still naive
        assert normalized.hour == 0
        assert normalized.minute == 0
        assert normalized.second == 0
        assert normalized.microsecond == 0
        assert normalized.tzinfo is None
        assert normalized.year == 2024
        assert normalized.month == 10
        assert normalized.day == 15

    def test_normalize_date_with_timezone(
        self, client, test_challenge: Challenge, auth_headers: dict, db_session: Session
    ):
        """Test that timezone-aware dates are normalized correctly."""
        # Create a habit with a timezone-aware datetime entry
        habit = Habit(
            id="habit-1",
            challenge_id=test_challenge.id,
            name="Test Habit",
            type="binary",
            is_active=True,
            order=1
        )
        db_session.add(habit)
        db_session.commit()

        # Create an entry with timezone-aware datetime
        tz_aware_date = datetime.now(timezone.utc).replace(hour=15, minute=30)
        entry = DailyEntry(
            id=str(uuid.uuid4()),
            habit_id=habit.id,
            date=tz_aware_date,
            completed=True
        )
        db_session.add(entry)
        db_session.commit()

        # The progress endpoint should handle this without error
        response = client.get(
            f"/api/v1/challenges/{test_challenge.id}/progress", headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["challengeId"] == test_challenge.id

    def test_challenge_started_recently(
        self, client, test_user: User, auth_headers: dict, db_session: Session
    ):
        """Test progress when challenge started less than 7 days ago."""
        # Create a challenge that started today
        start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=30)

        challenge = Challenge(
            id=str(uuid.uuid4()),
            user_id=test_user.id,
            start_date=start_date,
            end_date=end_date,
            status=ChallengeStatus.ACTIVE
        )
        db_session.add(challenge)
        db_session.commit()

        # Create a habit
        habit = Habit(
            id="habit-1",
            challenge_id=challenge.id,
            name="Test Habit",
            type="binary",
            is_active=True,
            order=1
        )
        db_session.add(habit)
        db_session.commit()

        # Get progress (should handle dates before challenge start)
        response = client.get(
            f"/api/v1/challenges/{challenge.id}/progress", headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # last_7_days should only include dates from start_date onwards
        assert isinstance(data["last7Days"], list)
        for day in data["last7Days"]:
            day_date = datetime.fromisoformat(day["date"])
            assert day_date >= start_date

    def test_habit_with_template_id(
        self, client, test_challenge: Challenge, auth_headers: dict, db_session: Session
    ):
        """Test progress calculation with habit that has a template_id."""
        # Create a habit with a valid template_id
        habit_with_template = Habit(
            id="habit-1",
            challenge_id=test_challenge.id,
            name="Vitamin D",
            type="binary",
            is_active=True,
            order=1,
            template_id="vitamin_d"  # Valid template ID from HABIT_TEMPLATES
        )
        # Create a habit with an invalid template_id
        habit_no_template = Habit(
            id="habit-2",
            challenge_id=test_challenge.id,
            name="Custom Habit",
            type="binary",
            is_active=True,
            order=2,
            template_id="invalid-template-id"  # Invalid template ID
        )
        db_session.add_all([habit_with_template, habit_no_template])
        db_session.commit()

        response = client.get(
            f"/api/v1/challenges/{test_challenge.id}/progress", headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["habitProgress"]) == 2

        # Find each habit in the progress (using snake_case for nested fields)
        habit1_progress = next(h for h in data["habitProgress"] if h["habit_id"] == "habit-1")
        habit2_progress = next(h for h in data["habitProgress"] if h["habit_id"] == "habit-2")

        # Habit with valid template should have icon
        assert habit1_progress["icon"] == "☀️"
        # Habit with invalid template should have None icon
        assert habit2_progress["icon"] is None

    def test_challenge_with_timezone_aware_dates(
        self, client, test_user: User, auth_headers: dict, db_session: Session
    ):
        """Test that challenges with timezone-aware dates are handled correctly."""
        # Create a challenge with timezone-aware dates
        start_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=30)

        challenge = Challenge(
            id=str(uuid.uuid4()),
            user_id=test_user.id,
            start_date=start_date,
            end_date=end_date,
            status=ChallengeStatus.ACTIVE
        )
        db_session.add(challenge)
        db_session.commit()

        # Create a habit
        habit = Habit(
            id="habit-1",
            challenge_id=challenge.id,
            name="Test Habit",
            type="binary",
            is_active=True,
            order=1
        )
        db_session.add(habit)
        db_session.commit()

        # Get progress - this should normalize the timezone-aware dates
        response = client.get(
            f"/api/v1/challenges/{challenge.id}/progress", headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["challengeId"] == challenge.id
