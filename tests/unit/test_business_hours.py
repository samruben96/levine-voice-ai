"""Tests for business hours functionality.

These tests verify the business hours awareness functions in src/business_hours.py:
- is_office_open() - Determine if the office is currently open
- get_next_open_time() - Calculate when the office will reopen
- get_business_hours_context() - Provide context dict for agent prompts
- get_current_time() - Get current time in Eastern timezone
- format_business_hours_prompt() - Format business hours for LLM prompts

Business hours: Monday-Friday, 9 AM to 5 PM Eastern (America/New_York)
"""

# Import from the src directory
import sys
from datetime import datetime, time
from zoneinfo import ZoneInfo

import pytest

sys.path.insert(0, "src")

from business_hours import (
    LUNCH_END,
    LUNCH_START,
    OFFICE_HOURS_DISPLAY,
    TIMEZONE,
    WEEKLY_SCHEDULE,
    DaySchedule,
    format_business_hours_prompt,
    get_business_hours_context,
    get_current_time,
    get_next_open_time,
    get_timezone,
    is_lunch_hour,
    is_office_open,
)

# Eastern timezone constant for tests
EASTERN_TZ = ZoneInfo("America/New_York")


# =============================================================================
# HELPER FUNCTIONS FOR CREATING TEST TIMES
# =============================================================================


def make_eastern_datetime(
    year: int, month: int, day: int, hour: int, minute: int = 0, second: int = 0
) -> datetime:
    """Create a datetime in Eastern timezone for testing.

    Args:
        year: Year
        month: Month (1-12)
        day: Day of month
        hour: Hour (0-23)
        minute: Minute (0-59)
        second: Second (0-59)

    Returns:
        datetime in America/New_York timezone
    """
    return datetime(year, month, day, hour, minute, second, tzinfo=EASTERN_TZ)


# =============================================================================
# Test dates reference:
# - 2024-01-08 = Monday
# - 2024-01-09 = Tuesday
# - 2024-01-10 = Wednesday
# - 2024-01-11 = Thursday
# - 2024-01-12 = Friday
# - 2024-01-13 = Saturday
# - 2024-01-14 = Sunday
# - 2024-01-15 = Monday
# =============================================================================


class TestConfiguration:
    """Tests for business hours configuration constants."""

    def test_timezone_is_eastern(self) -> None:
        """TIMEZONE constant should be America/New_York."""
        assert TIMEZONE == "America/New_York"

    def test_get_timezone_returns_zoneinfo(self) -> None:
        """get_timezone() should return ZoneInfo for America/New_York."""
        tz = get_timezone()
        assert str(tz) == "America/New_York"

    def test_office_hours_display(self) -> None:
        """OFFICE_HOURS_DISPLAY should describe M-F 9-5."""
        assert "Monday" in OFFICE_HOURS_DISPLAY
        assert "Friday" in OFFICE_HOURS_DISPLAY
        assert "9" in OFFICE_HOURS_DISPLAY
        assert "5" in OFFICE_HOURS_DISPLAY

    def test_weekly_schedule_has_all_days(self) -> None:
        """WEEKLY_SCHEDULE should have entries for all 7 days."""
        assert len(WEEKLY_SCHEDULE) == 7
        for day in range(7):
            assert day in WEEKLY_SCHEDULE

    def test_weekdays_have_9_to_5_schedule(self) -> None:
        """Monday-Friday should have 9 AM to 5 PM schedule."""
        for day in range(5):  # Monday (0) through Friday (4)
            schedule = WEEKLY_SCHEDULE[day]
            assert isinstance(schedule, DaySchedule)
            assert schedule.open_time == time(9, 0)
            assert schedule.close_time == time(17, 0)
            assert not schedule.is_closed

    def test_weekends_are_closed(self) -> None:
        """Saturday and Sunday should be closed."""
        for day in [5, 6]:  # Saturday, Sunday
            schedule = WEEKLY_SCHEDULE[day]
            assert isinstance(schedule, DaySchedule)
            assert schedule.is_closed


class TestGetCurrentTime:
    """Tests for get_current_time() function."""

    def test_returns_datetime_with_eastern_timezone(self) -> None:
        """get_current_time() should return a datetime in Eastern timezone."""
        now = get_current_time()
        assert now.tzinfo is not None
        assert str(now.tzinfo) == "America/New_York"

    def test_returns_current_time_approximately(self) -> None:
        """The returned time should be approximately now (within 1 second)."""
        before = datetime.now(EASTERN_TZ)
        result = get_current_time()
        after = datetime.now(EASTERN_TZ)

        assert before <= result <= after


