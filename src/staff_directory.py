"""Staff directory configuration and routing logic for Harry Levine Insurance.

This module provides the staff directory data and routing helper functions
for call transfer decisions in the voice agent.

Routing Rules:
--------------

1. Commercial Lines (CL) Alpha-Split Routing:
   - New business AND existing client inquiries are handled by CL Account Executives
   - Routing is based on the BUSINESS NAME's first letter (after handling exceptions)
   - Alpha ranges: A-F (Adriana), G-O (Rayvon), P-Z (Dionna)
   - Platinum clients go to Rachel T. (CL Department Manager)

2. Personal Lines (PL) Routing:
   - NEW business goes to PL Sales Agents: Queens (A-L), Brad (M-Z)
   - EXISTING clients go to PL Account Executives: Yarislyn (A-G), Al (H-M), Luis (N-Z)
   - The routing is based on the caller's last name first letter

3. Alpha Exception Prefixes:
   - If business name starts with "The", use the NEXT word for routing
   - If business name starts with "Law office of" or "Law offices of", use the NEXT word
   - Example: "The Great Company" routes on "G", not "T"
   - Example: "Law Offices of Harry Levine" routes on "H", not "L"

4. Restricted Transfers:
   - Jason L. and Fred cannot receive direct AI transfers
   - These staff members require a live person to answer first
   - Check is_transferable() before initiating any transfer

5. Time Blocks:
   - Some agents have designated time blocks (e.g., "9:00-10:00")
   - "L" suffix indicates lunch period (e.g., "12:00-1:00 L")
   - Consider time blocks for transfer availability
"""

from __future__ import annotations

from datetime import datetime
from typing import TypedDict


class StaffMember(TypedDict, total=False):
    """Type definition for a staff member entry."""

    department: str
    name: str
    assigned: str
    ext: str
    timeBlock: str | None
    transferable: bool


class RingGroup(TypedDict):
    """Type definition for a ring group configuration."""

    name: str
    extensions: list[str]
    description: str


class StaffDirectoryConfig(TypedDict):
    """Type definition for the complete staff directory configuration."""

    staff: list[StaffMember]
    restrictedTransfers: list[str]
    alphaExceptionPrefixes: list[str]
    ringGroups: dict[str, RingGroup]


STAFF_DIRECTORY: StaffDirectoryConfig = {
    "staff": [
        {
            "department": "Agency Support",
            "name": "Anamer L.",
            "assigned": "Agency Support",
            "ext": "7013",
            "timeBlock": "12:00-1:00 L",
        },
        {
            "department": "CL-Account Executive",
            "name": "Adriana",
            "assigned": "A-F",
            "ext": "7002",
            "timeBlock": "1:00-2:00",
        },
        {
            "department": "CL-Account Executive",
            "name": "Rayvon",
            "assigned": "G-O",
            "ext": "7018",
            "timeBlock": "9:00-10:00",
        },
        {
            "department": "CL-Account Executive",
            "name": "Dionna",
            "assigned": "P-Z",
            "ext": "7006",
            "timeBlock": "2:00-3:00",
        },
        {
            "department": "CL-Department Manager",
            "name": "Rachel T.",
            "assigned": "Platinum",
            "ext": "7005",
            "timeBlock": "1:00-2:00",
        },
        {
            "department": "CL-Producer",
            "name": "Kevin K.",
            "assigned": "Producer",
            "ext": "7003",
            "timeBlock": None,
        },
        {
            "department": "CL-Service",
            "name": "Stephanie",
            "assigned": "CSR",
            "ext": "7014",
            "timeBlock": "2:00-3:00 L",
        },
        {
            "department": "Management",
            "name": "Julie L.",
            "assigned": "Manager, Admin",
            "ext": "7001",
            "timeBlock": None,
            "transferable": True,
        },
        {
            "department": "Management",
            "name": "Jason L.",
            "assigned": "Manager, General",
            "ext": "7000",
            "timeBlock": None,
            "transferable": False,
        },
        {
            "department": "Management",
            "name": "Kelly U.",
            "assigned": "Manager, Operations",
            "ext": "7009",
            "timeBlock": "4:00-5:00",
        },
        {
            "department": "PL-Account Executive",
            "name": "Yarislyn",
            "assigned": "A-G",
            "ext": "7011",
            "timeBlock": "11:00-12:00",
        },
        {
            "department": "PL-Account Executive",
            "name": "Al",
            "assigned": "H-M",
            "ext": "7015",
            "timeBlock": "9:00-10:00",
        },
        {
            "department": "PL-Account Executive",
            "name": "Luis",
            "assigned": "N-Z",
            "ext": "7017",
            "timeBlock": "10:00-11:00",
        },
        {
            "department": "PL-Sales Agent",
            "name": "Queens",
            "assigned": "A-L",
            "ext": "7010",
            "timeBlock": None,
        },
        {
            "department": "PL-Sales Agent",
            "name": "Brad",
            "assigned": "M-Z",
            "ext": "7007",
            "timeBlock": None,
        },
        {
            "department": "PL-Service",
            "name": "Ann",
            "assigned": "CSR",
            "ext": "7016",
            "timeBlock": "1:00-2:00 L",
        },
        {
            "department": "PL-Service",
            "name": "Sheree",
            "assigned": "CSR",
            "ext": "7008",
            "timeBlock": "2:00-3:00 L",
        },
        {
            "department": "PL-Special Projects",
            "name": "Fred",
            "assigned": "",
            "ext": "7012",
            "timeBlock": None,
            "transferable": False,
        },
    ],
    "restrictedTransfers": ["Jason L.", "Fred"],
    "alphaExceptionPrefixes": ["The", "Law office of", "Law offices of"],
    "ringGroups": {
        "VA": {
            "name": "Virtual Assistant Team",
            "extensions": ["7016", "7008"],  # Ann and Sheree (PL-Service CSRs)
            "description": "Payment and ID/Dec requests",
        },
    },
}


