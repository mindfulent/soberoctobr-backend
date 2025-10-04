"""Daily entry API endpoint tests."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.models.challenge import Challenge
from app.models.daily_entry import DailyEntry
from app.models.habit import Habit, HabitType
from app.models.user import User


class TestGetHabitEntries:
    """Tests for GET /api/v1/habits/{habit_id}/entries endpoint."""

    def test_get_entries_success(
        self,
        client,
        test_binary_habit: Habit,
        test_entry: DailyEntry,
        auth_headers: dict,
    ):
        """Test successfully retrieving entries for a habit."""
        response = client.get(
            f"/api/v1/habits/{test_binary_habit.id}/entries",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert data[0]["id"] == test_entry.id
        assert data[0]["habit_id"] == test_binary_habit.id

    def test_get_entries_with_date_filter(
        self,
        client,
        test_binary_habit: Habit,
        auth_headers: dict,
        db_session: Session,
    ):
        """Test getting entries with date range filter."""
        # Create entries for different dates
        dates = [
            datetime(2024, 10, 1),
            datetime(2024, 10, 5),
            datetime(2024, 10, 10),
        ]
        for date in dates:
            entry = DailyEntry(
                id=f"entry-{date.day}",
                habit_id=test_binary_habit.id,
                date=date,
                completed=True,
            )
            db_session.add(entry)
        db_session.commit()

        # Query with date range
        response = client.get(
            f"/api/v1/habits/{test_binary_habit.id}/entries",
            headers=auth_headers,
            params={
                "start_date": "2024-10-03T00:00:00",
                "end_date": "2024-10-08T00:00:00",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should only include Oct 5 entry
        assert len(data) == 1

    def test_get_entries_habit_not_found(self, client, auth_headers: dict):
        """Test getting entries for non-existent habit."""
        response = client.get(
            "/api/v1/habits/nonexistent-id/entries",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCreateOrUpdateEntry:
    """Tests for POST /api/v1/habits/{habit_id}/entries endpoint."""

    def test_create_entry_success(
        self, client, test_binary_habit: Habit, auth_headers: dict
    ):
        """Test successfully creating a new entry."""
        entry_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        response = client.post(
            f"/api/v1/habits/{test_binary_habit.id}/entries",
            headers=auth_headers,
            json={
                "date": entry_date.isoformat(),
                "completed": True,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["completed"] is True
        assert data["habit_id"] == test_binary_habit.id

    def test_create_counted_entry_success(
        self, client, test_counted_habit: Habit, auth_headers: dict
    ):
        """Test creating entry for counted habit."""
        entry_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        response = client.post(
            f"/api/v1/habits/{test_counted_habit.id}/entries",
            headers=auth_headers,
            json={
                "date": entry_date.isoformat(),
                "count": 6,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["count"] == 6

    def test_update_existing_entry(
        self,
        client,
        test_binary_habit: Habit,
        auth_headers: dict,
        db_session: Session,
    ):
        """Test updating an existing entry (upsert behavior)."""
        # Use today's date to avoid retroactive logging restrictions
        entry_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        # Create initial entry
        entry = DailyEntry(
            id="test-entry-id",
            habit_id=test_binary_habit.id,
            date=entry_date,
            completed=False,
        )
        db_session.add(entry)
        db_session.commit()

        # Update via POST
        response = client.post(
            f"/api/v1/habits/{test_binary_habit.id}/entries",
            headers=auth_headers,
            json={
                "date": entry_date.isoformat(),
                "completed": True,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["completed"] is True
        assert data["id"] == "test-entry-id"  # Same entry, updated

    def test_create_entry_within_challenge_period(
        self, client, test_binary_habit: Habit, test_challenge: Challenge, auth_headers: dict
    ):
        """Test creating entry within challenge period is allowed."""
        # Entry within the challenge period (Oct 1-31)
        entry_date = datetime(2024, 10, 5)

        response = client.post(
            f"/api/v1/habits/{test_binary_habit.id}/entries",
            headers=auth_headers,
            json={
                "date": entry_date.isoformat(),
                "completed": True,
            },
        )

        assert response.status_code == status.HTTP_200_OK

    def test_create_entry_before_challenge_start(
        self, client, test_binary_habit: Habit, test_challenge: Challenge, auth_headers: dict
    ):
        """Test that entries before challenge start date are rejected."""
        # Entry before challenge start (challenge starts Oct 1)
        entry_date = datetime(2024, 9, 30)

        response = client.post(
            f"/api/v1/habits/{test_binary_habit.id}/entries",
            headers=auth_headers,
            json={
                "date": entry_date.isoformat(),
                "completed": True,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "before the challenge start date" in response.json()["detail"]

    def test_create_entry_after_challenge_end(
        self, client, test_binary_habit: Habit, test_challenge: Challenge, auth_headers: dict
    ):
        """Test that entries after challenge end date are rejected."""
        # Entry after challenge end (challenge ends Oct 31)
        entry_date = datetime(2024, 11, 1)

        response = client.post(
            f"/api/v1/habits/{test_binary_habit.id}/entries",
            headers=auth_headers,
            json={
                "date": entry_date.isoformat(),
                "completed": True,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "after the challenge end date" in response.json()["detail"]

    def test_create_entry_future_date(
        self, client, test_binary_habit: Habit, auth_headers: dict
    ):
        """Test that entries for future dates are rejected."""
        future_date = datetime.utcnow() + timedelta(days=1)

        response = client.post(
            f"/api/v1/habits/{test_binary_habit.id}/entries",
            headers=auth_headers,
            json={
                "date": future_date.isoformat(),
                "completed": True,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "future dates" in response.json()["detail"]

    def test_create_entry_habit_not_found(self, client, auth_headers: dict):
        """Test creating entry for non-existent habit."""
        response = client.post(
            "/api/v1/habits/nonexistent-id/entries",
            headers=auth_headers,
            json={
                "date": datetime.utcnow().isoformat(),
                "completed": True,
            },
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGetDailyEntriesForChallenge:
    """Tests for GET /api/v1/challenges/{challenge_id}/entries/{date} endpoint."""

    def test_get_challenge_entries_success(
        self,
        client,
        test_challenge: Challenge,
        test_binary_habit: Habit,
        test_counted_habit: Habit,
        auth_headers: dict,
        db_session: Session,
    ):
        """Test getting all entries for a challenge on a specific date."""
        entry_date = datetime(2024, 10, 10)

        # Create entries for both habits
        entry1 = DailyEntry(
            id="entry-1",
            habit_id=test_binary_habit.id,
            date=entry_date,
            completed=True,
        )
        entry2 = DailyEntry(
            id="entry-2",
            habit_id=test_counted_habit.id,
            date=entry_date,
            count=5,
        )
        db_session.add_all([entry1, entry2])
        db_session.commit()

        response = client.get(
            f"/api/v1/challenges/{test_challenge.id}/entries/{entry_date.isoformat()}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        habit_ids = [e["habit_id"] for e in data]
        assert test_binary_habit.id in habit_ids
        assert test_counted_habit.id in habit_ids

    def test_get_challenge_entries_empty(
        self,
        client,
        test_challenge: Challenge,
        test_binary_habit: Habit,
        auth_headers: dict,
    ):
        """Test getting entries when none exist for the date."""
        entry_date = datetime(2024, 10, 20)

        response = client.get(
            f"/api/v1/challenges/{test_challenge.id}/entries/{entry_date.isoformat()}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_challenge_entries_not_found(self, client, auth_headers: dict):
        """Test getting entries for non-existent challenge."""
        response = client.get(
            f"/api/v1/challenges/nonexistent-id/entries/{datetime.utcnow().isoformat()}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateEntry:
    """Tests for PUT /api/v1/entries/{entry_id} endpoint."""

    def test_update_entry_success(
        self, client, test_entry: DailyEntry, auth_headers: dict
    ):
        """Test successfully updating an entry."""
        response = client.put(
            f"/api/v1/entries/{test_entry.id}",
            headers=auth_headers,
            json={"completed": False},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["completed"] is False

    def test_update_entry_count(
        self,
        client,
        test_counted_habit: Habit,
        auth_headers: dict,
        db_session: Session,
    ):
        """Test updating count for counted habit entry."""
        entry = DailyEntry(
            id="counted-entry",
            habit_id=test_counted_habit.id,
            date=datetime(2024, 10, 10),
            count=3,
        )
        db_session.add(entry)
        db_session.commit()

        response = client.put(
            f"/api/v1/entries/{entry.id}",
            headers=auth_headers,
            json={"count": 7},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["count"] == 7

    def test_update_entry_not_found(self, client, auth_headers: dict):
        """Test updating non-existent entry."""
        response = client.put(
            "/api/v1/entries/nonexistent-id",
            headers=auth_headers,
            json={"completed": True},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteEntry:
    """Tests for DELETE /api/v1/entries/{entry_id} endpoint."""

    def test_delete_entry_success(
        self,
        client,
        test_entry: DailyEntry,
        auth_headers: dict,
        db_session: Session,
    ):
        """Test successfully deleting an entry."""
        response = client.delete(
            f"/api/v1/entries/{test_entry.id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify entry was deleted
        deleted_entry = (
            db_session.query(DailyEntry)
            .filter(DailyEntry.id == test_entry.id)
            .first()
        )
        assert deleted_entry is None

    def test_delete_entry_not_found(self, client, auth_headers: dict):
        """Test deleting non-existent entry."""
        response = client.delete(
            "/api/v1/entries/nonexistent-id",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDateNormalization:
    """Tests for date normalization functionality."""

    def test_date_normalized_to_midnight(
        self,
        client,
        test_binary_habit: Habit,
        auth_headers: dict,
        db_session: Session,
    ):
        """Test that entry dates are normalized to midnight UTC."""
        # Create entry with specific time (use today to avoid retroactive logging restrictions)
        entry_date = datetime.utcnow().replace(hour=15, minute=30, second=45, microsecond=0)

        response = client.post(
            f"/api/v1/habits/{test_binary_habit.id}/entries",
            headers=auth_headers,
            json={
                "date": entry_date.isoformat(),
                "completed": True,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify date was normalized
        returned_date = datetime.fromisoformat(data["date"])
        assert returned_date.hour == 0
        assert returned_date.minute == 0
        assert returned_date.second == 0
        assert returned_date.microsecond == 0

    def test_date_with_timezone_normalized(
        self,
        client,
        test_binary_habit: Habit,
        auth_headers: dict,
        db_session: Session,
    ):
        """Test that timezone-aware dates are normalized correctly."""
        # Create entry with timezone-aware datetime (use today to avoid retroactive logging restrictions)
        entry_date = datetime.now(timezone.utc).replace(hour=15, minute=30, second=45, microsecond=0)

        response = client.post(
            f"/api/v1/habits/{test_binary_habit.id}/entries",
            headers=auth_headers,
            json={
                "date": entry_date.isoformat(),
                "completed": True,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify date was normalized and timezone was removed
        returned_date = datetime.fromisoformat(data["date"])
        assert returned_date.hour == 0
        assert returned_date.minute == 0
        assert returned_date.second == 0
        assert returned_date.microsecond == 0
        assert returned_date.tzinfo is None