class TestIsOfficeOpen:
    """Tests for is_office_open() function."""

    # -------------------------------------------------------------------------
    # Weekday during business hours (should be OPEN)
    # -------------------------------------------------------------------------

    def test_monday_10am_is_open(self) -> None:
        """Monday at 10 AM ET should be open."""
        test_time = make_eastern_datetime(2024, 1, 8, 10, 0)  # Monday 10:00 AM
        assert is_office_open(test_time) is True

    def test_tuesday_2pm_is_open(self) -> None:
        """Tuesday at 2 PM ET should be open."""
        test_time = make_eastern_datetime(2024, 1, 9, 14, 0)  # Tuesday 2:00 PM
        assert is_office_open(test_time) is True

    def test_wednesday_noon_is_closed_for_lunch(self) -> None:
        """Wednesday at noon ET should be closed for lunch."""
        test_time = make_eastern_datetime(2024, 1, 10, 12, 0)  # Wednesday 12:00 PM
        assert is_office_open(test_time) is False

    def test_thursday_930am_is_open(self) -> None:
        """Thursday at 9:30 AM ET should be open."""
        test_time = make_eastern_datetime(2024, 1, 11, 9, 30)  # Thursday 9:30 AM
        assert is_office_open(test_time) is True

    def test_friday_3pm_is_open(self) -> None:
        """Friday at 3 PM ET should be open."""
        test_time = make_eastern_datetime(2024, 1, 12, 15, 0)  # Friday 3:00 PM
        assert is_office_open(test_time) is True

    # -------------------------------------------------------------------------
    # Edge cases at opening time (9:00 AM)
    # -------------------------------------------------------------------------

    def test_monday_9am_exactly_is_open(self) -> None:
        """Monday at exactly 9:00:00 AM ET should be open (opening time)."""
        test_time = make_eastern_datetime(2024, 1, 8, 9, 0, 0)  # Monday 9:00:00 AM
        assert is_office_open(test_time) is True

    def test_monday_9am_1second_is_open(self) -> None:
        """Monday at 9:00:01 AM ET should be open."""
        test_time = make_eastern_datetime(2024, 1, 8, 9, 0, 1)  # Monday 9:00:01 AM
        assert is_office_open(test_time) is True

    # -------------------------------------------------------------------------
    # Edge cases at closing time (5:00 PM)
    # -------------------------------------------------------------------------

    def test_monday_459pm_is_open(self) -> None:
        """Monday at 4:59 PM ET should be open (just before closing)."""
        test_time = make_eastern_datetime(2024, 1, 8, 16, 59)  # Monday 4:59 PM
        assert is_office_open(test_time) is True

    def test_monday_45959pm_is_open(self) -> None:
        """Monday at 4:59:59 PM ET should be open (1 second before closing)."""
        test_time = make_eastern_datetime(2024, 1, 8, 16, 59, 59)  # Monday 4:59:59 PM
        assert is_office_open(test_time) is True

    def test_monday_5pm_exactly_is_closed(self) -> None:
        """Monday at exactly 5:00:00 PM ET should be closed (closing time)."""
        test_time = make_eastern_datetime(2024, 1, 8, 17, 0, 0)  # Monday 5:00:00 PM
        assert is_office_open(test_time) is False

    def test_monday_501pm_is_closed(self) -> None:
        """Monday at 5:01 PM ET should be closed."""
        test_time = make_eastern_datetime(2024, 1, 8, 17, 1)  # Monday 5:01 PM
        assert is_office_open(test_time) is False

    # -------------------------------------------------------------------------
    # Edge cases before opening time (before 9:00 AM)
    # -------------------------------------------------------------------------

    def test_monday_859am_is_closed(self) -> None:
        """Monday at 8:59 AM ET should be closed (before opening)."""
        test_time = make_eastern_datetime(2024, 1, 8, 8, 59)  # Monday 8:59 AM
        assert is_office_open(test_time) is False

    def test_monday_85959am_is_closed(self) -> None:
        """Monday at 8:59:59 AM ET should be closed (1 second before opening)."""
        test_time = make_eastern_datetime(2024, 1, 8, 8, 59, 59)  # Monday 8:59:59 AM
        assert is_office_open(test_time) is False

    def test_monday_6am_is_closed(self) -> None:
        """Monday at 6 AM ET should be closed (early morning)."""
        test_time = make_eastern_datetime(2024, 1, 8, 6, 0)  # Monday 6:00 AM
        assert is_office_open(test_time) is False

    def test_monday_midnight_is_closed(self) -> None:
        """Monday at midnight ET should be closed."""
        test_time = make_eastern_datetime(2024, 1, 8, 0, 0)  # Monday 12:00 AM
        assert is_office_open(test_time) is False

    # -------------------------------------------------------------------------
    # Weekend (always closed)
    # -------------------------------------------------------------------------

    def test_saturday_10am_is_closed(self) -> None:
        """Saturday at 10 AM ET should be closed (weekend)."""
        test_time = make_eastern_datetime(2024, 1, 13, 10, 0)  # Saturday 10:00 AM
        assert is_office_open(test_time) is False

    def test_saturday_noon_is_closed(self) -> None:
        """Saturday at noon ET should be closed (weekend)."""
        test_time = make_eastern_datetime(2024, 1, 13, 12, 0)  # Saturday 12:00 PM
        assert is_office_open(test_time) is False

    def test_sunday_2pm_is_closed(self) -> None:
        """Sunday at 2 PM ET should be closed (weekend)."""
        test_time = make_eastern_datetime(2024, 1, 14, 14, 0)  # Sunday 2:00 PM
        assert is_office_open(test_time) is False

    def test_sunday_10am_is_closed(self) -> None:
        """Sunday at 10 AM ET should be closed (weekend)."""
        test_time = make_eastern_datetime(2024, 1, 14, 10, 0)  # Sunday 10:00 AM
        assert is_office_open(test_time) is False

    # -------------------------------------------------------------------------
    # After hours on weekdays (closed)
    # -------------------------------------------------------------------------

    def test_monday_6pm_is_closed(self) -> None:
        """Monday at 6 PM ET should be closed (after hours)."""
        test_time = make_eastern_datetime(2024, 1, 8, 18, 0)  # Monday 6:00 PM
        assert is_office_open(test_time) is False

    def test_wednesday_10pm_is_closed(self) -> None:
        """Wednesday at 10 PM ET should be closed (late night)."""
        test_time = make_eastern_datetime(2024, 1, 10, 22, 0)  # Wednesday 10:00 PM
        assert is_office_open(test_time) is False

    def test_friday_8pm_is_closed(self) -> None:
        """Friday at 8 PM ET should be closed (weekend starting)."""
        test_time = make_eastern_datetime(2024, 1, 12, 20, 0)  # Friday 8:00 PM
        assert is_office_open(test_time) is False

    # -------------------------------------------------------------------------
    # Function signature tests
    # -------------------------------------------------------------------------

    def test_accepts_none_uses_current_time(self) -> None:
        """is_office_open(None) should work and return a boolean."""
        result = is_office_open(None)
        assert isinstance(result, bool)

    def test_accepts_no_argument(self) -> None:
        """is_office_open() with no args should work."""
        result = is_office_open()
        assert isinstance(result, bool)


