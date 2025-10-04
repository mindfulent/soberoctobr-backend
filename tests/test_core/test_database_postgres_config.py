"""Tests for PostgreSQL database engine configuration.

These tests must be run in a separate process to control the import order
and settings before the database module is imported.
"""

import os
import sys
import subprocess
import pytest


class TestPostgreSQLConfiguration:
    """Tests for PostgreSQL-specific configuration."""

    def test_postgresql_production_config_in_subprocess(self):
        """Test PostgreSQL production configuration by running in subprocess."""
        # Create a test script that will run in a subprocess
        test_script = """
import os
os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/testdb"
os.environ["ENVIRONMENT"] = "production"
os.environ["DEBUG"] = "False"
os.environ["SECRET_KEY"] = "test-secret"

from unittest.mock import patch, MagicMock

# Mock create_engine at the SQLAlchemy level before importing database module
with patch('sqlalchemy.create_engine') as mock_create_engine:
    mock_engine = MagicMock()
    mock_create_engine.return_value = mock_engine

    # Import the database module (this triggers engine creation)
    import app.core.database

    # Verify create_engine was called with production settings
    assert mock_create_engine.call_count >= 1
    call_args = mock_create_engine.call_args

    # The first arg should be the database URL
    assert call_args[0][0] == "postgresql://user:pass@localhost:5432/testdb"

    # Check production pool settings
    assert call_args[1]['pool_size'] == 1
    assert call_args[1]['max_overflow'] == 2
    assert call_args[1]['pool_pre_ping'] == True

    print("PASS: Production PostgreSQL configuration validated")
"""

        # Run the test script in a subprocess
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
            cwd="/Users/jonpappas/Projects/soberoctobr/soberoctobr-backend"
        )

        # Check if the test passed
        assert "PASS: Production PostgreSQL configuration validated" in result.stdout, \
            f"Test failed. STDOUT: {result.stdout}\nSTDERR: {result.stderr}\nReturn code: {result.returncode}"

    def test_postgresql_development_config_in_subprocess(self):
        """Test PostgreSQL development configuration by running in subprocess."""
        # Create a test script that will run in a subprocess
        test_script = """
import os
os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/testdb"
os.environ["ENVIRONMENT"] = "development"
os.environ["DEBUG"] = "True"
os.environ["SECRET_KEY"] = "test-secret"

from unittest.mock import patch, MagicMock

# Mock create_engine at the SQLAlchemy level before importing database module
with patch('sqlalchemy.create_engine') as mock_create_engine:
    mock_engine = MagicMock()
    mock_create_engine.return_value = mock_engine

    # Import the database module (this triggers engine creation)
    import app.core.database

    # Verify create_engine was called with development settings
    assert mock_create_engine.call_count >= 1
    call_args = mock_create_engine.call_args

    # The first arg should be the database URL
    assert call_args[0][0] == "postgresql://user:pass@localhost:5432/testdb"

    # Check development pool settings
    assert call_args[1]['pool_size'] == 5
    assert call_args[1]['max_overflow'] == 10
    assert call_args[1]['pool_pre_ping'] == True

    print("PASS: Development PostgreSQL configuration validated")
"""

        # Run the test script in a subprocess
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
            cwd="/Users/jonpappas/Projects/soberoctobr/soberoctobr-backend"
        )

        # Check if the test passed
        assert "PASS: Development PostgreSQL configuration validated" in result.stdout, \
            f"Test failed. STDOUT: {result.stdout}\nSTDERR: {result.stderr}\nReturn code: {result.returncode}"
