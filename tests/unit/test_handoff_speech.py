"""Unit tests for the handoff speech flag in CallerInfo.

These tests verify the _handoff_speech_delivered flag used to prevent
duplicate speech during agent handoffs.
"""

import sys

import pytest

sys.path.insert(0, "src")
from agent import CallerInfo, InsuranceType


@pytest.mark.unit
class TestHandoffSpeechFlag:
    """Tests for the _handoff_speech_delivered flag."""

    def test_handoff_flag_default_false(self):
        """New CallerInfo should have handoff flag set to False by default."""
        caller = CallerInfo()
        assert caller._handoff_speech_delivered is False

    def test_handoff_flag_can_be_set(self):
        """Verify flag can be set to True."""
        caller = CallerInfo()
        caller._handoff_speech_delivered = True
        assert caller._handoff_speech_delivered is True

    def test_handoff_flag_can_be_reset(self):
        """Verify flag can be toggled back to False."""
        caller = CallerInfo()
        caller._handoff_speech_delivered = True
        assert caller._handoff_speech_delivered is True
        caller._handoff_speech_delivered = False
        assert caller._handoff_speech_delivered is False

    def test_handoff_flag_getattr_safe_access(self):
        """Verify getattr with default works correctly (how agents access it)."""
        caller = CallerInfo()
        # This is how agents safely access the flag
        result = getattr(caller, "_handoff_speech_delivered", False)
        assert result is False

        # After setting to True
        caller._handoff_speech_delivered = True
        result = getattr(caller, "_handoff_speech_delivered", False)
        assert result is True

    def test_handoff_flag_preserved_in_dataclass(self):
        """Verify flag persists after other fields are modified."""
        caller = CallerInfo()
        caller._handoff_speech_delivered = True

        # Modify other fields
        caller.name = "John Smith"
        caller.phone_number = "555-1234"
        caller.insurance_type = InsuranceType.PERSONAL
        caller.last_name_spelled = "Smith"
        caller.additional_notes = "Test note"

        # Flag should still be True
        assert caller._handoff_speech_delivered is True


@pytest.mark.unit
class TestHandoffSpeechFlagViaConstructor:
    """Tests for setting handoff flag via constructor."""

    def test_handoff_flag_via_constructor_true(self):
        """Verify flag can be set to True via constructor."""
        caller = CallerInfo(_handoff_speech_delivered=True)
        assert caller._handoff_speech_delivered is True

    def test_handoff_flag_via_constructor_false(self):
        """Verify flag can be explicitly set to False via constructor."""
        caller = CallerInfo(_handoff_speech_delivered=False)
        assert caller._handoff_speech_delivered is False

    def test_handoff_flag_with_other_fields(self):
        """Verify flag works with other fields set via constructor."""
        caller = CallerInfo(
            name="Jane Doe",
            phone_number="555-9876",
            insurance_type=InsuranceType.BUSINESS,
            business_name="Acme Corp",
            _handoff_speech_delivered=True,
        )
        assert caller._handoff_speech_delivered is True
        assert caller.name == "Jane Doe"
        assert caller.business_name == "Acme Corp"
