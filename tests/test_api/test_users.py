"""Tests for user API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User


class TestGetUserProfile:
    """Tests for GET /api/v1/users/profile endpoint."""

    def test_get_user_profile_success(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test successful retrieval of user profile."""
        response = client.get("/api/v1/users/profile", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name
        assert data["picture"] == test_user.picture

    def test_get_user_profile_unauthorized(self, client: TestClient):
        """Test getting profile without authentication."""
        response = client.get("/api/v1/users/profile")
        assert response.status_code == 403


class TestUpdateUserProfile:
    """Tests for PUT /api/v1/users/profile endpoint."""

    def test_update_user_profile_success(
        self, client: TestClient, test_user: User, auth_headers: dict, db_session: Session
    ):
        """Test successful update of user profile."""
        new_name = "Updated Name"
        response = client.put(
            f"/api/v1/users/profile?name={new_name}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == new_name
        assert data["id"] == test_user.id

        # Verify the change was persisted in database
        db_session.refresh(test_user)
        assert test_user.name == new_name

    def test_update_user_profile_unauthorized(self, client: TestClient):
        """Test updating profile without authentication."""
        response = client.put("/api/v1/users/profile?name=New Name")
        assert response.status_code == 403