class TestLunchHour:
    """Tests for lunch hour detection (12:00 PM - 1:00 PM Eastern)."""

    # -------------------------------------------------------------------------
    # Lunch hour constants
    # -------------------------------------------------------------------------

    def test_lunch_start_is_noon(self) -> None:
        """LUNCH_START should be 12:00 PM."""
        assert time(12, 0) == LUNCH_START

    def test_lunch_end_is_1pm(self) -> None:
        """LUNCH_END should be 1:00 PM."""
        assert time(13, 0) == LUNCH_END

    # -------------------------------------------------------------------------
    # is_lunch_hour function tests
    # -------------------------------------------------------------------------

    def test_1230pm_tuesday_is_lunch_hour(self) -> None:
        """12:30 PM on Tuesday should be lunch hour."""
        test_time = make_eastern_datetime(2024, 1, 9, 12, 30)  # Tuesday 12:30 PM
        assert is_lunch_hour(test_time) is True

    def test_1130am_tuesday_is_not_lunch_hour(self) -> None:
        """11:30 AM on Tuesday should NOT be lunch hour."""
        test_time = make_eastern_datetime(2024, 1, 9, 11, 30)  # Tuesday 11:30 AM
        assert is_lunch_hour(test_time) is False

    def test_noon_exactly_is_lunch_hour(self) -> None:
        """12:00 PM exactly should be lunch hour."""
        test_time = make_eastern_datetime(2024, 1, 9, 12, 0)  # Tuesday 12:00 PM
        assert is_lunch_hour(test_time) is True

    def test_1pm_exactly_is_not_lunch_hour(self) -> None:
        """1:00 PM exactly should NOT be lunch hour (office reopens)."""
        test_time = make_eastern_datetime(2024, 1, 9, 13, 0)  # Tuesday 1:00 PM
        assert is_lunch_hour(test_time) is False

    def test_1259pm_is_lunch_hour(self) -> None:
        """12:59 PM should still be lunch hour."""
        test_time = make_eastern_datetime(2024, 1, 9, 12, 59)  # Tuesday 12:59 PM
        assert is_lunch_hour(test_time) is True

    def test_saturday_noon_is_not_lunch_hour(self) -> None:
        """Saturday at noon should NOT be lunch hour (weekend)."""
        test_time = make_eastern_datetime(2024, 1, 13, 12, 30)  # Saturday 12:30 PM
        assert is_lunch_hour(test_time) is False

    def test_sunday_noon_is_not_lunch_hour(self) -> None:
        """Sunday at noon should NOT be lunch hour (weekend)."""
        test_time = make_eastern_datetime(2024, 1, 14, 12, 30)  # Sunday 12:30 PM
        assert is_lunch_hour(test_time) is False

    def test_each_weekday_at_lunch(self) -> None:
        """Every weekday at 12:30 PM should be lunch hour."""
        # Week of Jan 8-12, 2024
        for day in range(8, 13):  # Monday through Friday
            test_time = make_eastern_datetime(2024, 1, day, 12, 30)
            assert is_lunch_hour(test_time) is True, f"Failed for day {day}"

    # -------------------------------------------------------------------------
    # is_office_open during lunch hour
    # -------------------------------------------------------------------------

    def test_office_closed_during_lunch(self) -> None:
        """Office should be closed during lunch hour."""
        test_time = make_eastern_datetime(2024, 1, 9, 12, 30)  # Tuesday 12:30 PM
        assert is_office_open(test_time) is False

    def test_office_open_at_1159am(self) -> None:
        """Office should be open at 11:59 AM (before lunch)."""
        test_time = make_eastern_datetime(2024, 1, 9, 11, 59)  # Tuesday 11:59 AM
        assert is_office_open(test_time) is True

    def test_office_open_at_1pm(self) -> None:
        """Office should be open at 1:00 PM (after lunch)."""
        test_time = make_eastern_datetime(2024, 1, 9, 13, 0)  # Tuesday 1:00 PM
        assert is_office_open(test_time) is True

    def test_office_open_at_101pm(self) -> None:
        """Office should be open at 1:01 PM (after lunch)."""
        test_time = make_eastern_datetime(2024, 1, 9, 13, 1)  # Tuesday 1:01 PM
        assert is_office_open(test_time) is True

    def test_accepts_none_uses_current_time(self) -> None:
        """is_lunch_hour(None) should work and return a boolean."""
        result = is_lunch_hour(None)
        assert isinstance(result, bool)

    def test_accepts_no_argument(self) -> None:
        """is_lunch_hour() with no args should work."""
        result = is_lunch_hour()
        assert isinstance(result, bool)


