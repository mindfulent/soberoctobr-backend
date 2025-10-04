"""Tests for application configuration settings."""

import json
import os
import sys
import subprocess
import pytest
from pydantic import ValidationError


class TestCORSOriginsParserDirectly:
    """Direct tests for parse_cors_origins validator."""

    def test_parse_cors_origins_with_list(self):
        """Test parse_cors_origins with list input."""
        from app.config import Settings

        # Call the validator directly
        result = Settings.parse_cors_origins(["http://example.com", "http://example2.com"])
        assert result == ["http://example.com", "http://example2.com"]

    def test_parse_cors_origins_with_json_array_string(self):
        """Test parse_cors_origins with JSON array string."""
        from app.config import Settings

        # This should hit lines 147-149 (JSON parsing returning a list)
        result = Settings.parse_cors_origins('["http://example.com", "http://example2.com"]')
        assert isinstance(result, list)
        assert len(result) == 2
        assert "http://example.com" in result
        assert "http://example2.com" in result

    def test_parse_cors_origins_with_json_non_list(self):
        """Test parse_cors_origins with JSON that's not a list."""
        from app.config import Settings

        # JSON parses successfully to a dict, but it's not a list
        # Should fall back to comma-separated parsing
        result = Settings.parse_cors_origins('{"key": "value"}')
        # Since the string has no commas, it becomes a single-item list
        assert isinstance(result, list)
        assert '{"key": "value"}' in result

    def test_parse_cors_origins_with_comma_separated(self):
        """Test parse_cors_origins with comma-separated string."""
        from app.config import Settings

        result = Settings.parse_cors_origins("http://localhost:3000,http://localhost:5173")
        assert isinstance(result, list)
        assert len(result) == 2
        assert "http://localhost:3000" in result
        assert "http://localhost:5173" in result

    def test_parse_cors_origins_with_non_string_non_list(self):
        """Test parse_cors_origins with value that's neither string nor list."""
        from app.config import Settings

        # This should hit line 154 (return v for unexpected types)
        result = Settings.parse_cors_origins(123)
        assert result == 123


class TestDatabaseURLValidatorDirectly:
    """Direct tests for validate_database_url validator."""

    def test_validate_database_url_with_postgresql(self):
        """Test validate_database_url with postgresql:// scheme."""
        from app.config import Settings

        result = Settings.validate_database_url("postgresql://user:pass@localhost:5432/testdb")
        assert result == "postgresql://user:pass@localhost:5432/testdb"

    def test_validate_database_url_with_postgres(self):
        """Test validate_database_url converts postgres:// to postgresql://."""
        from app.config import Settings

        # This should hit lines 54-56
        result = Settings.validate_database_url("postgres://user:pass@localhost:5432/testdb")
        assert result == "postgresql://user:pass@localhost:5432/testdb"

    def test_validate_database_url_empty_raises_error(self):
        """Test validate_database_url raises ValueError for empty string."""
        from app.config import Settings

        # This should hit line 47
        with pytest.raises(ValueError) as exc_info:
            Settings.validate_database_url("")

        assert "DATABASE_URL must be set" in str(exc_info.value)


class TestDatabaseURLValidator:
    """Tests for DATABASE_URL validation and transformation."""

    def test_database_url_postgres_to_postgresql_conversion(self):
        """Test that postgres:// scheme is converted to postgresql://."""
        # Use subprocess to avoid cached settings
        test_script = """
import os
os.environ["DATABASE_URL"] = "postgres://user:pass@localhost:5432/testdb"
os.environ["SECRET_KEY"] = "test-secret"

from app.config import Settings

settings = Settings()
assert settings.DATABASE_URL == "postgresql://user:pass@localhost:5432/testdb"
print("PASS: postgres:// converted to postgresql://")
"""
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
            cwd="/Users/jonpappas/Projects/soberoctobr/soberoctobr-backend"
        )

        assert "PASS: postgres:// converted to postgresql://" in result.stdout, \
            f"Test failed. STDOUT: {result.stdout}\nSTDERR: {result.stderr}"

    def test_database_url_postgresql_unchanged(self):
        """Test that postgresql:// scheme is not modified."""
        test_script = """
import os
os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/testdb"
os.environ["SECRET_KEY"] = "test-secret"

from app.config import Settings

settings = Settings()
assert settings.DATABASE_URL == "postgresql://user:pass@localhost:5432/testdb"
print("PASS: postgresql:// unchanged")
"""
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
            cwd="/Users/jonpappas/Projects/soberoctobr/soberoctobr-backend"
        )

        assert "PASS: postgresql:// unchanged" in result.stdout, \
            f"Test failed. STDOUT: {result.stdout}\nSTDERR: {result.stderr}"

    def test_database_url_empty_raises_error(self):
        """Test that empty DATABASE_URL raises ValueError."""
        test_script = """
import os
os.environ["DATABASE_URL"] = ""
os.environ["SECRET_KEY"] = "test-secret"

try:
    from app.config import Settings
    settings = Settings()
    print("FAIL: Should have raised ValueError")
    exit(1)
except ValueError as e:
    if "DATABASE_URL must be set" in str(e):
        print("PASS: ValueError raised for empty DATABASE_URL")
        exit(0)
    else:
        print(f"FAIL: Wrong error message: {e}")
        exit(1)
except Exception as e:
    print(f"FAIL: Wrong exception type: {type(e).__name__}: {e}")
    exit(1)
"""
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
            cwd="/Users/jonpappas/Projects/soberoctobr/soberoctobr-backend"
        )

        assert "PASS: ValueError raised for empty DATABASE_URL" in result.stdout, \
            f"Test failed. STDOUT: {result.stdout}\nSTDERR: {result.stderr}"


