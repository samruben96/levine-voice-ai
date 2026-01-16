"""Unit tests for agent instruction generation.

These tests verify the Assistant and other agents generate correct
instructions with business hours context injection.
"""

import sys

import pytest

sys.path.insert(0, "src")
from agent import Assistant


@pytest.mark.unit
class TestAssistantBusinessHoursContext:
    """Tests for business hours context injection into Assistant instructions."""

    def test_assistant_accepts_business_hours_context_parameter(self):
        """Test that Assistant accepts a business_hours_context parameter."""
        # Create assistant with custom context
        custom_context = (
            "CURRENT TIME: 2:00 PM ET, Wednesday\nOFFICE STATUS: Open (closes at 5 PM)"
        )
        assistant = Assistant(business_hours_context=custom_context)

        # Verify the instructions contain the custom context
        assert "CURRENT TIME: 2:00 PM ET, Wednesday" in assistant.instructions
        assert "OFFICE STATUS: Open" in assistant.instructions

    def test_assistant_generates_context_when_none_provided(self):
        """Test that Assistant auto-generates context when none provided."""
        assistant = Assistant()

        # Should have CURRENT TIME and OFFICE STATUS in instructions
        assert "CURRENT TIME:" in assistant.instructions
        assert "OFFICE STATUS:" in assistant.instructions
        # Should have ET (Eastern Time) timezone indicator
        assert "ET" in assistant.instructions

    def test_assistant_instructions_contain_open_status_during_business_hours(self):
        """Test that instructions show 'Open' during simulated business hours."""
        # Simulate business hours context
        open_context = (
            "CURRENT TIME: 10:00 AM ET, Monday\nOFFICE STATUS: Open (closes at 5 PM)"
        )
        assistant = Assistant(business_hours_context=open_context)

        assert "OFFICE STATUS: Open" in assistant.instructions
        assert "closes at 5 PM" in assistant.instructions

    def test_assistant_instructions_contain_closed_status_after_hours(self):
        """Test that instructions show 'Closed' during simulated after hours."""
        # Simulate after hours context
        closed_context = (
            "CURRENT TIME: 7:00 PM ET, Tuesday\n"
            "OFFICE STATUS: Closed (reopens tomorrow at 9 AM)"
        )
        assistant = Assistant(business_hours_context=closed_context)

        assert "OFFICE STATUS: Closed" in assistant.instructions
        assert "reopens tomorrow" in assistant.instructions

    def test_assistant_instructions_contain_hours_guidance(self):
        """Test that instructions contain guidance for handling hours questions."""
        assistant = Assistant()

        # Should have guidance about using the CURRENT TIME/OFFICE STATUS context
        assert "OFFICE INFO" in assistant.instructions
        # Should have the static hours info as backup
        assert "9 AM to 5 PM" in assistant.instructions

    def test_assistant_instructions_contain_receptionist_identity(self):
        """Test that instructions establish Aizellee identity."""
        assistant = Assistant()

        # Should establish the receptionist identity
        assert (
            "Aizellee" in assistant.instructions
            or "receptionist" in assistant.instructions.lower()
        )

    def test_assistant_instructions_contain_company_info(self):
        """Test that instructions contain Harry Levine Insurance info."""
        assistant = Assistant()

        # Should mention the company
        assert "Harry Levine" in assistant.instructions

    def test_assistant_instructions_weekend_context(self):
        """Test that weekend context is correctly injected."""
        weekend_context = (
            "CURRENT TIME: 11:00 AM ET, Saturday\n"
            "OFFICE STATUS: Closed (reopens Monday at 9 AM)"
        )
        assistant = Assistant(business_hours_context=weekend_context)

        assert "Saturday" in assistant.instructions
        assert "Monday" in assistant.instructions

    def test_assistant_instructions_early_morning_context(self):
        """Test that early morning context is correctly injected."""
        early_context = (
            "CURRENT TIME: 7:00 AM ET, Thursday\nOFFICE STATUS: Closed (opens at 9 AM)"
        )
        assistant = Assistant(business_hours_context=early_context)

        assert "7:00 AM" in assistant.instructions
        assert "opens at 9 AM" in assistant.instructions


@pytest.mark.unit
class TestAssistantInstructionContent:
    """Tests for the content of Assistant instructions."""

    def test_assistant_instructions_not_empty(self):
        """Test that instructions are not empty."""
        assistant = Assistant()
        assert assistant.instructions
        assert len(assistant.instructions) > 100  # Should be substantial

    def test_assistant_instructions_contain_call_intents(self):
        """Test that instructions mention various call intents."""
        assistant = Assistant()
        instructions_lower = assistant.instructions.lower()

        # Should mention various reasons people might call
        assert "quote" in instructions_lower or "policy" in instructions_lower
        assert "claim" in instructions_lower or "payment" in instructions_lower

    def test_assistant_instructions_contain_transfer_guidance(self):
        """Test that instructions contain transfer guidance."""
        assistant = Assistant()
        instructions_lower = assistant.instructions.lower()

        # Should mention transfers
        assert "transfer" in instructions_lower or "connect" in instructions_lower

    def test_assistant_instructions_contain_contact_collection(self):
        """Test that instructions mention collecting contact info."""
        assistant = Assistant()
        instructions_lower = assistant.instructions.lower()

        # Should mention collecting name and phone
        assert "name" in instructions_lower
        assert "phone" in instructions_lower
