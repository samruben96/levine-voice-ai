"""Business hours management for Harry Levine Insurance.

This module provides utilities for determining office hours, calculating
when the office will next be open, and generating context for LLM prompts.

Business Hours: Monday - Friday, 9:00 AM to 5:00 PM Eastern Time
Location: Orlando, Florida

Usage
-----
Basic usage::

    from business_hours import is_office_open, get_next_open_time

    if is_office_open():
        print("Office is open!")
    else:
        print(f"Office is closed. Reopens {get_next_open_time()}")

For LLM context injection::

    from business_hours import get_business_hours_context

    context = get_business_hours_context()
    # Use context["current_time"], context["is_open"], etc. in prompts

Testing with specific times::

    from datetime import datetime
    from zoneinfo import ZoneInfo

    # Test with a specific time
    test_time = datetime(2024, 1, 9, 10, 0, tzinfo=ZoneInfo("America/New_York"))
    is_open = is_office_open(now=test_time)  # True (Tuesday 10 AM)

See Also
--------
docs/OPERATIONS.md : Operational guide including business hours info
"""

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Final

try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Python < 3.9 compatibility
    from backports.zoneinfo import ZoneInfo  # type: ignore[import-not-found]


# =============================================================================
# CONFIGURATION
# =============================================================================

# Timezone for business operations
TIMEZONE: Final[str] = "America/New_York"

# Location information
LOCATION: Final[str] = "Florida"
OFFICE_ADDRESS: Final[str] = "7208 West Sand Lake Road, Suite 206, Orlando, FL 32819"

# Human-readable office hours string for prompts
OFFICE_HOURS_DISPLAY: Final[str] = (
    "Monday - Friday, 9 AM to 5 PM Eastern (closed 12-1 PM for lunch)"
)

# Lunch break times
LUNCH_START: Final[time] = time(12, 0)  # 12:00 PM
LUNCH_END: Final[time] = time(13, 0)  # 1:00 PM


@dataclass(frozen=True)
class DaySchedule:
    """Schedule for a single day.

    Attributes:
        open_time: Time the office opens (None if closed).
        close_time: Time the office closes (None if closed).
    """

    open_time: time | None
    close_time: time | None

    @property
    def is_closed(self) -> bool:
        """Return True if office is closed all day."""
        return self.open_time is None or self.close_time is None


# Default schedule: M-F 9 AM - 5 PM, closed weekends
# Days are indexed 0=Monday, 6=Sunday (matching datetime.weekday())
WEEKLY_SCHEDULE: Final[dict[int, DaySchedule]] = {
    0: DaySchedule(time(9, 0), time(17, 0)),  # Monday
    1: DaySchedule(time(9, 0), time(17, 0)),  # Tuesday
    2: DaySchedule(time(9, 0), time(17, 0)),  # Wednesday
    3: DaySchedule(time(9, 0), time(17, 0)),  # Thursday
    4: DaySchedule(time(9, 0), time(17, 0)),  # Friday
    5: DaySchedule(None, None),  # Saturday - closed
    6: DaySchedule(None, None),  # Sunday - closed
}

# Day names for human-readable output
DAY_NAMES: Final[tuple[str, ...]] = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)

# TODO: Holiday support
# Future enhancement: Add holiday schedule support
# - Load holiday calendar (federal holidays, Florida state holidays)
# - Check for special hours (early close, etc.)
# - Consider client-specific closures
# Example structure:
# HOLIDAYS_2024 = {
#     datetime(2024, 1, 1).date(): "New Year's Day",
#     datetime(2024, 7, 4).date(): "Independence Day",
#     ...
# }


# =============================================================================
# TIMEZONE UTILITIES
# =============================================================================

# Cache the timezone object
_EASTERN_TZ: Final[ZoneInfo] = ZoneInfo(TIMEZONE)


def get_timezone() -> ZoneInfo:
    """Get the Eastern timezone object.

    Returns:
        ZoneInfo object for America/New_York.

    Example:
        >>> tz = get_timezone()
        >>> str(tz)
        'America/New_York'
    """
    return _EASTERN_TZ


def get_current_time() -> datetime:
    """Get the current time in Eastern timezone.

    Returns:
        Current datetime in America/New_York timezone.

    Example:
        >>> now = get_current_time()
        >>> now.tzinfo is not None
        True
    """
    return datetime.now(_EASTERN_TZ)