class TestIsOfficeOpenEdgeCases:
    """Additional edge case tests for is_office_open()."""

    def test_new_years_day_midnight(self) -> None:
        """New Year's Day at midnight - closed (outside hours)."""
        # 2024-01-01 is a Monday
        test_time = make_eastern_datetime(2024, 1, 1, 0, 0)  # Monday midnight
        assert is_office_open(test_time) is False

    def test_new_years_day_during_business_hours(self) -> None:
        """New Year's Day during business hours.

        Note: 2024-01-01 is a Monday. Without holiday awareness, it's "open".
        """
        test_time = make_eastern_datetime(2024, 1, 1, 10, 0)  # Monday 10 AM
        # Currently no holiday awareness, so Monday at 10am is "open"
        assert is_office_open(test_time) is True

    def test_end_of_year_friday_afternoon(self) -> None:
        """December 29, 2023 (Friday) at 4pm should be open."""
        test_time = make_eastern_datetime(2023, 12, 29, 16, 0)  # Friday 4:00 PM
        assert is_office_open(test_time) is True

    def test_each_weekday_at_noon_is_closed_for_lunch(self) -> None:
        """Every weekday at noon should be closed for lunch (12-1 PM)."""
        # Week of Jan 8-12, 2024
        for day in range(8, 13):  # Monday through Friday
            test_time = make_eastern_datetime(2024, 1, day, 12, 0)
            assert is_office_open(test_time) is False, f"Failed for day {day}"

    def test_each_weekday_at_8am(self) -> None:
        """Every weekday at 8 AM should be closed (before opening)."""
        for day in range(8, 13):  # Monday through Friday
            test_time = make_eastern_datetime(2024, 1, day, 8, 0)
            assert is_office_open(test_time) is False, f"Failed for day {day}"

    def test_each_weekday_at_6pm(self) -> None:
        """Every weekday at 6 PM should be closed (after closing)."""
        for day in range(8, 13):  # Monday through Friday
            test_time = make_eastern_datetime(2024, 1, day, 18, 0)
            assert is_office_open(test_time) is False, f"Failed for day {day}"

    def test_handles_naive_datetime_as_eastern(self) -> None:
        """Naive datetime should be treated as Eastern time."""
        # Naive datetime (no timezone)
        naive_time = datetime(2024, 1, 9, 10, 0)  # Tuesday 10 AM
        assert is_office_open(naive_time) is True

    def test_handles_utc_datetime(self) -> None:
        """UTC datetime should be converted to Eastern."""
        # 3 PM Eastern = 8 PM UTC (during EST, offset -5)
        utc_time = datetime(2024, 1, 9, 20, 0, tzinfo=ZoneInfo("UTC"))
        assert is_office_open(utc_time) is True  # 3 PM Eastern = open


