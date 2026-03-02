"""Unit tests for is_transferable staff directory function."""

import sys

import pytest

sys.path.insert(0, "src")
from staff_directory import is_transferable


@pytest.mark.unit
class TestIsTransferable:
    """Tests for is_transferable function checking transfer restrictions."""

    def test_restricted_agent_jason(self):
        """Test that Jason L. (restricted) cannot receive direct AI transfers."""
        assert is_transferable("Jason L.") is False

    def test_restricted_agent_fred(self):
        """Test that Fred (restricted) cannot receive direct AI transfers."""
        assert is_transferable("Fred") is False

    def test_normal_agent_adriana(self):
        """Test that Adriana (normal agent) can receive direct AI transfers."""
        assert is_transferable("Adriana") is True

    def test_unknown_agent_fails_closed(self):
        """Test that unknown agents are denied transfer (fail-closed)."""
        assert is_transferable("Nonexistent Agent") is False

    def test_explicitly_transferable_agent(self):
        """Test agent with explicit transferable=True."""
        assert is_transferable("Julie L.") is True

    def test_empty_string_agent_name(self):
        """Test that empty string agent name is denied (fail-closed)."""
        assert is_transferable("") is False
