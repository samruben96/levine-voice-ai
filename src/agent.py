"""Harry Levine Insurance Voice Agent - Backwards Compatibility Module.

This module serves as a thin wrapper to maintain backwards compatibility.
The actual implementation has been refactored into separate modules:

- models.py: CallerInfo, CallIntent, InsuranceType
- utils.py: mask_phone, mask_name, validate_phone, validate_environment
- constants.py: HOLD_MESSAGE, CARRIER_CLAIMS_NUMBERS, get_carrier_claims_number
- agents/: All specialized agent classes
- main.py: Server setup and entry point

For new code, prefer importing directly from the specific modules.
This file re-exports all public symbols for backwards compatibility.

Usage
-----
Development mode (auto-reload)::

    uv run python src/agent.py dev

Production mode::

    uv run python src/agent.py start

Interactive testing::

    uv run python src/agent.py console

Download required models::

    uv run python src/agent.py download-files
"""

# Re-export models
# Re-export all specialized agents
# Note: Many sub-agents were removed in the single-agent architecture simplification.
# The Assistant now handles most routing intents directly via transfer tools.
from agents import (
    AfterHoursAgent,
    Assistant,
    ClaimsAgent,
    MortgageeCertificateAgent,
)

# Re-export constants
from constants import (
    CARRIER_CLAIMS_NUMBERS,
    HOLD_MESSAGE,
    get_carrier_claims_number,
)

# Re-export server components
from main import my_agent, prewarm, request_fnc, server
from models import CallerInfo, CallIntent, InsuranceType

# Re-export utilities
from utils import mask_name, mask_phone, validate_environment, validate_phone

# Run the CLI when executed directly
if __name__ == "__main__":
    from livekit.agents import cli

    cli.run_app(server)


__all__ = [
    "CARRIER_CLAIMS_NUMBERS",
    "HOLD_MESSAGE",
    "AfterHoursAgent",
    "Assistant",
    "CallIntent",
    "CallerInfo",
    "ClaimsAgent",
    "InsuranceType",
    "MortgageeCertificateAgent",
    "get_carrier_claims_number",
    "mask_name",
    "mask_phone",
    "my_agent",
    "prewarm",
    "request_fnc",
    "server",
    "validate_environment",
    "validate_phone",
]