class TestGetNextOpenTime:
    """Tests for get_next_open_time() function."""

    # -------------------------------------------------------------------------
    # Weekday after hours -> next day
    # -------------------------------------------------------------------------

    def test_monday_6pm_returns_tomorrow(self) -> None:
        """Monday at 6 PM should return 'tomorrow at 9 AM'."""
        test_time = make_eastern_datetime(2024, 1, 8, 18, 0)  # Monday 6 PM
        result = get_next_open_time(test_time)
        assert result == "tomorrow at 9 AM"

    def test_tuesday_7pm_returns_tomorrow(self) -> None:
        """Tuesday at 7 PM should return 'tomorrow at 9 AM'."""
        test_time = make_eastern_datetime(2024, 1, 9, 19, 0)  # Tuesday 7 PM
        result = get_next_open_time(test_time)
        assert result == "tomorrow at 9 AM"

    def test_wednesday_late_night_returns_tomorrow(self) -> None:
        """Wednesday at 11 PM should return 'tomorrow at 9 AM'."""
        test_time = make_eastern_datetime(2024, 1, 10, 23, 0)  # Wednesday 11 PM
        result = get_next_open_time(test_time)
        assert result == "tomorrow at 9 AM"

    def test_thursday_5pm_returns_tomorrow(self) -> None:
        """Thursday at 5 PM (just closed) should return 'tomorrow at 9 AM'."""
        test_time = make_eastern_datetime(2024, 1, 11, 17, 0)  # Thursday 5 PM
        result = get_next_open_time(test_time)
        assert result == "tomorrow at 9 AM"

    # -------------------------------------------------------------------------
    # Friday after hours -> Monday
    # -------------------------------------------------------------------------

    def test_friday_6pm_returns_monday(self) -> None:
        """Friday at 6 PM should return 'Monday at 9 AM'."""
        test_time = make_eastern_datetime(2024, 1, 12, 18, 0)  # Friday 6 PM
        result = get_next_open_time(test_time)
        assert result == "Monday at 9 AM"

    def test_friday_10pm_returns_monday(self) -> None:
        """Friday at 10 PM should return 'Monday at 9 AM'."""
        test_time = make_eastern_datetime(2024, 1, 12, 22, 0)  # Friday 10 PM
        result = get_next_open_time(test_time)
        assert result == "Monday at 9 AM"

    # -------------------------------------------------------------------------
    # Weekend -> Monday
    # -------------------------------------------------------------------------

    def test_saturday_10am_returns_monday(self) -> None:
        """Saturday at 10 AM should return 'Monday at 9 AM'."""
        test_time = make_eastern_datetime(2024, 1, 13, 10, 0)  # Saturday 10 AM
        result = get_next_open_time(test_time)
        assert result == "Monday at 9 AM"

    def test_saturday_midnight_returns_monday(self) -> None:
        """Saturday at midnight should return 'Monday at 9 AM'."""
        test_time = make_eastern_datetime(2024, 1, 13, 0, 0)  # Saturday midnight
        result = get_next_open_time(test_time)
        assert result == "Monday at 9 AM"

    def test_sunday_10am_returns_tomorrow(self) -> None:
        """Sunday at 10 AM should return 'tomorrow at 9 AM' (Monday)."""
        test_time = make_eastern_datetime(2024, 1, 14, 10, 0)  # Sunday 10 AM
        result = get_next_open_time(test_time)
        assert result == "tomorrow at 9 AM"

    def test_sunday_11pm_returns_tomorrow(self) -> None:
        """Sunday at 11 PM should return 'tomorrow at 9 AM' (Monday)."""
        test_time = make_eastern_datetime(2024, 1, 14, 23, 0)  # Sunday 11 PM
        result = get_next_open_time(test_time)
        assert result == "tomorrow at 9 AM"

    # -------------------------------------------------------------------------
    # Weekday before opening - "later today" or "in about X minutes"
    # -------------------------------------------------------------------------

    def test_monday_830am_returns_in_about_30_minutes(self) -> None:
        """Monday at 8:30 AM returns 'in about 30 minutes'."""
        test_time = make_eastern_datetime(2024, 1, 8, 8, 30)  # Monday 8:30 AM
        result = get_next_open_time(test_time)
        assert result == "in about 30 minutes"

    def test_tuesday_7am_returns_later_today(self) -> None:
        """Tuesday at 7 AM returns 'later today at 9 AM' (more than 1 hour)."""
        test_time = make_eastern_datetime(2024, 1, 9, 7, 0)  # Tuesday 7 AM
        result = get_next_open_time(test_time)
        assert result == "later today at 9 AM"

    def test_wednesday_855am_returns_in_about_5_minutes(self) -> None:
        """Wednesday at 8:55 AM returns 'in about 5 minutes'."""
        test_time = make_eastern_datetime(2024, 1, 10, 8, 55)  # Wednesday 8:55 AM
        result = get_next_open_time(test_time)
        assert result == "in about 5 minutes"

    def test_thursday_8am_returns_in_about_60_minutes(self) -> None:
        """Thursday at 8 AM returns 'in about 60 minutes' (exactly 1 hour)."""
        test_time = make_eastern_datetime(2024, 1, 11, 8, 0)  # Thursday 8 AM
        result = get_next_open_time(test_time)
        assert result == "in about 60 minutes"

    def test_friday_859am_returns_in_about_a_minute(self) -> None:
        """Friday at 8:59 AM returns 'in about a minute' (or similar)."""
        test_time = make_eastern_datetime(2024, 1, 12, 8, 59)  # Friday 8:59 AM
        result = get_next_open_time(test_time)
        # Could be "in about 1 minutes" or "in about a minute"
        assert "minute" in result.lower()

    # -------------------------------------------------------------------------
    # Function signature tests
    # -------------------------------------------------------------------------

    def test_accepts_none_uses_current_time(self) -> None:
        """get_next_open_time(None) should work and return a string."""
        result = get_next_open_time(None)
        assert isinstance(result, str)

    def test_accepts_no_argument(self) -> None:
        """get_next_open_time() with no args should work."""
        result = get_next_open_time()
        assert isinstance(result, str)


