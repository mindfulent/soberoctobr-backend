"""Tests for main application endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
from sqlalchemy import text


class TestRootEndpoint:
    """Tests for root / endpoint."""

    def test_root_returns_welcome_message(self, client: TestClient):
        """Test root endpoint returns welcome message."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Welcome to the Sober October API!"}


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check_returns_healthy_status(self, client: TestClient):
        """Test health endpoint returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"
        assert "environment" in data
        assert "port" in data


class TestDetailedHealthEndpoint:
    """Tests for /health/detailed endpoint."""

    def test_detailed_health_check_with_database_success(self, client: TestClient):
        """Test detailed health check with successful database connection."""
        response = client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"
        assert "environment" in data
        assert "port" in data
        # Database check should succeed with test database
        assert data["database"] == "connected"

    def test_detailed_health_check_with_database_failure(self, client: TestClient):
        """Test detailed health check when database connection fails."""
        # Mock the engine.connect() to raise an exception
        from app.core import database

        original_engine = database.engine
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = Exception("Database connection failed")

        try:
            database.engine = mock_engine
            response = client.get("/health/detailed")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["database"] == "disconnected"
            assert "database_error" in data
            assert "Database connection failed" in data["database_error"]
        finally:
            database.engine = original_engine


class TestPingEndpoint:
    """Tests for /ping endpoint."""

    def test_ping_returns_pong(self, client: TestClient):
        """Test ping endpoint returns pong response."""
        response = client.get("/ping")
        assert response.status_code == 200
        assert response.json() == {"ping": "pong"}


class TestMainExecution:
    """Tests for __main__ execution block."""

    def test_main_execution_starts_uvicorn(self):
        """Test that running main.py as script starts uvicorn."""
        with patch('uvicorn.run') as mock_run:
            # Import main module and simulate __name__ == "__main__"
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "__main__",
                "/Users/jonpappas/Projects/soberoctobr/soberoctobr-backend/app/main.py"
            )
            module = importlib.util.module_from_spec(spec)

            # Mock __name__ to be "__main__"
            with patch.object(sys, 'modules', {**sys.modules, '__main__': module}):
                try:
                    spec.loader.exec_module(module)
                    # The uvicorn.run should have been called
                    mock_run.assert_called_once()
                    call_args = mock_run.call_args
                    assert call_args[1]["host"] == "0.0.0.0"
                    assert call_args[1]["port"] == 8000
                except SystemExit:
                    # It's okay if the script tries to exit
                    pass