# =============================================================================
# CORE BUSINESS HOURS FUNCTIONS
# =============================================================================


def is_office_open(now: datetime | None = None) -> bool:
    """Check if the office is currently open for business.

    Business hours: Monday-Friday, 9:00 AM to 5:00 PM Eastern Time.
    The office is considered open at exactly 9:00 AM and closed at exactly 5:00 PM.

    Args:
        now: Optional datetime for testing. If None, uses current Eastern time.
             If provided, the datetime should ideally be timezone-aware.
             Naive datetimes are treated as if in Eastern time.

    Returns:
        True if currently within business hours, False otherwise.

    Examples:
        >>> from datetime import datetime
        >>> from zoneinfo import ZoneInfo
        >>> et = ZoneInfo("America/New_York")

        >>> # Tuesday at 10 AM - open
        >>> is_office_open(datetime(2024, 1, 9, 10, 0, tzinfo=et))
        True

        >>> # Tuesday at 8 PM - closed
        >>> is_office_open(datetime(2024, 1, 9, 20, 0, tzinfo=et))
        False

        >>> # Saturday at 10 AM - closed
        >>> is_office_open(datetime(2024, 1, 13, 10, 0, tzinfo=et))
        False

        >>> # Wednesday at exactly 9 AM - open
        >>> is_office_open(datetime(2024, 1, 10, 9, 0, 0, tzinfo=et))
        True

        >>> # Thursday at exactly 5 PM - closed
        >>> is_office_open(datetime(2024, 1, 11, 17, 0, 0, tzinfo=et))
        False

    Note:
        Holiday schedule is not currently implemented. See TODO for future plans.
    """
    if now is None:
        now = get_current_time()
    elif now.tzinfo is None:
        # Treat naive datetime as Eastern time
        now = now.replace(tzinfo=_EASTERN_TZ)
    else:
        # Convert to Eastern time if in different timezone
        now = now.astimezone(_EASTERN_TZ)

    # Get schedule for today
    day_of_week = now.weekday()
    schedule = WEEKLY_SCHEDULE.get(day_of_week)

    if schedule is None or schedule.is_closed:
        return False

    # Extract current time
    current_time = now.time()

    # Office is open: open_time <= current_time < close_time
    # At exactly 5:00 PM, office is closed
    assert schedule.open_time is not None  # Type narrowing
    assert schedule.close_time is not None

    # Check if it's lunch hour (12-1 PM on weekdays)
    if LUNCH_START <= current_time < LUNCH_END:
        return False

    return schedule.open_time <= current_time < schedule.close_time


def is_lunch_hour(now: datetime | None = None) -> bool:
    """Check if it's currently lunch hour (12:00 PM - 1:00 PM Eastern).

    Args:
        now: Optional datetime for testing. If None, uses current Eastern time.

    Returns:
        True if currently during lunch hour on a weekday, False otherwise.

    Examples:
        >>> from datetime import datetime
        >>> from zoneinfo import ZoneInfo
        >>> et = ZoneInfo("America/New_York")
        >>> is_lunch_hour(datetime(2024, 1, 9, 12, 30, tzinfo=et))  # Tuesday 12:30 PM
        True
        >>> is_lunch_hour(datetime(2024, 1, 9, 11, 30, tzinfo=et))  # Tuesday 11:30 AM
        False
    """
    if now is None:
        now = get_current_time()
    elif now.tzinfo is None:
        now = now.replace(tzinfo=_EASTERN_TZ)
    else:
        now = now.astimezone(_EASTERN_TZ)

    # Only lunch on weekdays
    if now.weekday() >= 5:  # Saturday=5, Sunday=6
        return False

    current_time = now.time()
    return LUNCH_START <= current_time < LUNCH_END


