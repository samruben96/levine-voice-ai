"""Utility functions for the Harry Levine Insurance Voice Agent.

This module contains helper functions for:
- PII masking (for secure logging)
- Phone number validation
- Environment variable validation
- Structured routing decision logging
"""

from __future__ import annotations

import logging
import os
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import CallIntent, InsuranceType

logger = logging.getLogger("agent")

# =============================================================================
# ENVIRONMENT VALIDATION
# =============================================================================

REQUIRED_ENV = ["LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET"]


def validate_environment() -> None:
    """Validate required environment variables are set.

    Checks that all required LiveKit environment variables are present.

    Raises:
        RuntimeError: If any required environment variables are missing.

    Example:
        >>> validate_environment()  # Raises RuntimeError if LIVEKIT_URL not set
    """
    missing = [v for v in REQUIRED_ENV if not os.getenv(v)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {missing}")


# =============================================================================
# PII MASKING UTILITIES
# =============================================================================


def mask_phone(phone: str) -> str:
    """Mask phone number for logging, showing only last 4 digits.

    Args:
        phone: The phone number to mask.

    Returns:
        Masked phone number showing only last 4 digits.

    Examples:
        >>> mask_phone("555-123-4567")
        '***-***-4567'
        >>> mask_phone("123")
        '***'
    """
    return "***-***-" + phone[-4:] if phone and len(phone) >= 4 else "***"


def mask_name(name: str) -> str:
    """Mask name for logging, showing only first character.

    Args:
        name: The name to mask.

    Returns:
        Masked name showing only first character.

    Examples:
        >>> mask_name("John Smith")
        'J*********'
        >>> mask_name("")
        '***'
    """
    return name[0] + "*" * (len(name) - 1) if name else "***"


def mask_email(email: str | None) -> str:
    """Mask email for logging, showing only first character and domain.

    Args:
        email: Email address to mask, or None

    Returns:
        Masked email like "j***@example.com" or "***" if invalid/empty

    Examples:
        >>> mask_email("john.smith@example.com")
        'j***@example.com'
        >>> mask_email("")
        '***'
        >>> mask_email(None)
        '***'
    """
    if not email or "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    return f"{local[0]}***@{domain}" if local else f"***@{domain}"


# =============================================================================
# PHONE VALIDATION
# =============================================================================


def format_email_for_speech(email: str) -> str:
    """Format email for TTS with spelling.

    Example: 'info@hlinsure.com' -> 'info@hlinsure.com. That's I-N-F-O at H-L-I-N-S-U-R-E dot com.'
    """
    if not email or "@" not in email:
        return email
    local, domain = email.split("@")
    domain_name, tld = domain.rsplit(".", 1)
    local_spelled = "-".join(local.upper())
    domain_spelled = "-".join(domain_name.upper())
    return f"{email}. That's {local_spelled} at {domain_spelled} dot {tld}."


def validate_phone(phone: str) -> tuple[bool, str]:
    """Validate and normalize a phone number.

    Strips non-digit characters and validates the length is between
    10 and 15 digits (supporting both US numbers and international formats).

    Args:
        phone: The phone number to validate.

    Returns:
        Tuple of (is_valid, normalized_digits).
        If valid, normalized_digits contains only the numeric digits.
        If invalid, normalized_digits contains the original phone string.

    Examples:
        >>> validate_phone("555-123-4567")
        (True, '5551234567')
        >>> validate_phone("+1 (555) 123-4567")
        (True, '15551234567')
        >>> validate_phone("123")
        (False, '123')
        >>> validate_phone("")
        (False, '')
    """
    if not phone:
        return False, ""
    digits = re.sub(r"[^\d]", "", phone)
    if 10 <= len(digits) <= 15:
        return True, digits
    return False, phone


# =============================================================================
# STRUCTURED ROUTE DECISION LOGGING
# =============================================================================


def log_route_decision(
    intent: CallIntent | str | None,
    agent: str | None,
    insurance_type: InsuranceType | None,
    identifier: str | None,
    destination: str,
    *,
    is_personal: bool = False,
) -> None:
    """Log a structured ROUTE_DECISION event for debugging routing decisions.

    This function creates standardized log entries for all routing decisions,
    enabling consistent debugging and analysis of call routing behavior.

    The log format is:
        ROUTE_DECISION: intent=<call_intent> | agent=<assigned_agent> |
                       insurance_type=<type> | identifier=<masked_identifier> |
                       destination=<destination_type>

    Args:
        intent: The detected call intent (CallIntent enum or string).
        agent: The assigned agent name (may be None if routing to ring group).
        insurance_type: Business or personal insurance type.
        identifier: The routing identifier (business name or last name).
                   Will be masked if is_personal=True.
        destination: Description of where the call is being routed
                    (e.g., "transfer", "handoff:ClaimsAgent", "ring_group:VA").
        is_personal: If True, the identifier is a personal name and will be masked.
                    Business names are not masked.

    Example:
        >>> log_route_decision(
        ...     intent=CallIntent.NEW_QUOTE,
        ...     agent="Rachel Moreno",
        ...     insurance_type=InsuranceType.PERSONAL,
        ...     identifier="Smith",
        ...     destination="transfer",
        ...     is_personal=True,
        ... )
        # Logs: ROUTE_DECISION: intent=new_quote | agent=Rachel Moreno |
        #       insurance_type=personal | identifier=S**** | destination=transfer
    """
    # Convert enums to string values
    # Use hasattr instead of isinstance because the import path may differ
    # (e.g., src.models vs models), which creates different class objects
    intent_str = intent.value if hasattr(intent, "value") else (intent or "None")
    type_str = insurance_type.value if hasattr(insurance_type, "value") else "None"

    # Mask personal identifiers (last names) but not business names
    if identifier and is_personal:
        masked_id = mask_name(identifier)
    else:
        masked_id = identifier or "None"

    logger.info(
        f"ROUTE_DECISION: intent={intent_str} | agent={agent or 'None'} | "
        f"insurance_type={type_str} | identifier={masked_id} | destination={destination}"
    )
