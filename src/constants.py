"""Constants and configuration for the Harry Levine Insurance Voice Agent.

This module contains:
- Hold messages
- Carrier claims phone numbers
- Carrier lookup utility function
"""

# =============================================================================
# HOLD MESSAGE CONFIGURATION
# =============================================================================

HOLD_MESSAGE = "One moment while I connect you."


# =============================================================================
# CARRIER CLAIMS NUMBERS CONFIGURATION
# =============================================================================

CARRIER_CLAIMS_NUMBERS: dict[str, str] = {
    # ==========================================================================
    # NOTE: These numbers are PLACEHOLDERS for development/testing.
    # TODO (Needs Client Input): Verify all carrier claims numbers before
    # production deployment. Numbers marked with "# Placeholder" are fake.
    # ==========================================================================
    #
    # National carriers (numbers appear valid but should be verified)
    "Progressive": "1-800-776-4737",
    "Travelers": "1-800-252-4633",
    "Hartford": "1-800-243-5860",
    "Liberty Mutual": "1-800-225-2467",
    "State Farm": "1-800-732-5246",
    "Allstate": "1-800-255-7828",
    "GEICO": "1-800-841-3000",
    "Nationwide": "1-800-421-3535",
    "USAA": "1-800-531-8722",
    "Farmers": "1-800-435-7764",
    "American Family": "1-800-692-6326",
    "Auto-Owners": "1-800-346-0346",
    "Erie": "1-800-367-3743",
    "Safeco": "1-800-332-3226",
    # TODO (HIGH PRIORITY - Needs Client Input): Add real claims numbers for Florida
    # regional carriers: Citizens, Florida Peninsula, Universal Property, Tower Hill,
    # Heritage, People's Trust, Security First. These are critical for this FL agency.
}


def get_carrier_claims_number(carrier_name: str) -> str | None:
    """Look up the claims phone number for an insurance carrier.

    Performs case-insensitive lookup with partial matching support.
    The lookup first tries an exact match (case-insensitive), then
    falls back to partial prefix matching.

    Args:
        carrier_name: The name of the insurance carrier (case-insensitive).

    Returns:
        The carrier's claims phone number, or None if not found.

    Examples:
        >>> get_carrier_claims_number("Progressive")
        '1-800-776-4737'
        >>> get_carrier_claims_number("progressive")
        '1-800-776-4737'
        >>> get_carrier_claims_number("Liberty")
        '1-800-225-2467'
        >>> get_carrier_claims_number("Unknown Carrier")
        None
    """
    if not carrier_name:
        return None

    carrier_lower = carrier_name.lower().strip()

    # First pass: exact match (case-insensitive)
    for name, number in CARRIER_CLAIMS_NUMBERS.items():
        if name.lower() == carrier_lower:
            return number

    # Second pass: partial prefix match
    for name, number in CARRIER_CLAIMS_NUMBERS.items():
        if name.lower().startswith(carrier_lower):
            return number

    # Third pass: search term is prefix of carrier name
    for name, number in CARRIER_CLAIMS_NUMBERS.items():
        if carrier_lower in name.lower():
            return number

    return None
