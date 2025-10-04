"""Tests for Google OAuth utilities."""

from unittest.mock import AsyncMock, patch, Mock

import pytest
from fastapi import HTTPException, status
import httpx


class TestExchangeCodeForToken:
    """Tests for exchange_code_for_token function."""

    @pytest.mark.asyncio
    async def test_exchange_code_success(self):
        """Test successful authorization code exchange."""
        from app.core.oauth import exchange_code_for_token

        # Mock the httpx client and response
        with patch("app.core.oauth.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json = Mock(return_value={
                "access_token": "ya29.test_access_token",
                "token_type": "Bearer",
                "expires_in": 3599,
            })

            mock_client.__aenter__.return_value = mock_client
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            result = await exchange_code_for_token("test_code", "http://localhost:5173/callback")

            assert result["access_token"] == "ya29.test_access_token"
            assert result["token_type"] == "Bearer"

    @pytest.mark.asyncio
    @patch("app.core.oauth.httpx.AsyncClient")
    async def test_exchange_code_failure(self, mock_client_class):
        """Test failed authorization code exchange."""
        from app.core.oauth import exchange_code_for_token

        # Mock failed response
        mock_response = AsyncMock()
        mock_response.status_code = 400
        mock_response.text = '{"error": "invalid_grant", "error_description": "Bad Request"}'

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        with pytest.raises(HTTPException) as exc_info:
            await exchange_code_for_token("invalid_code", "http://localhost:5173/callback")

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Failed to exchange authorization code for token" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("app.core.oauth.httpx.AsyncClient")
    async def test_exchange_code_failure_401(self, mock_client_class):
        """Test authorization code exchange with 401 response."""
        from app.core.oauth import exchange_code_for_token

        # Mock unauthorized response
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.text = '{"error": "unauthorized_client"}'

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        with pytest.raises(HTTPException) as exc_info:
            await exchange_code_for_token("invalid_code", "http://localhost:5173/callback")

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


class TestGetGoogleUserInfo:
    """Tests for get_google_user_info function."""

    @pytest.mark.asyncio
    async def test_get_user_info_success(self):
        """Test successful user info retrieval."""
        from app.core.oauth import get_google_user_info

        # Mock the httpx client and response
        with patch("app.core.oauth.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json = Mock(return_value={
                "id": "123456789",
                "email": "user@example.com",
                "name": "Test User",
                "picture": "https://example.com/pic.jpg",
            })

            mock_client.__aenter__.return_value = mock_client
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            result = await get_google_user_info("test_access_token")

            assert result["id"] == "123456789"
            assert result["email"] == "user@example.com"
            assert result["name"] == "Test User"

    @pytest.mark.asyncio
    @patch("app.core.oauth.httpx.AsyncClient")
    async def test_get_user_info_failure(self, mock_client_class):
        """Test failed user info retrieval."""
        from app.core.oauth import get_google_user_info

        # Mock failed response
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.text = '{"error": "invalid_token"}'

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        with pytest.raises(HTTPException) as exc_info:
            await get_google_user_info("invalid_token")

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Failed to get user info from Google" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("app.core.oauth.httpx.AsyncClient")
    async def test_get_user_info_failure_403(self, mock_client_class):
        """Test user info retrieval with 403 response."""
        from app.core.oauth import get_google_user_info

        # Mock forbidden response
        mock_response = AsyncMock()
        mock_response.status_code = 403
        mock_response.text = '{"error": "access_denied"}'

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        with pytest.raises(HTTPException) as exc_info:
            await get_google_user_info("restricted_token")

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Failed to get user info from Google" in exc_info.value.detail
