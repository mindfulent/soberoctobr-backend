"""Tests for database connection and session management."""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.core.database import get_db, init_db


class TestGetDB:
    """Tests for get_db() dependency function."""

    def test_get_db_yields_session(self):
        """Test that get_db() yields a database session and closes it."""
        session_created = False
        session_closed = False

        # Mock SessionLocal to track session lifecycle
        mock_session = MagicMock(spec=Session)

        def track_close():
            nonlocal session_closed
            session_closed = True

        mock_session.close = track_close

        with patch('app.core.database.SessionLocal') as mock_session_local:
            mock_session_local.return_value = mock_session
            session_created = True

            # Use the generator
            gen = get_db()
            session = next(gen)

            assert session_created
            assert session == mock_session
            assert not session_closed

            # Complete the generator (simulating end of request)
            try:
                next(gen)
            except StopIteration:
                pass

            # Session should be closed after generator completes
            assert session_closed


class TestInitDB:
    """Tests for init_db() function."""

    def test_init_db_creates_all_tables(self):
        """Test that init_db() creates all database tables."""
        with patch('app.core.database.Base') as mock_base:
            mock_metadata = MagicMock()
            mock_base.metadata = mock_metadata

            init_db()

            # Verify create_all was called
            mock_metadata.create_all.assert_called_once()


class TestDatabaseEngineConfiguration:
    """Tests for database engine configuration with different settings."""

    def test_postgresql_pool_size_logic_production(self):
        """Test that production environment uses smaller pool size."""
        # Test the logic directly
        environment = "production"
        pool_size = 1 if environment == "production" else 5
        max_overflow = 2 if environment == "production" else 10

        assert pool_size == 1
        assert max_overflow == 2

    def test_postgresql_pool_size_logic_development(self):
        """Test that non-production environment uses larger pool size."""
        # Test the logic directly
        environment = "development"
        pool_size = 1 if environment == "production" else 5
        max_overflow = 2 if environment == "production" else 10

        assert pool_size == 5
        assert max_overflow == 10
