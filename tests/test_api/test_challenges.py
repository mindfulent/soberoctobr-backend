"""Challenge API endpoint tests."""

from datetime import datetime, timedelta

import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.models.challenge import Challenge, ChallengeStatus
from app.models.user import User


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
        assert datetime.fromisoformat(data["start_date"]).date() == start_date.date()

        # Verify end date is 30 days after start
        end_date = datetime.fromisoformat(data["end_date"])
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
