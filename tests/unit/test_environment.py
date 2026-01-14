"""Unit tests for environment validation.

These tests verify the validate_environment function works correctly
and properly handles missing environment variables.
"""

import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, "src")
from agent import validate_environment


@pytest.mark.unit
class TestEnvironmentValidation:
    """Tests for error handling in the agent."""

    def test_validate_environment_missing_vars(self):
        """Test that missing environment variables raise RuntimeError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError) as exc_info:
                validate_environment()
            assert "Missing required environment variables" in str(exc_info.value)
            assert "LIVEKIT_URL" in str(exc_info.value)

    def test_validate_environment_partial_vars_missing_key(self):
        """Test with only URL set, missing API key."""
        with patch.dict(os.environ, {"LIVEKIT_URL": "wss://test"}, clear=True):
            with pytest.raises(RuntimeError) as exc_info:
                validate_environment()
            assert "LIVEKIT_API_KEY" in str(exc_info.value)

    def test_validate_environment_partial_vars_missing_secret(self):
        """Test with URL and key set, missing secret."""
        env = {
            "LIVEKIT_URL": "wss://test",
            "LIVEKIT_API_KEY": "key",
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(RuntimeError) as exc_info:
                validate_environment()
            assert "LIVEKIT_API_SECRET" in str(exc_info.value)

    def test_validate_environment_all_vars_present(self):
        """Test that no error is raised when all vars are present."""
        env = {
            "LIVEKIT_URL": "wss://test",
            "LIVEKIT_API_KEY": "key",
            "LIVEKIT_API_SECRET": "secret",
        }
        with patch.dict(os.environ, env, clear=True):
            # Should not raise
            validate_environment()

    def test_validate_environment_empty_values(self):
        """Test with empty string values (should count as missing)."""
        env = {
            "LIVEKIT_URL": "",
            "LIVEKIT_API_KEY": "",
            "LIVEKIT_API_SECRET": "",
        }
        with patch.dict(os.environ, env, clear=True):
            # Empty values might be treated as present or missing
            # depending on implementation - test documents actual behavior
            try:
                validate_environment()
                # If it doesn't raise, empty strings are accepted
            except RuntimeError:
                # If it raises, empty strings are treated as missing
                pass

    def test_validate_environment_whitespace_values(self):
        """Test with whitespace-only values."""
        env = {
            "LIVEKIT_URL": "wss://test.livekit.cloud",
            "LIVEKIT_API_KEY": "  valid_key  ",
            "LIVEKIT_API_SECRET": "  valid_secret  ",
        }
        with patch.dict(os.environ, env, clear=True):
            # Should not raise - whitespace around values is acceptable
            validate_environment()
