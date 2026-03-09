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

# Carrier claims numbers verified from client spreadsheet (2026-03-08)
# Format: "Carrier Name": "claims-phone-number"
CARRIER_CLAIMS_NUMBERS: dict[str, str] = {
    "AAA": "888-929-4222",
    "Allstate": "800-255-7828",
    "American Family": "800-692-6326",
    "American Integrity": "866-277-9871 x2050",
    "Amica Mutual": "800-242-6422",
    "ASI": "866-274-8765",
    "Auto Owners": "888-252-4626",
    "Bankers Insurance": "800-765-9700",
    "Bristol West": "888-888-0080",
    "Capitol Preferred": "888-388-2742",
    "Centauri": "866-896-5504",
    "CHUBB": "800-252-4670",
    "Citizens": "866-411-2742",
    "CNA": "877-262-2727",
    "Cypress": "877-560-5224",
    "Edison": "888-882-8822",
    "EMC Insurance": "800-362-2227",
    "Encompass": "800-588-7400",
    "Erie": "800-367-3743",
    "Farmers": "800-435-7764",
    "Federated National": "800-293-2532",
    "Florida Family": "888-486-4663",
    "Florida Peninsula": "877-994-8368",
    "Foremost": "800-527-3907",
    "Frontline": "877-744-5224",
    "GAINSCO": "866-455-9518",
    "GEICO": "800-841-3000",
    "Hartford": "800-243-5860",
    "Heritage": "855-415-7120",
    "Homeowners Choice": "866-324-3138",
    "Infinity": "800-334-1661",
    "Kemper": "866-536-7376",
    "Liberty Mutual": "800-225-2467",
    "Monarch": "888-527-3030",
    "National General": "800-325-1088",
    "Nationwide": "800-421-4243",
    "Olympus": "866-281-2242",
    "Pacific Indemnity": "800-452-2788",
    "People's Trust": "877-333-1230",
    "Progressive": "800-274-4499",
    "Safeco": "877-566-6001",
    "SafePoint": "855-252-4641",
    "Security First": "877-581-4862",
    "Slide Insurance": "855-754-3311",
    "Southern Oak": "877-900-2280",
    "State Farm": "800-732-5246",
    "Tower Hill CL": "800-342-3407 x6050",
    "Tower Hill PL": "800-342-3407",
    "Travelers CL": "800-238-6225",
    "Travelers PL": "877-878-2468",
    "USAA": "800-531-8722",
    "United Property": "866-755-2680",
    "Universal Insurance": "800-470-4052",
    "Universal Property": "800-470-0599",
    "UPC Insurance": "800-861-0220",
    "Velocity Risk": "844-822-2742",
    "Western World": "201-847-8600",
    "Weston": "866-296-3115",
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