class TestGetNextOpenTimeEdgeCases:
    """Edge case tests for get_next_open_time()."""

    def test_exactly_at_closing_time(self) -> None:
        """At exactly 5:00 PM on Monday, should return next opening time."""
        test_time = make_eastern_datetime(2024, 1, 8, 17, 0, 0)  # Monday 5:00:00 PM
        result = get_next_open_time(test_time)
        assert result == "tomorrow at 9 AM"

    def test_during_business_hours_returns_now(self) -> None:
        """When office is open, should return 'now'."""
        test_time = make_eastern_datetime(2024, 1, 9, 10, 0)  # Tuesday 10 AM
        result = get_next_open_time(test_time)
        assert result == "now"

    def test_exactly_at_opening_time(self) -> None:
        """At exactly 9:00 AM on Monday, should return 'now'."""
        test_time = make_eastern_datetime(2024, 1, 8, 9, 0, 0)  # Monday 9:00:00 AM
        result = get_next_open_time(test_time)
        assert result == "now"


class TestGetBusinessHoursContext:
    """Tests for get_business_hours_context() function.

    This function returns a dict with business hours context for LLM prompts.
    """

    def test_returns_dict(self) -> None:
        """Verify the function returns a dictionary."""
        result = get_business_hours_context()
        assert isinstance(result, dict)

    def test_has_required_keys(self) -> None:
        """Verify the returned dict has all required keys."""
        result = get_business_hours_context()

        assert "current_time" in result
        assert "is_open" in result
        assert "next_open_time" in result
        assert "office_hours" in result

    def test_is_open_is_boolean(self) -> None:
        """Verify is_open is a boolean value."""
        result = get_business_hours_context()
        assert isinstance(result["is_open"], bool)

    def test_current_time_is_string(self) -> None:
        """Verify current_time is a formatted string."""
        result = get_business_hours_context()
        assert isinstance(result["current_time"], str)
        assert len(result["current_time"]) > 0

    def test_office_hours_contains_schedule(self) -> None:
        """Verify office_hours contains the schedule."""
        result = get_business_hours_context()
        assert isinstance(result["office_hours"], str)
        assert result["office_hours"] == OFFICE_HOURS_DISPLAY

    def test_during_business_hours(self) -> None:
        """During business hours, is_open should be True."""
        test_time = make_eastern_datetime(2024, 1, 9, 14, 30)  # Tuesday 2:30 PM
        result = get_business_hours_context(test_time)

        assert result["is_open"] is True
        assert result["next_open_time"] is None
        assert "2:30 PM" in result["current_time"]
        assert "Tuesday" in result["current_time"]

    def test_after_hours(self) -> None:
        """After hours, is_open should be False with next_open_time."""
        test_time = make_eastern_datetime(2024, 1, 9, 19, 0)  # Tuesday 7 PM
        result = get_business_hours_context(test_time)

        assert result["is_open"] is False
        assert result["next_open_time"] == "tomorrow at 9 AM"

    def test_weekend(self) -> None:
        """On weekend, is_open should be False."""
        test_time = make_eastern_datetime(2024, 1, 13, 12, 0)  # Saturday noon
        result = get_business_hours_context(test_time)

        assert result["is_open"] is False
        assert result["next_open_time"] == "Monday at 9 AM"

    def test_friday_evening_shows_monday_reopen(self) -> None:
        """Friday evening should show Monday reopen time."""
        test_time = make_eastern_datetime(2024, 1, 12, 20, 0)  # Friday 8 PM
        result = get_business_hours_context(test_time)

        assert result["is_open"] is False
        assert result["next_open_time"] == "Monday at 9 AM"

    def test_monday_morning_before_open(self) -> None:
        """Monday morning before 9 AM should show closed."""
        test_time = make_eastern_datetime(2024, 1, 8, 8, 30)  # Monday 8:30 AM
        result = get_business_hours_context(test_time)

        assert result["is_open"] is False
        assert result["next_open_time"] == "in about 30 minutes"

    def test_accepts_none_argument(self) -> None:
        """get_business_hours_context(None) should work."""
        result = get_business_hours_context(None)
        assert isinstance(result, dict)
        assert "is_open" in result

    def test_accepts_no_argument(self) -> None:
        """get_business_hours_context() with no args should work."""
        result = get_business_hours_context()
        assert isinstance(result, dict)