# Alpha exception prefixes in lowercase for case-insensitive matching
_ALPHA_EXCEPTION_PREFIXES_LOWER: list[str] = [
    prefix.lower() for prefix in STAFF_DIRECTORY["alphaExceptionPrefixes"]
]


def get_alpha_route_key(business_name: str) -> str:
    """Extract the routing letter from a business name.

    Handles exception prefixes by skipping them to find the actual routing word.

    Args:
        business_name: The name of the business to route.

    Returns:
        The uppercase letter to use for alpha-split routing.

    Examples:
        >>> get_alpha_route_key("Acme Corporation")
        'A'
        >>> get_alpha_route_key("The Great Company")
        'G'
        >>> get_alpha_route_key("Law Offices of Harry Levine")
        'H'
        >>> get_alpha_route_key("law office of Smith & Associates")
        'S'
    """
    if not business_name or not business_name.strip():
        return "A"  # Default fallback

    name_lower = business_name.lower().strip()
    words = business_name.strip().split()

    # Check each exception prefix
    for prefix in _ALPHA_EXCEPTION_PREFIXES_LOWER:
        if name_lower.startswith(prefix):
            # Count words in the prefix to skip
            prefix_word_count = len(prefix.split())
            if len(words) > prefix_word_count:
                # Return first letter of the word after the prefix
                return words[prefix_word_count][0].upper()
            # If no word after prefix, use the prefix's first letter
            break

    # Default: use first letter of the business name
    return words[0][0].upper()


def _letter_in_range(letter: str, range_str: str) -> bool:
    """Check if a letter falls within an alpha range like 'A-F' or 'H-M'.

    Args:
        letter: Single uppercase letter to check.
        range_str: Range string in format 'X-Y' (e.g., 'A-F', 'G-O').

    Returns:
        True if letter falls within the range, False otherwise.
    """
    if "-" not in range_str:
        return False

    parts = range_str.split("-")
    if len(parts) != 2:
        return False

    start, end = parts[0].upper(), parts[1].upper()
    letter_upper = letter.upper()

    return start <= letter_upper <= end


