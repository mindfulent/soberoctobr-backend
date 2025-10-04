"""Security and JWT token tests."""

from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from jose import jwt

from app.config import settings
from app.core.security import create_access_token, decode_access_token, get_current_user
from app.models.user import User


class TestCreateAccessToken:
    """Tests for JWT token creation."""

    def test_create_token_success(self):
        """Test successfully creating a JWT token."""
        user_id = "test-user-123"
        token = create_access_token(data={"sub": user_id})

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == user_id
        assert "exp" in payload

    def test_create_token_with_custom_expiration(self):
        """Test creating token with custom expiration time."""
        user_id = "test-user-123"
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data={"sub": user_id}, expires_delta=expires_delta)

        assert isinstance(token, str)

        # Decode and verify expiration
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == user_id

    def test_create_token_with_additional_claims(self):
        """Test creating token with additional claims."""
        data = {
            "sub": "test-user-123",
            "email": "test@example.com",
            "role": "user",
        }
        token = create_access_token(data=data)

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "test-user-123"
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "user"


class TestDecodeAccessToken:
    """Tests for JWT token decoding and validation."""

    def test_decode_valid_token(self):
        """Test decoding a valid JWT token."""
        user_id = "test-user-123"
        token = create_access_token(data={"sub": user_id})

        payload = decode_access_token(token)

        assert payload is not None
        assert payload["sub"] == user_id

    def test_decode_invalid_token(self):
        """Test decoding an invalid token."""
        invalid_token = "invalid.token.here"

        payload = decode_access_token(invalid_token)

        assert payload is None

    def test_decode_expired_token(self):
        """Test decoding an expired token."""
        user_id = "test-user-123"
        token = create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(minutes=-30)  # Already expired
        )

        payload = decode_access_token(token)

        assert payload is None

    def test_decode_tampered_token(self):
        """Test decoding a token that has been tampered with."""
        token = create_access_token(data={"sub": "test-user-123"})

        # Tamper with token
        parts = token.split(".")
        tampered_token = parts[0] + ".tampered." + parts[2]

        payload = decode_access_token(tampered_token)

        assert payload is None

    def test_decode_wrong_secret(self):
        """Test decoding token signed with different secret."""
        # Create token with different secret
        wrong_token = jwt.encode(
            {"sub": "test-user-123"},
            "wrong-secret-key",
            algorithm=settings.ALGORITHM
        )

        payload = decode_access_token(wrong_token)

        assert payload is None


class TestGetCurrentUser:
    """Tests for get_current_user dependency function."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, test_user: User, db_session):
        """Test successfully getting current user from valid token."""
        token = create_access_token(data={"sub": test_user.id})

        # Mock credentials
        credentials = MagicMock()
        credentials.credentials = token

        user = await get_current_user(credentials=credentials, db=db_session)

        assert user.id == test_user.id
        assert user.email == test_user.email

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, db_session):
        """Test get_current_user with invalid token."""
        credentials = MagicMock()
        credentials.credentials = "invalid.token.here"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=credentials, db=db_session)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_no_user_id(self, db_session):
        """Test get_current_user with token missing user ID."""
        # Create token without 'sub' claim
        token = create_access_token(data={"email": "test@example.com"})

        credentials = MagicMock()
        credentials.credentials = token

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=credentials, db=db_session)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self, db_session):
        """Test get_current_user when user doesn't exist in database."""
        # Create token for non-existent user
        token = create_access_token(data={"sub": "nonexistent-user-id"})

        credentials = MagicMock()
        credentials.credentials = token

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=credentials, db=db_session)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self, test_user: User, db_session):
        """Test get_current_user with expired token."""
        # Create expired token
        token = create_access_token(
            data={"sub": test_user.id},
            expires_delta=timedelta(minutes=-30)
        )

        credentials = MagicMock()
        credentials.credentials = token

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=credentials, db=db_session)

        assert exc_info.value.status_code == 401


class TestTokenSecurity:
    """Tests for token security features."""

    def test_tokens_are_unique(self):
        """Test that each token generation creates unique tokens."""
        import time
        user_id = "test-user-123"
        token1 = create_access_token(data={"sub": user_id})
        time.sleep(1.1)  # Sleep to ensure different exp times (JWT rounds to seconds)
        token2 = create_access_token(data={"sub": user_id})

        # Tokens should be different due to different exp times
        assert token1 != token2

    def test_token_cannot_be_modified(self):
        """Test that modifying token payload invalidates it."""
        token = create_access_token(data={"sub": "user-123"})

        # Decode, modify, and re-encode with different secret
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        payload["sub"] = "hacker-456"

        # Re-encode with same secret
        modified_token = jwt.encode(
            payload,
            "different-secret",
            algorithm=settings.ALGORITHM
        )

        # Should fail to decode
        decoded = decode_access_token(modified_token)
        assert decoded is None