class TestFormatBusinessHoursPrompt:
    """Tests for format_business_hours_prompt() function."""

    def test_returns_string(self) -> None:
        """Verify the function returns a string."""
        result = format_business_hours_prompt()
        assert isinstance(result, str)

    def test_contains_current_time_header(self) -> None:
        """Verify the returned string contains CURRENT TIME header."""
        result = format_business_hours_prompt()
        assert "CURRENT TIME:" in result

    def test_contains_office_status_header(self) -> None:
        """Verify the returned string contains OFFICE STATUS header."""
        result = format_business_hours_prompt()
        assert "OFFICE STATUS:" in result

    def test_during_business_hours_shows_open(self) -> None:
        """During business hours, should show 'Open (closes at 5 PM)'."""
        test_time = make_eastern_datetime(2024, 1, 9, 14, 30)  # Tuesday 2:30 PM
        result = format_business_hours_prompt(test_time)

        assert "OFFICE STATUS: Open" in result
        assert "closes at 5 PM" in result

    def test_after_hours_shows_closed(self) -> None:
        """After hours, should show 'Closed' with reopen time."""
        test_time = make_eastern_datetime(2024, 1, 9, 19, 0)  # Tuesday 7 PM
        result = format_business_hours_prompt(test_time)

        assert "OFFICE STATUS: Closed" in result
        assert "reopens tomorrow at 9 AM" in result

    def test_weekend_shows_closed(self) -> None:
        """On weekend, should show 'Closed' with Monday reopen time."""
        test_time = make_eastern_datetime(2024, 1, 13, 12, 0)  # Saturday noon
        result = format_business_hours_prompt(test_time)

        assert "OFFICE STATUS: Closed" in result
        assert "reopens Monday at 9 AM" in result

    def test_shows_correct_day_of_week(self) -> None:
        """Should show the correct day of week in current time."""
        test_time = make_eastern_datetime(2024, 1, 8, 10, 0)  # Monday 10 AM
        result = format_business_hours_prompt(test_time)
        assert "Monday" in result

    def test_shows_et_timezone(self) -> None:
        """Should show ET timezone."""
        result = format_business_hours_prompt()
        assert "ET" in result


class TestDaylightSavingTimeHandling:
    """Tests for DST transition handling.

    DST 2024:
    - Spring forward: March 10, 2024 (2 AM becomes 3 AM)
    - Fall back: November 3, 2024 (2 AM becomes 1 AM)
    """

    def test_day_before_spring_forward(self) -> None:
        """Saturday before spring DST - should be closed (weekend)."""
        test_time = make_eastern_datetime(2024, 3, 9, 10, 0)  # Sat Mar 9
        assert is_office_open(test_time) is False

    def test_monday_after_spring_forward(self) -> None:
        """Monday after spring DST transition - should work normally."""
        test_time = make_eastern_datetime(2024, 3, 11, 10, 0)  # Mon Mar 11
        assert is_office_open(test_time) is True

    def test_friday_before_fall_back(self) -> None:
        """Friday before fall DST - should be open during business hours."""
        test_time = make_eastern_datetime(2024, 11, 1, 10, 0)  # Fri Nov 1
        assert is_office_open(test_time) is True

    def test_monday_after_fall_back(self) -> None:
        """Monday after fall DST transition - should work normally."""
        test_time = make_eastern_datetime(2024, 11, 4, 10, 0)  # Mon Nov 4
        assert is_office_open(test_time) is True

    def test_9am_after_spring_forward(self) -> None:
        """9 AM on day after spring forward should be open."""
        test_time = make_eastern_datetime(2024, 3, 11, 9, 0)
        assert is_office_open(test_time) is True

    def test_5pm_after_fall_back(self) -> None:
        """5 PM on day after fall back should be closed."""
        test_time = make_eastern_datetime(2024, 11, 4, 17, 0)
        assert is_office_open(test_time) is False


class TestYearBoundaryHandling:
    """Tests for year boundary handling (New Year's, etc.)."""

    def test_new_years_eve_afternoon(self) -> None:
        """December 31 afternoon - depends on day of week."""
        # 2024-12-31 is a Tuesday
        test_time = make_eastern_datetime(2024, 12, 31, 14, 0)  # Tuesday 2 PM
        assert is_office_open(test_time) is True

    def test_new_years_day_2025_morning(self) -> None:
        """January 1, 2025 morning - Wednesday, would be 'open' without holiday logic."""
        test_time = make_eastern_datetime(2025, 1, 1, 10, 0)  # Wednesday 10 AM
        # Without holiday awareness, this is a normal Wednesday
        assert is_office_open(test_time) is True

    def test_cross_year_get_next_open_friday_dec_31(self) -> None:
        """Friday Dec 31, 2021 at 6 PM -> Monday Jan 3, 2022."""
        # 2021-12-31 is a Friday
        test_time = make_eastern_datetime(2021, 12, 31, 18, 0)  # Friday 6 PM
        result = get_next_open_time(test_time)
        assert result == "Monday at 9 AM"


class TestTimezoneConsistency:
    """Tests to verify timezone handling is consistent."""

    def test_get_business_hours_context_uses_eastern(self) -> None:
        """Verify context string mentions ET timezone."""
        result = get_business_hours_context()
        assert "ET" in result["current_time"]


