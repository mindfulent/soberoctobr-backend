"""Authentication API endpoint tests."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.models.user import User


class TestGoogleAuth:
    """Tests for Google OAuth authentication endpoint."""

    @patch("app.api.auth.exchange_code_for_token")
    @patch("app.api.auth.get_google_user_info")
    def test_google_auth_new_user(
        self,
        mock_get_user_info: AsyncMock,
        mock_exchange_token: AsyncMock,
        client,
        db_session: Session,
    ):
        """Test successful authentication with new user creation."""
        # Mock Google OAuth responses
        mock_exchange_token.return_value = {"access_token": "google_access_token"}
        mock_get_user_info.return_value = {
            "id": "google_user_123",
            "email": "newuser@example.com",
            "name": "New User",
            "picture": "https://example.com/pic.jpg",
        }

        response = client.post(
            "/api/v1/auth/google",
            json={"code": "auth_code", "redirect_uri": "http://localhost:5173/callback"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # Verify user was created in database
        user = db_session.query(User).filter(User.email == "newuser@example.com").first()
        assert user is not None
        assert user.name == "New User"
        assert user.google_id == "google_user_123"

    @patch("app.api.auth.exchange_code_for_token")
    @patch("app.api.auth.get_google_user_info")
    def test_google_auth_existing_user(
        self,
        mock_get_user_info: AsyncMock,
        mock_exchange_token: AsyncMock,
        client,
        test_user: User,
        db_session: Session,
    ):
        """Test successful authentication with existing user."""
        # Mock Google OAuth responses
        mock_exchange_token.return_value = {"access_token": "google_access_token"}
        mock_get_user_info.return_value = {
            "id": test_user.google_id,
            "email": test_user.email,
            "name": test_user.name,
            "picture": test_user.picture,
        }

        initial_user_count = db_session.query(User).count()

        response = client.post(
            "/api/v1/auth/google",
            json={"code": "auth_code", "redirect_uri": "http://localhost:5173/callback"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # Verify no new user was created
        assert db_session.query(User).count() == initial_user_count

    @patch("app.api.auth.exchange_code_for_token")
    def test_google_auth_invalid_code(
        self,
        mock_exchange_token: AsyncMock,
        client,
    ):
        """Test authentication with invalid authorization code."""
        from fastapi import HTTPException

        # Mock failed token exchange
        mock_exchange_token.side_effect = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange authorization code for token",
        )

        response = client.post(
            "/api/v1/auth/google",
            json={"code": "invalid_code", "redirect_uri": "http://localhost:5173/callback"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestGetCurrentUser:
    """Tests for getting current user information."""

    def test_get_current_user_success(self, client, test_user: User, auth_headers: dict):
        """Test successfully retrieving current user info."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name

    def test_get_current_user_no_token(self, client):
        """Test getting current user without authentication token."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_expired_token(self, client, test_user: User):
        """Test getting current user with expired token."""
        from datetime import timedelta
        from app.core.security import create_access_token

        # Create an expired token (negative expiration)
        expired_token = create_access_token(
            data={"sub": test_user.id},
            expires_delta=timedelta(minutes=-30),
        )

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestLogout:
    """Tests for logout endpoint."""

    def test_logout_success(self, client):
        """Test logout endpoint returns success message."""
        response = client.post("/api/v1/auth/logout")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert data["message"] == "Successfully logged out"


class TestGoogleCallback:
    """Tests for Google OAuth callback endpoint."""

    @patch("app.api.auth.exchange_code_for_token")
    @patch("app.api.auth.get_google_user_info")
    def test_google_callback_new_user(
        self,
        mock_get_user_info: AsyncMock,
        mock_exchange_token: AsyncMock,
        client,
        db_session: Session,
    ):
        """Test successful callback with new user creation."""
        # Mock Google OAuth responses
        mock_exchange_token.return_value = {"access_token": "google_access_token"}
        mock_get_user_info.return_value = {
            "id": "google_user_456",
            "email": "callback@example.com",
            "name": "Callback User",
            "picture": "https://example.com/callback.jpg",
        }

        response = client.get("/api/v1/auth/google/callback?code=test_code", follow_redirects=False)

        # Should redirect to frontend
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert "location" in response.headers
        assert "token=" in response.headers["location"]
        assert "/auth/callback" in response.headers["location"]

        # Verify user was created in database
        user = db_session.query(User).filter(User.email == "callback@example.com").first()
        assert user is not None
        assert user.name == "Callback User"
        assert user.google_id == "google_user_456"

    @patch("app.api.auth.exchange_code_for_token")
    @patch("app.api.auth.get_google_user_info")
    def test_google_callback_existing_user(
        self,
        mock_get_user_info: AsyncMock,
        mock_exchange_token: AsyncMock,
        client,
        test_user: User,
        db_session: Session,
    ):
        """Test successful callback with existing user."""
        # Mock Google OAuth responses
        mock_exchange_token.return_value = {"access_token": "google_access_token"}
        mock_get_user_info.return_value = {
            "id": test_user.google_id,
            "email": test_user.email,
            "name": test_user.name,
            "picture": test_user.picture,
        }

        initial_user_count = db_session.query(User).count()

        response = client.get("/api/v1/auth/google/callback?code=test_code", follow_redirects=False)

        # Should redirect to frontend
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert "token=" in response.headers["location"]

        # Verify no new user was created
        assert db_session.query(User).count() == initial_user_count

    @patch("app.api.auth.exchange_code_for_token")
    @patch("app.api.auth.get_google_user_info")
    def test_google_callback_with_state(
        self,
        mock_get_user_info: AsyncMock,
        mock_exchange_token: AsyncMock,
        client,
        test_user: User,
    ):
        """Test callback with custom state parameter."""
        # Mock Google OAuth responses
        mock_exchange_token.return_value = {"access_token": "google_access_token"}
        mock_get_user_info.return_value = {
            "id": test_user.google_id,
            "email": test_user.email,
            "name": test_user.name,
            "picture": test_user.picture,
        }

        custom_frontend_url = "http://localhost:3000"
        response = client.get(
            f"/api/v1/auth/google/callback?code=test_code&state={custom_frontend_url}",
            follow_redirects=False
        )

        # Should redirect to custom frontend URL
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert custom_frontend_url in response.headers["location"]

    @patch("app.api.auth.exchange_code_for_token")
    @patch("app.api.auth.get_google_user_info")
    def test_google_callback_with_production_state(
        self,
        mock_get_user_info: AsyncMock,
        mock_exchange_token: AsyncMock,
        client,
        test_user: User,
    ):
        """Test callback with production domain in state."""
        # Mock Google OAuth responses
        mock_exchange_token.return_value = {"access_token": "google_access_token"}
        mock_get_user_info.return_value = {
            "id": test_user.google_id,
            "email": test_user.email,
            "name": test_user.name,
            "picture": test_user.picture,
        }

        production_url = "https://soberoctobr.com"
        response = client.get(
            f"/api/v1/auth/google/callback?code=test_code&state={production_url}",
            follow_redirects=False
        )

        # Should redirect to production URL
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert production_url in response.headers["location"]

    @patch("app.api.auth.exchange_code_for_token")
    @patch("app.api.auth.get_google_user_info")
    def test_google_callback_with_unsafe_state(
        self,
        mock_get_user_info: AsyncMock,
        mock_exchange_token: AsyncMock,
        client,
        test_user: User,
    ):
        """Test callback with unsafe URL in state parameter falls back to configured URL."""
        # Mock Google OAuth responses
        mock_exchange_token.return_value = {"access_token": "google_access_token"}
        mock_get_user_info.return_value = {
            "id": test_user.google_id,
            "email": test_user.email,
            "name": test_user.name,
            "picture": test_user.picture,
        }

        unsafe_url = "https://malicious-site.com"
        response = client.get(
            f"/api/v1/auth/google/callback?code=test_code&state={unsafe_url}",
            follow_redirects=False
        )

        # Should redirect to configured FRONTEND_URL, not the unsafe URL
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert unsafe_url not in response.headers["location"]
        # Should use the configured FRONTEND_URL from settings
        from app.config import settings
        assert settings.FRONTEND_URL in response.headers["location"]

    @patch("app.api.auth.exchange_code_for_token")
    def test_google_callback_http_exception(
        self,
        mock_exchange_token: AsyncMock,
        client,
    ):
        """Test callback error handling when HTTPException is raised."""
        from fastapi import HTTPException

        # Mock failed token exchange
        mock_exchange_token.side_effect = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange authorization code for token",
        )

        response = client.get("/api/v1/auth/google/callback?code=invalid_code", follow_redirects=False)

        # Should redirect to frontend with error
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert "error=auth_failed" in response.headers["location"]
        assert "detail=http_exception" in response.headers["location"]

    @patch("app.api.auth.exchange_code_for_token")
    def test_google_callback_http_exception_with_safe_state(
        self,
        mock_exchange_token: AsyncMock,
        client,
    ):
        """Test callback error handling with safe state URL when HTTPException is raised."""
        from fastapi import HTTPException

        # Mock failed token exchange
        mock_exchange_token.side_effect = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange authorization code for token",
        )

        safe_state = "http://localhost:3000"
        response = client.get(
            f"/api/v1/auth/google/callback?code=invalid_code&state={safe_state}",
            follow_redirects=False
        )

        # Should redirect to safe state URL with error
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert safe_state in response.headers["location"]
        assert "error=auth_failed" in response.headers["location"]

    @patch("app.api.auth.exchange_code_for_token")
    def test_google_callback_general_exception(
        self,
        mock_exchange_token: AsyncMock,
        client,
    ):
        """Test callback error handling when general Exception is raised."""
        # Mock unexpected exception
        mock_exchange_token.side_effect = RuntimeError("Unexpected error")

        response = client.get("/api/v1/auth/google/callback?code=test_code", follow_redirects=False)

        # Should redirect to frontend with error
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert "error=auth_failed" in response.headers["location"]
        assert "detail=exception" in response.headers["location"]

    @patch("app.api.auth.exchange_code_for_token")
    def test_google_callback_general_exception_with_unsafe_state(
        self,
        mock_exchange_token: AsyncMock,
        client,
    ):
        """Test callback error handling with unsafe state when general Exception is raised."""
        # Mock unexpected exception
        mock_exchange_token.side_effect = RuntimeError("Unexpected error")

        unsafe_state = "https://malicious.com"
        response = client.get(
            f"/api/v1/auth/google/callback?code=test_code&state={unsafe_state}",
            follow_redirects=False
        )

        # Should redirect to configured FRONTEND_URL (not unsafe state) with error
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert unsafe_state not in response.headers["location"]
        from app.config import settings
        assert settings.FRONTEND_URL in response.headers["location"]
        assert "error=auth_failed" in response.headers["location"]