class TestCORSOriginsValidator:
    """Tests for CORS_ORIGINS parsing."""

    def test_cors_origins_list_unchanged(self):
        """Test that list of CORS origins is not modified."""
        test_script = """
import os
os.environ["SECRET_KEY"] = "test-secret"

from app.config import Settings

# Create settings with list (using default)
settings = Settings()
assert isinstance(settings.CORS_ORIGINS, list)
assert len(settings.CORS_ORIGINS) > 0
print("PASS: List of CORS origins unchanged")
"""
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
            cwd="/Users/jonpappas/Projects/soberoctobr/soberoctobr-backend"
        )

        assert "PASS: List of CORS origins unchanged" in result.stdout, \
            f"Test failed. STDOUT: {result.stdout}\nSTDERR: {result.stderr}"

    def test_cors_origins_json_string_parsing(self):
        """Test parsing CORS_ORIGINS from JSON array string."""
        # This test ensures we hit lines 147-149 (JSON parsing with list result)
        test_script = """
import os
import json
os.environ["CORS_ORIGINS"] = '["http://example.com", "http://example2.com"]'
os.environ["SECRET_KEY"] = "test-secret"

from app.config import Settings

settings = Settings()
assert isinstance(settings.CORS_ORIGINS, list)
assert len(settings.CORS_ORIGINS) == 2
assert "http://example.com" in settings.CORS_ORIGINS
assert "http://example2.com" in settings.CORS_ORIGINS
print("PASS: JSON string parsed correctly")
"""
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
            cwd="/Users/jonpappas/Projects/soberoctobr/soberoctobr-backend"
        )

        assert "PASS: JSON string parsed correctly" in result.stdout, \
            f"Test failed. STDOUT: {result.stdout}\nSTDERR: {result.stderr}"

    def test_cors_origins_comma_separated_parsing(self):
        """Test parsing CORS_ORIGINS from comma-separated string."""
        test_script = """
import os
os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://localhost:5173,http://example.com"
os.environ["SECRET_KEY"] = "test-secret"

from app.config import Settings

settings = Settings()
assert isinstance(settings.CORS_ORIGINS, list)
assert len(settings.CORS_ORIGINS) == 3
assert "http://localhost:3000" in settings.CORS_ORIGINS
assert "http://localhost:5173" in settings.CORS_ORIGINS
assert "http://example.com" in settings.CORS_ORIGINS
print("PASS: Comma-separated string parsed correctly")
"""
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
            cwd="/Users/jonpappas/Projects/soberoctobr/soberoctobr-backend"
        )

        assert "PASS: Comma-separated string parsed correctly" in result.stdout, \
            f"Test failed. STDOUT: {result.stdout}\nSTDERR: {result.stderr}"

    def test_cors_origins_comma_separated_with_whitespace(self):
        """Test parsing CORS_ORIGINS from comma-separated string with whitespace."""
        test_script = """
import os
os.environ["CORS_ORIGINS"] = "http://localhost:3000 , http://localhost:5173 , http://example.com"
os.environ["SECRET_KEY"] = "test-secret"

from app.config import Settings

settings = Settings()
assert isinstance(settings.CORS_ORIGINS, list)
assert len(settings.CORS_ORIGINS) == 3
assert "http://localhost:3000" in settings.CORS_ORIGINS
assert "http://localhost:5173" in settings.CORS_ORIGINS
print("PASS: Comma-separated with whitespace parsed correctly")
"""
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
            cwd="/Users/jonpappas/Projects/soberoctobr/soberoctobr-backend"
        )

        assert "PASS: Comma-separated with whitespace parsed correctly" in result.stdout, \
            f"Test failed. STDOUT: {result.stdout}\nSTDERR: {result.stderr}"

    def test_cors_origins_invalid_json_falls_back_to_comma_separated(self):
        """Test that invalid JSON falls back to comma-separated parsing."""
        test_script = """
import os
os.environ["CORS_ORIGINS"] = "not-a-json-array"
os.environ["SECRET_KEY"] = "test-secret"

from app.config import Settings

settings = Settings()
assert isinstance(settings.CORS_ORIGINS, list)
assert len(settings.CORS_ORIGINS) == 1
assert "not-a-json-array" in settings.CORS_ORIGINS
print("PASS: Invalid JSON falls back to comma-separated")
"""
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
            cwd="/Users/jonpappas/Projects/soberoctobr/soberoctobr-backend"
        )

        assert "PASS: Invalid JSON falls back to comma-separated" in result.stdout, \
            f"Test failed. STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