def find_agent_by_alpha(
    letter: str, department: str, is_new_business: bool = False
) -> StaffMember | None:
    """Find the appropriate agent based on alpha routing rules.

    Args:
        letter: The routing letter (uppercase).
        department: Either "PL" (Personal Lines) or "CL" (Commercial Lines).
        is_new_business: Whether this is a new business inquiry.
            - For PL: True -> Sales Agents, False -> Account Executives
            - For CL: Account Executives handle BOTH new and existing

    Returns:
        The matching staff member dict, or None if no match found.

    Examples:
        >>> # Personal Lines, new business, last name starts with 'B'
        >>> agent = find_agent_by_alpha("B", "PL", is_new_business=True)
        >>> agent["name"] if agent else None
        'Queens'

        >>> # Personal Lines, existing client, last name starts with 'S'
        >>> agent = find_agent_by_alpha("S", "PL", is_new_business=False)
        >>> agent["name"] if agent else None
        'Luis'

        >>> # Commercial Lines, business name starts with 'H'
        >>> agent = find_agent_by_alpha("H", "CL", is_new_business=True)
        >>> agent["name"] if agent else None
        'Rayvon'
    """
    letter_upper = letter.upper()
    department_upper = department.upper()

    # Determine which department type to search for
    if department_upper == "PL":
        # Personal Lines
        if is_new_business:
            target_department = "PL-Sales Agent"
        else:
            target_department = "PL-Account Executive"
    elif department_upper == "CL":
        # Commercial Lines - Account Executives handle both new and existing
        target_department = "CL-Account Executive"
    else:
        return None

    # Search for matching agent
    for staff in STAFF_DIRECTORY["staff"]:
        if staff["department"] == target_department:
            assigned = staff.get("assigned", "")
            if _letter_in_range(letter_upper, assigned):
                return staff

    return None


def is_agent_available(agent: StaffMember) -> bool:
    """Check if an agent is currently available based on their time block.

    Time blocks indicate when agents are unavailable (meetings, etc.).
    "L" suffix indicates lunch period.

    Time blocks use 12-hour format without AM/PM (business hours assumed).
    Hours 1-6 are assumed to be PM (13:00-18:00).
    Hours 7-12 are kept as-is (morning through noon).

    Args:
        agent: The staff member to check.

    Returns:
        True if the agent is available, False if in their time block.
    """
    time_block = agent.get("timeBlock")
    if not time_block:
        return True  # No time block means always available

    # Parse the time block (e.g., "9:00-10:00", "12:00-1:00 L")
    time_block = time_block.replace(" L", "").strip()  # Remove lunch indicator

    if "-" not in time_block:
        return True

    try:
        start_str, end_str = time_block.split("-")
        now = datetime.now()

        # Parse start time
        start_parts = start_str.strip().split(":")
        start_hour = int(start_parts[0])
        start_minute = int(start_parts[1]) if len(start_parts) > 1 else 0

        # Parse end time
        end_parts = end_str.strip().split(":")
        end_hour = int(end_parts[0])
        end_minute = int(end_parts[1]) if len(end_parts) > 1 else 0

        # Convert 12-hour format to 24-hour format
        # Business hours: assume 1-6 are PM (13:00-18:00)
        if 1 <= start_hour <= 6:
            start_hour += 12
        if 1 <= end_hour <= 6:
            end_hour += 12

        # Convert to today's datetime for comparison
        start_time = now.replace(
            hour=start_hour, minute=start_minute, second=0, microsecond=0
        )
        end_time = now.replace(
            hour=end_hour, minute=end_minute, second=0, microsecond=0
        )

        # Check if current time is within the blocked period
        return not (start_time <= now <= end_time)

    except (ValueError, IndexError):
        # If parsing fails, assume available
        return True


def get_available_agent_by_alpha(
    letter: str, department: str, is_new_business: bool = False
) -> StaffMember | None:
    """Find an available agent based on alpha routing rules.

    Like find_agent_by_alpha but also checks time block availability.

    Args:
        letter: The routing letter (uppercase).
        department: Either "PL" (Personal Lines) or "CL" (Commercial Lines).
        is_new_business: Whether this is a new business inquiry.

    Returns:
        The matching available staff member, or None if no available match.
    """
    agent = find_agent_by_alpha(letter, department, is_new_business)
    if agent and is_agent_available(agent):
        return agent
    return None


