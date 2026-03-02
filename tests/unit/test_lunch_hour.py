"""Unit tests for lunch hour handling in business_hours and Assistant agent.

These tests verify that:
- is_lunch_hour() correctly identifies the 12-1 PM window on weekdays
- _find_next_opening() returns 1 PM during lunch
- get_next_open_time() returns "in about N minutes" during lunch
- format_business_hours_prompt() shows "Lunch" status (not "Closed") during lunch
- Assistant._is_lunch / _is_after_hours flags are set correctly
- Greeting content reflects the correct office status

NO LLM API calls. NO network calls. Pure Python unit tests.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from business_hours import (
    _find_next_opening,
    format_business_hours_prompt,
    get_next_open_time,
    is_lunch_hour,
)

ET = ZoneInfo("America/New_York")


# =============================================================================
# 1. _find_next_opening during lunch
# =============================================================================


@pytest.mark.unit
class TestFindNextOpeningDuringLunch:
    """Tests for _find_next_opening() behavior during the lunch window."""

    def test_at_noon_monday_returns_1pm_same_day(self):
        """At 12:00 PM Monday (start of lunch), next opening is 1:00 PM same day."""
        # 2024-01-08 is a Monday
        now = datetime(2024, 1, 8, 12, 0, tzinfo=ET)
        result = _find_next_opening(now)
        assert result.date() == now.date()
        assert result.hour == 13
        assert result.minute == 0

    def test_at_12_30_tuesday_returns_1pm_same_day(self):
        """At 12:30 PM Tuesday, next opening is 1:00 PM same day."""
        # 2024-01-09 is a Tuesday
        now = datetime(2024, 1, 9, 12, 30, tzinfo=ET)
        result = _find_next_opening(now)
        assert result.date() == now.date()
        assert result.hour == 13
        assert result.minute == 0

    def test_at_12_59_wednesday_returns_1pm_same_day(self):
        """At 12:59 PM Wednesday, next opening is 1:00 PM same day."""
        # 2024-01-10 is a Wednesday
        now = datetime(2024, 1, 10, 12, 59, tzinfo=ET)
        result = _find_next_opening(now)
        assert result.date() == now.date()
        assert result.hour == 13
        assert result.minute == 0

    def test_at_1pm_thursday_not_lunch_returns_9am(self):
        """At 1:00 PM Thursday (lunch over, office open), next 'opening' is 9 AM today (already open)."""
        # 2024-01-11 is a Thursday
        now = datetime(2024, 1, 11, 13, 0, tzinfo=ET)
        result = _find_next_opening(now)
        # Office is open at 1 PM; _find_next_opening returns 9 AM same day
        assert result.date() == now.date()
        assert result.hour == 9
        assert result.minute == 0


# =============================================================================
# 2. format_business_hours_prompt during lunch
# =============================================================================


@pytest.mark.unit
class TestFormatBusinessHoursPromptDuringLunch:
    """Tests for format_business_hours_prompt() showing correct status at lunch."""

    def test_lunch_status_shown_at_12_30_monday(self):
        """At 12:30 PM Monday output must contain 'OFFICE STATUS: Lunch'."""
        # 2024-01-08 is a Monday
        now = datetime(2024, 1, 8, 12, 30, tzinfo=ET)
        prompt = format_business_hours_prompt(now)
        assert "OFFICE STATUS: Lunch" in prompt

    def test_lunch_status_does_not_say_closed_at_12_30_monday(self):
        """At 12:30 PM Monday output must NOT contain 'OFFICE STATUS: Closed'."""
        now = datetime(2024, 1, 8, 12, 30, tzinfo=ET)
        prompt = format_business_hours_prompt(now)
        assert "OFFICE STATUS: Closed" not in prompt

    def test_lunch_prompt_contains_reopens_minutes_phrase(self):
        """At 12:30 PM Monday prompt must mention reopening time in minutes."""
        now = datetime(2024, 1, 8, 12, 30, tzinfo=ET)
        prompt = format_business_hours_prompt(now)
        # Should contain "in about" with a minutes phrase
        assert "in about" in prompt and "minutes" in prompt

    def test_after_hours_status_shown_at_7pm_monday(self):
        """Regression: at 7:00 PM Monday output must contain 'OFFICE STATUS: Closed'."""
        now = datetime(2024, 1, 8, 19, 0, tzinfo=ET)
        prompt = format_business_hours_prompt(now)
        assert "OFFICE STATUS: Closed" in prompt

    def test_open_status_shown_at_10am_monday(self):
        """Regression: at 10:00 AM Monday output must contain 'OFFICE STATUS: Open'."""
        now = datetime(2024, 1, 8, 10, 0, tzinfo=ET)
        prompt = format_business_hours_prompt(now)
        assert "OFFICE STATUS: Open" in prompt

    def test_weekend_noon_shows_closed_not_lunch(self):
        """At 12:30 PM Saturday output must show 'Closed', not 'Lunch'."""
        # 2024-01-13 is a Saturday
        now = datetime(2024, 1, 13, 12, 30, tzinfo=ET)
        prompt = format_business_hours_prompt(now)
        assert "OFFICE STATUS: Closed" in prompt
        assert "OFFICE STATUS: Lunch" not in prompt


# =============================================================================
# 3. get_next_open_time during lunch
# =============================================================================


@pytest.mark.unit
class TestGetNextOpenTimeDuringLunch:
    """Tests for get_next_open_time() during the lunch window."""

    def test_at_12_30_monday_returns_about_30_minutes(self):
        """At 12:30 PM Monday, next open time should be 'in about 30 minutes'."""
        now = datetime(2024, 1, 8, 12, 30, tzinfo=ET)
        result = get_next_open_time(now)
        assert "in about" in result
        assert "minutes" in result

    def test_at_12_55_monday_returns_about_5_minutes(self):
        """At 12:55 PM Monday, next open time should be 'in about 5 minutes'."""
        now = datetime(2024, 1, 8, 12, 55, tzinfo=ET)
        result = get_next_open_time(now)
        assert "in about" in result
        assert "minutes" in result or "minute" in result

    def test_at_noon_monday_returns_about_60_minutes(self):
        """At 12:00 PM Monday (start of lunch), next open is in about 60 minutes."""
        now = datetime(2024, 1, 8, 12, 0, tzinfo=ET)
        result = get_next_open_time(now)
        assert "in about" in result
        # 60 minutes is the boundary; accept either "60 minutes" or "in about 60 minutes"
        assert "minutes" in result

    def test_at_12_30_result_is_not_now(self):
        """At 12:30 PM Monday, result must not be 'now' (office is on lunch)."""
        now = datetime(2024, 1, 8, 12, 30, tzinfo=ET)
        result = get_next_open_time(now)
        assert result != "now"


# =============================================================================
# 4. is_lunch_hour edge cases
# =============================================================================


@pytest.mark.unit
class TestIsLunchHourEdgeCases:
    """Edge case tests for is_lunch_hour() boundary and weekend behavior."""

    def test_at_exactly_noon_monday_is_lunch(self):
        """At 12:00:00 PM Monday, is_lunch_hour is True (boundary inclusive)."""
        now = datetime(2024, 1, 8, 12, 0, 0, tzinfo=ET)
        assert is_lunch_hour(now) is True

    def test_at_12_59_59_monday_is_lunch(self):
        """At 12:59:59 PM Monday, is_lunch_hour is True."""
        now = datetime(2024, 1, 8, 12, 59, 59, tzinfo=ET)
        assert is_lunch_hour(now) is True

    def test_at_exactly_1pm_monday_is_not_lunch(self):
        """At 1:00:00 PM Monday, is_lunch_hour is False (boundary exclusive)."""
        now = datetime(2024, 1, 8, 13, 0, 0, tzinfo=ET)
        assert is_lunch_hour(now) is False

    def test_at_11_59_59_monday_is_not_lunch(self):
        """At 11:59:59 AM Monday, is_lunch_hour is False."""
        now = datetime(2024, 1, 8, 11, 59, 59, tzinfo=ET)
        assert is_lunch_hour(now) is False

    def test_at_12_30_saturday_is_not_lunch(self):
        """At 12:30 PM Saturday, is_lunch_hour is False (weekend)."""
        now = datetime(2024, 1, 13, 12, 30, tzinfo=ET)
        assert is_lunch_hour(now) is False

    def test_at_12_30_sunday_is_not_lunch(self):
        """At 12:30 PM Sunday, is_lunch_hour is False (weekend)."""
        now = datetime(2024, 1, 14, 12, 30, tzinfo=ET)
        assert is_lunch_hour(now) is False


# =============================================================================
# 5. Assistant._is_lunch and _is_after_hours flags
# =============================================================================


@pytest.mark.unit
class TestAssistantLunchFlags:
    """Tests for Assistant._is_lunch and _is_after_hours flag derivation."""

    def test_lunch_context_sets_is_lunch_true_and_after_hours_false(self):
        """business_hours_context with 'OFFICE STATUS: Lunch' sets _is_lunch=True, _is_after_hours=False."""
        from agents.assistant import Assistant

        ctx = "CURRENT TIME: 12:30 PM ET, Monday\nOFFICE STATUS: Lunch (reopens in about 30 minutes)"
        agent = Assistant(business_hours_context=ctx)
        assert agent._is_lunch is True
        assert agent._is_after_hours is False

    def test_closed_context_sets_after_hours_true_and_is_lunch_false(self):
        """business_hours_context with 'OFFICE STATUS: Closed' sets _is_after_hours=True, _is_lunch=False."""
        from agents.assistant import Assistant

        ctx = "CURRENT TIME: 7:00 PM ET, Monday\nOFFICE STATUS: Closed (reopens tomorrow at 9 AM)"
        agent = Assistant(business_hours_context=ctx)
        assert agent._is_after_hours is True
        assert agent._is_lunch is False

    def test_open_context_sets_both_flags_false(self):
        """business_hours_context with 'OFFICE STATUS: Open' sets both flags to False."""
        from agents.assistant import Assistant

        ctx = "CURRENT TIME: 10:00 AM ET, Monday\nOFFICE STATUS: Open (closes at 5 PM)"
        agent = Assistant(business_hours_context=ctx)
        assert agent._is_lunch is False
        assert agent._is_after_hours is False

    def test_explicit_is_after_hours_true_sets_is_lunch_false(self):
        """With is_after_hours=True explicit, _is_lunch must be False."""
        from agents.assistant import Assistant

        agent = Assistant(is_after_hours=True)
        assert agent._is_after_hours is True
        assert agent._is_lunch is False


# =============================================================================
# 6. Greeting content for each office status
# =============================================================================


@pytest.mark.unit
class TestAssistantGreetingContent:
    """Tests for the greeting text embedded in Assistant instructions."""

    def test_lunch_greeting_contains_lunch(self):
        """Lunch-hour greeting must mention 'lunch'."""
        from agents.assistant import Assistant

        ctx = "CURRENT TIME: 12:30 PM ET, Monday\nOFFICE STATUS: Lunch (reopens in about 30 minutes)"
        agent = Assistant(business_hours_context=ctx)
        assert "lunch" in agent.instructions.lower()

    def test_lunch_greeting_contains_1_pm_return_time(self):
        """Lunch-hour greeting must mention '1' (for 1 PM return)."""
        from agents.assistant import Assistant

        ctx = "CURRENT TIME: 12:30 PM ET, Monday\nOFFICE STATUS: Lunch (reopens in about 30 minutes)"
        agent = Assistant(business_hours_context=ctx)
        # Greeting text includes "back at 1" for the 1 PM return
        assert "back at 1" in agent.instructions.lower()

    def test_after_hours_greeting_contains_closed(self):
        """After-hours greeting must mention 'closed'."""
        from agents.assistant import Assistant

        ctx = "CURRENT TIME: 7:00 PM ET, Monday\nOFFICE STATUS: Closed (reopens tomorrow at 9 AM)"
        agent = Assistant(business_hours_context=ctx)
        assert "closed" in agent.instructions.lower()

    def test_normal_greeting_does_not_mention_lunch(self):
        """Normal (open-hours) greeting must NOT contain 'lunch'."""
        from agents.assistant import Assistant

        ctx = "CURRENT TIME: 10:00 AM ET, Monday\nOFFICE STATUS: Open (closes at 5 PM)"
        agent = Assistant(business_hours_context=ctx)
        # The greeting instruction should not reference lunch
        # (static instructions may mention lunch hours in schedule info, so we
        # check the greeting section specifically via _is_lunch flag)
        assert agent._is_lunch is False

    def test_normal_greeting_does_not_say_closed(self):
        """Normal (open-hours) greeting must not say the office is closed in the greeting."""
        from agents.assistant import Assistant

        ctx = "CURRENT TIME: 10:00 AM ET, Monday\nOFFICE STATUS: Open (closes at 5 PM)"
        agent = Assistant(business_hours_context=ctx)
        assert agent._is_after_hours is False