class TestIntegrationScenarios:
    """Integration tests that simulate real-world call scenarios."""

    def test_caller_during_business_hours(self) -> None:
        """Simulate a call during business hours - office should be open."""
        test_time = make_eastern_datetime(2024, 1, 9, 14, 30)  # Tuesday 2:30 PM

        assert is_office_open(test_time) is True

        context = get_business_hours_context(test_time)
        assert context["is_open"] is True
        assert context["next_open_time"] is None

        prompt = format_business_hours_prompt(test_time)
        assert "Open" in prompt

    def test_caller_after_hours_weekday(self) -> None:
        """Simulate a call after hours on a weekday."""
        test_time = make_eastern_datetime(2024, 1, 10, 19, 0)  # Wednesday 7 PM

        assert is_office_open(test_time) is False

        next_open = get_next_open_time(test_time)
        assert next_open == "tomorrow at 9 AM"

        context = get_business_hours_context(test_time)
        assert context["is_open"] is False
        assert context["next_open_time"] == "tomorrow at 9 AM"

        prompt = format_business_hours_prompt(test_time)
        assert "Closed" in prompt
        assert "tomorrow at 9 AM" in prompt

    def test_caller_on_weekend(self) -> None:
        """Simulate a call on the weekend."""
        test_time = make_eastern_datetime(2024, 1, 13, 14, 0)  # Saturday afternoon

        assert is_office_open(test_time) is False

        next_open = get_next_open_time(test_time)
        assert next_open == "Monday at 9 AM"

        context = get_business_hours_context(test_time)
        assert context["is_open"] is False
        assert context["next_open_time"] == "Monday at 9 AM"

        prompt = format_business_hours_prompt(test_time)
        assert "Closed" in prompt
        assert "Monday at 9 AM" in prompt

    def test_caller_early_morning_weekday(self) -> None:
        """Simulate a call early morning before office opens."""
        test_time = make_eastern_datetime(2024, 1, 11, 7, 30)  # Thursday 7:30 AM

        assert is_office_open(test_time) is False

        next_open = get_next_open_time(test_time)
        assert next_open == "later today at 9 AM"

    def test_caller_friday_evening(self) -> None:
        """Simulate a call on Friday evening - weekend ahead."""
        test_time = make_eastern_datetime(2024, 1, 12, 20, 0)  # Friday 8 PM

        assert is_office_open(test_time) is False

        next_open = get_next_open_time(test_time)
        assert next_open == "Monday at 9 AM"


class TestGetNextOpenTimeParameterized:
    """Parameterized tests for comprehensive get_next_open_time coverage."""

    @pytest.mark.parametrize(
        "day,hour,expected",
        [
            # Monday-Thursday after hours -> tomorrow
            (8, 18, "tomorrow at 9 AM"),  # Monday 6 PM
            (9, 19, "tomorrow at 9 AM"),  # Tuesday 7 PM
            (10, 20, "tomorrow at 9 AM"),  # Wednesday 8 PM
            (11, 21, "tomorrow at 9 AM"),  # Thursday 9 PM
            # Friday after 5 PM -> Monday
            (12, 17, "Monday at 9 AM"),  # Friday 5 PM
            (12, 18, "Monday at 9 AM"),  # Friday 6 PM
            (12, 23, "Monday at 9 AM"),  # Friday 11 PM
            # Saturday -> Monday
            (13, 0, "Monday at 9 AM"),  # Saturday midnight
            (13, 12, "Monday at 9 AM"),  # Saturday noon
            (13, 23, "Monday at 9 AM"),  # Saturday 11 PM
            # Sunday -> tomorrow (Monday)
            (14, 0, "tomorrow at 9 AM"),  # Sunday midnight
            (14, 12, "tomorrow at 9 AM"),  # Sunday noon
            (14, 23, "tomorrow at 9 AM"),  # Sunday 11 PM
        ],
    )
    def test_get_next_open_time_after_hours(
        self, day: int, hour: int, expected: str
    ) -> None:
        """Test various day/time scenarios for get_next_open_time."""
        test_time = make_eastern_datetime(2024, 1, day, hour, 0)
        result = get_next_open_time(test_time)
        assert result == expected


class TestIsOfficeOpenParameterized:
    """Parameterized tests for comprehensive is_office_open coverage."""

    @pytest.mark.parametrize(
        "day,hour,expected_open",
        [
            # Monday (8) - Open during business hours (except 12-1 PM lunch)
            (8, 8, False),  # 8 AM - before opening
            (8, 9, True),  # 9 AM - opening time
            (8, 12, False),  # 12 PM - lunch hour (closed)
            (8, 13, True),  # 1 PM - after lunch
            (8, 16, True),  # 4 PM - afternoon
            (8, 17, False),  # 5 PM - closing time
            (8, 18, False),  # 6 PM - after hours
            # Tuesday (9)
            (9, 9, True),
            (9, 17, False),
            # Wednesday (10)
            (10, 10, True),
            (10, 20, False),
            # Thursday (11)
            (11, 14, True),
            (11, 22, False),
            # Friday (12)
            (12, 9, True),
            (12, 16, True),
            (12, 17, False),
            # Saturday (13) - always closed
            (13, 9, False),
            (13, 12, False),
            (13, 17, False),
            # Sunday (14) - always closed
            (14, 9, False),
            (14, 12, False),
            (14, 17, False),
        ],
    )
    def test_is_office_open_scenarios(
        self, day: int, hour: int, expected_open: bool
    ) -> None:
        """Test various day/time scenarios for is_office_open."""
        test_time = make_eastern_datetime(2024, 1, day, hour, 0)
        result = is_office_open(test_time)
        assert result == expected_open, f"Failed for day {day} hour {hour}"
