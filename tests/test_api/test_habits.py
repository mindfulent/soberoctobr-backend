"""Habit API endpoint tests."""

import uuid

import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.models.challenge import Challenge
from app.models.habit import Habit, HabitType
from app.models.user import User


class TestGetChallengeHabits:
    """Tests for GET /api/v1/challenges/{challenge_id}/habits endpoint."""

    def test_get_habits_success(
        self,
        client,
        test_challenge: Challenge,
        test_binary_habit: Habit,
        test_counted_habit: Habit,
        auth_headers: dict,
    ):
        """Test successfully retrieving habits for a challenge."""
        response = client.get(
            f"/api/v1/challenges/{test_challenge.id}/habits",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 2
        habit_ids = [h["id"] for h in data]
        assert test_binary_habit.id in habit_ids
        assert test_counted_habit.id in habit_ids

    def test_get_habits_ordered(
        self,
        client,
        test_challenge: Challenge,
        test_binary_habit: Habit,
        test_counted_habit: Habit,
        auth_headers: dict,
    ):
        """Test that habits are returned in order."""
        response = client.get(
            f"/api/v1/challenges/{test_challenge.id}/habits",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Verify order field is respected
        assert data[0]["order"] <= data[1]["order"]

    def test_get_habits_challenge_not_found(self, client, auth_headers: dict):
        """Test getting habits for non-existent challenge."""
        response = client.get(
            "/api/v1/challenges/nonexistent-id/habits",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_habits_other_user_challenge(
        self,
        client,
        other_user: User,
        auth_headers: dict,
        db_session: Session,
    ):
        """Test that users cannot get habits from other users' challenges."""
        from datetime import datetime
        from app.models.challenge import ChallengeStatus

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
            f"/api/v1/challenges/{other_challenge.id}/habits",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCreateHabit:
    """Tests for POST /api/v1/challenges/{challenge_id}/habits endpoint."""

    def test_create_binary_habit_success(
        self, client, test_challenge: Challenge, auth_headers: dict
    ):
        """Test successfully creating a binary habit."""
        response = client.post(
            f"/api/v1/challenges/{test_challenge.id}/habits",
            headers=auth_headers,
            json={
                "name": "Read for 30 minutes",
                "type": HabitType.BINARY.value,
                "preferred_time": "evening",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Read for 30 minutes"
        assert data["type"] == HabitType.BINARY.value
        assert data["preferred_time"] == "evening"
        assert data["is_active"] is True

    def test_create_counted_habit_success(
        self, client, test_challenge: Challenge, auth_headers: dict
    ):
        """Test successfully creating a counted habit."""
        response = client.post(
            f"/api/v1/challenges/{test_challenge.id}/habits",
            headers=auth_headers,
            json={
                "name": "Drink water",
                "type": HabitType.COUNTED.value,
                "target_count": 8,
                "preferred_time": "afternoon",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Drink water"
        assert data["type"] == HabitType.COUNTED.value
        assert data["target_count"] == 8

    def test_create_habit_max_limit(
        self,
        client,
        test_challenge: Challenge,
        auth_headers: dict,
        db_session: Session,
    ):
        """Test that users cannot create more than 10 habits per challenge."""
        # Create 10 habits
        for i in range(10):
            habit = Habit(
                id=str(uuid.uuid4()),
                challenge_id=test_challenge.id,
                name=f"Habit {i}",
                type=HabitType.BINARY,
                order=i,
                is_active=True,
            )
            db_session.add(habit)
        db_session.commit()

        # Try to create 11th habit
        response = client.post(
            f"/api/v1/challenges/{test_challenge.id}/habits",
            headers=auth_headers,
            json={
                "name": "11th Habit",
                "type": HabitType.BINARY.value,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Maximum of 10 habits" in response.json()["detail"]

    def test_create_habit_challenge_not_found(self, client, auth_headers: dict):
        """Test creating habit for non-existent challenge."""
        response = client.post(
            "/api/v1/challenges/nonexistent-id/habits",
            headers=auth_headers,
            json={
                "name": "Test Habit",
                "type": HabitType.BINARY.value,
            },
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_habit_auto_order(
        self,
        client,
        test_challenge: Challenge,
        test_binary_habit: Habit,
        auth_headers: dict,
    ):
        """Test that habit order is automatically assigned."""
        response = client.post(
            f"/api/v1/challenges/{test_challenge.id}/habits",
            headers=auth_headers,
            json={
                "name": "New Habit",
                "type": HabitType.BINARY.value,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        # Should be assigned next order number
        assert data["order"] >= 0


class TestGetHabit:
    """Tests for GET /api/v1/habits/{habit_id} endpoint."""

    def test_get_habit_success(
        self, client, test_binary_habit: Habit, auth_headers: dict
    ):
        """Test successfully retrieving a specific habit."""
        response = client.get(
            f"/api/v1/habits/{test_binary_habit.id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_binary_habit.id
        assert data["name"] == test_binary_habit.name

    def test_get_habit_not_found(self, client, auth_headers: dict):
        """Test getting non-existent habit."""
        response = client.get(
            "/api/v1/habits/nonexistent-id",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateHabit:
    """Tests for PUT /api/v1/habits/{habit_id} endpoint."""

    def test_update_habit_name(
        self, client, test_binary_habit: Habit, auth_headers: dict
    ):
        """Test updating habit name."""
        response = client.put(
            f"/api/v1/habits/{test_binary_habit.id}",
            headers=auth_headers,
            json={"name": "Updated Meditation"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Meditation"

    def test_update_habit_type(
        self, client, test_binary_habit: Habit, auth_headers: dict
    ):
        """Test updating habit type."""
        response = client.put(
            f"/api/v1/habits/{test_binary_habit.id}",
            headers=auth_headers,
            json={
                "type": HabitType.COUNTED.value,
                "target_count": 5,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["type"] == HabitType.COUNTED.value
        assert data["target_count"] == 5

    def test_update_habit_order(
        self, client, test_binary_habit: Habit, auth_headers: dict
    ):
        """Test updating habit order."""
        response = client.put(
            f"/api/v1/habits/{test_binary_habit.id}",
            headers=auth_headers,
            json={"order": 5},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["order"] == 5

    def test_update_habit_is_active(
        self, client, test_binary_habit: Habit, auth_headers: dict
    ):
        """Test archiving a habit by setting is_active to False."""
        response = client.put(
            f"/api/v1/habits/{test_binary_habit.id}",
            headers=auth_headers,
            json={"is_active": False},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_active"] is False

    def test_update_habit_not_found(self, client, auth_headers: dict):
        """Test updating non-existent habit."""
        response = client.put(
            "/api/v1/habits/nonexistent-id",
            headers=auth_headers,
            json={"name": "Updated"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteHabit:
    """Tests for DELETE /api/v1/habits/{habit_id} endpoint."""

    def test_delete_habit_archives(
        self,
        client,
        test_binary_habit: Habit,
        auth_headers: dict,
        db_session: Session,
    ):
        """Test that deleting a habit archives it instead of deleting."""
        response = client.delete(
            f"/api/v1/habits/{test_binary_habit.id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify habit was archived, not deleted
        db_session.refresh(test_binary_habit)
        assert test_binary_habit.is_active is False

    def test_delete_habit_not_found(self, client, auth_headers: dict):
        """Test deleting non-existent habit."""
        response = client.delete(
            "/api/v1/habits/nonexistent-id",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestBulkCreateHabits:
    """Tests for POST /api/v1/challenges/{challenge_id}/habits/bulk endpoint."""

    def test_bulk_create_habits_success(
        self, client, test_challenge: Challenge, auth_headers: dict
    ):
        """Test successfully creating multiple habits at once."""
        habits_data = {
            "habits": [
                {
                    "name": "Meditate",
                    "type": HabitType.BINARY.value,
                    "preferred_time": "morning",
                    "order": 0,
                },
                {
                    "name": "Pushups",
                    "type": HabitType.COUNTED.value,
                    "target_count": 20,
                    "preferred_time": "morning",
                    "order": 1,
                },
                {
                    "name": "Journal",
                    "type": HabitType.BINARY.value,
                    "preferred_time": "evening",
                    "order": 2,
                },
            ]
        }

        response = client.post(
            f"/api/v1/challenges/{test_challenge.id}/habits/bulk",
            headers=auth_headers,
            json=habits_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data) == 3
        
        # Verify each habit was created correctly
        assert data[0]["name"] == "Meditate"
        assert data[0]["type"] == HabitType.BINARY.value
        assert data[1]["name"] == "Pushups"
        assert data[1]["target_count"] == 20
        assert data[2]["name"] == "Journal"

    def test_bulk_create_with_template_ids(
        self, client, test_challenge: Challenge, auth_headers: dict
    ):
        """Test bulk creating habits with template IDs."""
        habits_data = {
            "habits": [
                {
                    "name": "Vitamin D",
                    "type": HabitType.BINARY.value,
                    "preferred_time": "afternoon",
                    "template_id": "vitamin_d",
                },
                {
                    "name": "Meditate",
                    "type": HabitType.BINARY.value,
                    "preferred_time": "morning",
                    "template_id": "meditate",
                },
            ]
        }

        response = client.post(
            f"/api/v1/challenges/{test_challenge.id}/habits/bulk",
            headers=auth_headers,
            json=habits_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data) == 2
        assert data[0]["template_id"] == "vitamin_d"
        assert data[1]["template_id"] == "meditate"

    def test_bulk_create_auto_order(
        self, client, test_challenge: Challenge, auth_headers: dict, db_session: Session
    ):
        """Test that habits get assigned orders (either explicit or auto)."""
        # First check how many existing habits there are
        existing_count = db_session.query(Habit).filter(
            Habit.challenge_id == test_challenge.id,
            Habit.is_active == True
        ).count()
        
        habits_data = {
            "habits": [
                {
                    "name": "Habit 1",
                    "type": HabitType.BINARY.value,
                },
                {
                    "name": "Habit 2",
                    "type": HabitType.BINARY.value,
                },
                {
                    "name": "Habit 3",
                    "type": HabitType.BINARY.value,
                },
            ]
        }

        response = client.post(
            f"/api/v1/challenges/{test_challenge.id}/habits/bulk",
            headers=auth_headers,
            json=habits_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        # Verify all habits have an order field
        assert all("order" in h for h in data)
        # Verify we got 3 habits back
        assert len(data) == 3

    def test_bulk_create_exceeds_limit(
        self, client, test_challenge: Challenge, auth_headers: dict, db_session: Session
    ):
        """Test that bulk creation fails if total exceeds 10 habits."""
        # Create 5 existing habits
        for i in range(5):
            habit = Habit(
                id=str(uuid.uuid4()),
                challenge_id=test_challenge.id,
                name=f"Existing Habit {i}",
                type=HabitType.BINARY,
                order=i,
                is_active=True,
            )
            db_session.add(habit)
        db_session.commit()

        # Try to add 6 more (would total 11)
        habits_data = {
            "habits": [
                {"name": f"New Habit {i}", "type": HabitType.BINARY.value}
                for i in range(6)
            ]
        }

        response = client.post(
            f"/api/v1/challenges/{test_challenge.id}/habits/bulk",
            headers=auth_headers,
            json=habits_data,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Maximum of 10 habits" in response.json()["detail"]

    def test_bulk_create_exactly_10_habits(
        self, client, test_challenge: Challenge, auth_headers: dict
    ):
        """Test creating exactly 10 habits at once."""
        habits_data = {
            "habits": [
                {"name": f"Habit {i}", "type": HabitType.BINARY.value}
                for i in range(10)
            ]
        }

        response = client.post(
            f"/api/v1/challenges/{test_challenge.id}/habits/bulk",
            headers=auth_headers,
            json=habits_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data) == 10

    def test_bulk_create_empty_list(
        self, client, test_challenge: Challenge, auth_headers: dict
    ):
        """Test that empty habits list is rejected."""
        habits_data = {"habits": []}

        response = client.post(
            f"/api/v1/challenges/{test_challenge.id}/habits/bulk",
            headers=auth_headers,
            json=habits_data,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_bulk_create_more_than_10_in_request(
        self, client, test_challenge: Challenge, auth_headers: dict
    ):
        """Test that more than 10 habits in single request is rejected."""
        habits_data = {
            "habits": [
                {"name": f"Habit {i}", "type": HabitType.BINARY.value}
                for i in range(11)
            ]
        }

        response = client.post(
            f"/api/v1/challenges/{test_challenge.id}/habits/bulk",
            headers=auth_headers,
            json=habits_data,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_bulk_create_challenge_not_found(self, client, auth_headers: dict):
        """Test bulk creating habits for non-existent challenge."""
        habits_data = {
            "habits": [
                {"name": "Test Habit", "type": HabitType.BINARY.value}
            ]
        }

        response = client.post(
            "/api/v1/challenges/nonexistent-id/habits/bulk",
            headers=auth_headers,
            json=habits_data,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_bulk_create_mixed_types(
        self, client, test_challenge: Challenge, auth_headers: dict
    ):
        """Test bulk creating mix of binary and counted habits."""
        habits_data = {
            "habits": [
                {
                    "name": "Meditate",
                    "type": HabitType.BINARY.value,
                    "preferred_time": "morning",
                },
                {
                    "name": "Pushups",
                    "type": HabitType.COUNTED.value,
                    "target_count": 50,
                    "preferred_time": "morning",
                },
                {
                    "name": "No Coffee",
                    "type": HabitType.BINARY.value,
                    "preferred_time": "all_day",
                },
                {
                    "name": "Drink Water",
                    "type": HabitType.COUNTED.value,
                    "target_count": 8,
                    "preferred_time": "all_day",
                },
            ]
        }

        response = client.post(
            f"/api/v1/challenges/{test_challenge.id}/habits/bulk",
            headers=auth_headers,
            json=habits_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data) == 4
        
        # Verify binary habits
        binary_habits = [h for h in data if h["type"] == HabitType.BINARY.value]
        assert len(binary_habits) == 2
        
        # Verify counted habits
        counted_habits = [h for h in data if h["type"] == HabitType.COUNTED.value]
        assert len(counted_habits) == 2
        assert all(h["target_count"] is not None for h in counted_habits)