def get_next_open_time(now: datetime | None = None) -> str:
    """Get a human-friendly string describing when the office reopens.

    Calculates when the office will next be open and returns a natural
    language string suitable for telling callers.

    Args:
        now: Optional datetime for testing. If None, uses current Eastern time.

    Returns:
        Human-friendly string like:
        - "tomorrow at 9 AM" (if reopening the next day)
        - "Monday at 9 AM" (if reopening on a specific weekday)
        - "in about 30 minutes" (if reopening soon, within 60 minutes)
        - "later today at 9 AM" (if before opening time on a business day)

    Examples:
        >>> from datetime import datetime
        >>> from zoneinfo import ZoneInfo
        >>> et = ZoneInfo("America/New_York")

        >>> # Friday evening - reopens Monday
        >>> get_next_open_time(datetime(2024, 1, 12, 18, 0, tzinfo=et))
        'Monday at 9 AM'

        >>> # Saturday - reopens Monday
        >>> get_next_open_time(datetime(2024, 1, 13, 10, 0, tzinfo=et))
        'Monday at 9 AM'

        >>> # Monday evening - reopens tomorrow
        >>> get_next_open_time(datetime(2024, 1, 8, 18, 0, tzinfo=et))
        'tomorrow at 9 AM'

        >>> # Wednesday at 8:30 AM - opens soon
        >>> get_next_open_time(datetime(2024, 1, 10, 8, 30, tzinfo=et))
        'in about 30 minutes'

        >>> # Tuesday at 7 AM - opens later today
        >>> get_next_open_time(datetime(2024, 1, 9, 7, 0, tzinfo=et))
        'later today at 9 AM'

    Note:
        If the office is currently open, this still calculates the next
        opening time (useful for edge cases).
    """
    if now is None:
        now = get_current_time()
    elif now.tzinfo is None:
        now = now.replace(tzinfo=_EASTERN_TZ)
    else:
        now = now.astimezone(_EASTERN_TZ)

    # Find the next opening datetime
    next_open = _find_next_opening(now)

    # Calculate the difference
    delta = next_open - now

    # Determine appropriate phrasing
    if delta.total_seconds() <= 0:
        # Edge case: currently open or exactly at opening
        return "now"

    # Check if it's within the next hour
    if delta.total_seconds() <= 3600:  # 60 minutes
        minutes = int(delta.total_seconds() / 60)
        if minutes <= 1:
            return "in about a minute"
        return f"in about {minutes} minutes"

    # Check if it's later today (same calendar day, before opening)
    if next_open.date() == now.date():
        return "later today at 9 AM"

    # Check if it's tomorrow
    tomorrow = now.date() + timedelta(days=1)
    if next_open.date() == tomorrow:
        return "tomorrow at 9 AM"

    # Otherwise, use the day name
    day_name = DAY_NAMES[next_open.weekday()]
    return f"{day_name} at 9 AM"


def _find_next_opening(now: datetime) -> datetime:
    """Find the next datetime when the office opens.

    Internal helper function that calculates the exact datetime of
    the next office opening.

    Args:
        now: Current datetime (timezone-aware, in Eastern time).

    Returns:
        Datetime of next opening time.
    """
    current_date = now.date()

    # Check up to 7 days ahead (covers full week + safety margin)
    for days_ahead in range(8):
        check_date = current_date + timedelta(days=days_ahead)
        check_weekday = check_date.weekday()
        schedule = WEEKLY_SCHEDULE.get(check_weekday)

        if schedule is None or schedule.is_closed:
            continue

        assert schedule.open_time is not None  # Type narrowing

        # Create opening datetime for this day
        opening_dt = datetime.combine(
            check_date, schedule.open_time, tzinfo=_EASTERN_TZ
        )

        # If this is today, check if opening time is in the future
        if days_ahead == 0:
            if opening_dt > now:
                return opening_dt
            # If we're past opening but before closing, still return this opening
            # (for edge cases where caller asks while office is open)
            if schedule.close_time is not None:
                closing_dt = datetime.combine(
                    check_date, schedule.close_time, tzinfo=_EASTERN_TZ
                )
                if now < closing_dt:
                    return opening_dt
            # Otherwise, continue to next day
            continue

        return opening_dt

    # Fallback (should never reach here with valid schedule)
    return datetime.combine(
        current_date + timedelta(days=1), time(9, 0), tzinfo=_EASTERN_TZ
    )


# =============================================================================
# LLM CONTEXT GENERATION
# =============================================================================