def is_transferable(agent_name: str) -> bool:
    """Check if an agent can receive direct AI transfers.

    Some staff members require a live person to answer first before
    the AI can transfer a call to them.

    Args:
        agent_name: The name of the agent to check.

    Returns:
        True if the agent can receive direct AI transfers, False otherwise.

    Examples:
        >>> is_transferable("Jason L.")
        False
        >>> is_transferable("Fred")
        False
        >>> is_transferable("Adriana")
        True
        >>> is_transferable("Julie L.")
        True
    """
    # Check the restricted transfers list first
    if agent_name in STAFF_DIRECTORY["restrictedTransfers"]:
        return False

    # Look up the agent and check their transferable field
    for staff in STAFF_DIRECTORY["staff"]:
        if staff["name"] == agent_name:
            # If transferable field is explicitly set, use it
            if "transferable" in staff:
                return staff["transferable"]
            # Default to True if not explicitly set
            return True

    # If agent not found, assume transferable (shouldn't happen in practice)
    return True


def get_agent_by_name(name: str) -> StaffMember | None:
    """Look up an agent by name with prefix matching support.

    Args:
        name: The name to search for (prefix match is OK).

    Returns:
        The matching staff member dict, or None if no match found.

    Examples:
        >>> agent = get_agent_by_name("Adriana")
        >>> agent["ext"] if agent else None
        '7002'

        >>> agent = get_agent_by_name("Rachel")
        >>> agent["department"] if agent else None
        'CL-Department Manager'

        >>> get_agent_by_name("Nonexistent")
        None
    """
    if not name:
        return None

    name_lower = name.lower().strip()

    # First pass: exact match
    for staff in STAFF_DIRECTORY["staff"]:
        if staff["name"].lower() == name_lower:
            return staff

    # Second pass: staff name starts with search term (prefix match)
    for staff in STAFF_DIRECTORY["staff"]:
        staff_name_lower = staff["name"].lower()
        if staff_name_lower.startswith(name_lower):
            return staff

    # Third pass: search term starts with staff first name (e.g., "Adriana Smith" matches "Adriana")
    for staff in STAFF_DIRECTORY["staff"]:
        staff_first_name = staff["name"].split()[0].lower()
        if name_lower.startswith(staff_first_name):
            return staff

    return None


def get_agent_by_extension(ext: str) -> StaffMember | None:
    """Look up an agent by their extension number.

    Args:
        ext: The extension number to search for.

    Returns:
        The matching staff member dict, or None if no match found.

    Examples:
        >>> agent = get_agent_by_extension("7002")
        >>> agent["name"] if agent else None
        'Adriana'

        >>> agent = get_agent_by_extension("7000")
        >>> agent["name"] if agent else None
        'Jason L.'

        >>> get_agent_by_extension("9999")
        None
    """
    if not ext:
        return None

    ext_stripped = ext.strip()

    for staff in STAFF_DIRECTORY["staff"]:
        if staff.get("ext") == ext_stripped:
            return staff

    return None


def get_agents_by_department(department: str) -> list[StaffMember]:
    """Get all agents in a specific department.

    Args:
        department: The department name to filter by (partial match supported).

    Returns:
        List of staff members in the department.

    Examples:
        >>> agents = get_agents_by_department("CL-Account Executive")
        >>> len(agents)
        3
        >>> agents = get_agents_by_department("Management")
        >>> len(agents)
        3
    """
    if not department:
        return []

    department_lower = department.lower().strip()

    return [
        staff
        for staff in STAFF_DIRECTORY["staff"]
        if department_lower in staff["department"].lower()
    ]


def get_ring_group(group_name: str) -> RingGroup | None:
    """Get a ring group configuration by name.

    Ring groups are collections of agents that can be called together
    for specific types of requests (e.g., payments, ID/Dec requests).

    Args:
        group_name: The name of the ring group (e.g., "VA").

    Returns:
        The ring group configuration dict, or None if not found.

    Examples:
        >>> group = get_ring_group("VA")
        >>> group["name"] if group else None
        'Virtual Assistant Team'
        >>> group = get_ring_group("VA")
        >>> group["extensions"] if group else None
        ['7016', '7008']
        >>> get_ring_group("Nonexistent")
        None
    """
    if not group_name:
        return None

    ring_groups = STAFF_DIRECTORY.get("ringGroups", {})
    return ring_groups.get(group_name)