def get_business_hours_context(
    now: datetime | None = None,
) -> dict[str, str | bool | None]:
    """Get context dictionary for injection into LLM prompts.

    Generates a dictionary with current time information, office status,
    and formatted strings suitable for including in agent prompts.

    Args:
        now: Optional datetime for testing. If None, uses current Eastern time.

    Returns:
        Dictionary with the following keys:
        - current_time: Formatted current time string (e.g., "3:45 PM ET, Tuesday, January 14")
        - is_open: Boolean indicating if office is currently open
        - next_open_time: When office reopens (None if currently open)
        - office_hours: Human-readable office hours string

    Examples:
        >>> from datetime import datetime
        >>> from zoneinfo import ZoneInfo
        >>> et = ZoneInfo("America/New_York")

        >>> # During business hours
        >>> ctx = get_business_hours_context(datetime(2024, 1, 9, 14, 30, tzinfo=et))
        >>> ctx["is_open"]
        True
        >>> ctx["next_open_time"] is None
        True
        >>> "2:30 PM" in ctx["current_time"]
        True

        >>> # After hours
        >>> ctx = get_business_hours_context(datetime(2024, 1, 9, 20, 0, tzinfo=et))
        >>> ctx["is_open"]
        False
        >>> ctx["next_open_time"]
        'tomorrow at 9 AM'
    """
    if now is None:
        now = get_current_time()
    elif now.tzinfo is None:
        now = now.replace(tzinfo=_EASTERN_TZ)
    else:
        now = now.astimezone(_EASTERN_TZ)

    is_open = is_office_open(now)

    # Format current time: "3:45 PM ET, Tuesday, January 14"
    current_time = _format_current_time(now)

    # Calculate next opening time if closed
    next_open = None if is_open else get_next_open_time(now)

    return {
        "current_time": current_time,
        "is_open": is_open,
        "next_open_time": next_open,
        "office_hours": OFFICE_HOURS_DISPLAY,
    }


def _format_current_time(now: datetime) -> str:
    """Format datetime as human-readable time string.

    Args:
        now: Datetime to format.

    Returns:
        Formatted string like "3:45 PM ET, Tuesday, January 14"
    """
    # Format: "3:45 PM ET, Tuesday, January 14"
    time_str = now.strftime("%-I:%M %p").lstrip("0")  # "3:45 PM"
    day_name = DAY_NAMES[now.weekday()]
    month_day = now.strftime("%B %-d")  # "January 14"

    return f"{time_str} ET, {day_name}, {month_day}"


def format_business_hours_prompt(now: datetime | None = None) -> str:
    """Generate a formatted business hours string for LLM prompt injection.

    This generates a context block suitable for including in agent instructions,
    providing the LLM with current time and office status information.

    Args:
        now: Optional datetime for testing. If None, uses current Eastern time.

    Returns:
        Formatted string for inclusion in agent instructions.

    Examples:
        >>> from datetime import datetime
        >>> from zoneinfo import ZoneInfo
        >>> et = ZoneInfo("America/New_York")

        >>> # During business hours
        >>> prompt = format_business_hours_prompt(datetime(2024, 1, 9, 14, 30, tzinfo=et))
        >>> "OFFICE STATUS: Open" in prompt
        True
        >>> "closes at 5 PM" in prompt
        True

        >>> # After hours
        >>> prompt = format_business_hours_prompt(datetime(2024, 1, 9, 20, 0, tzinfo=et))
        >>> "OFFICE STATUS: Closed" in prompt
        True
        >>> "reopens tomorrow" in prompt
        True
    """
    if now is None:
        now = get_current_time()
    elif now.tzinfo is None:
        now = now.replace(tzinfo=_EASTERN_TZ)
    else:
        now = now.astimezone(_EASTERN_TZ)

    # Format current time: "3:45 PM ET, Tuesday"
    time_str = now.strftime("%-I:%M %p").lstrip("0")
    day_str = DAY_NAMES[now.weekday()]
    current_time = f"{time_str} ET, {day_str}"

    # Determine office status
    is_open = is_office_open(now)

    if is_open:
        status = "Open (closes at 5 PM)"
    else:
        next_open = get_next_open_time(now)
        status = f"Closed (reopens {next_open})"

    return f"""CURRENT TIME: {current_time}
OFFICE STATUS: {status}"""


# =============================================================================
# CONVENIENCE EXPORTS
# =============================================================================

__all__ = [
    "LOCATION",
    "LUNCH_END",
    "LUNCH_START",
    "OFFICE_ADDRESS",
    "OFFICE_HOURS_DISPLAY",
    "TIMEZONE",
    "WEEKLY_SCHEDULE",
    "DaySchedule",
    "format_business_hours_prompt",
    "get_business_hours_context",
    "get_current_time",
    "get_next_open_time",
    "get_timezone",
    "is_lunch_hour",
    "is_office_open",
]
