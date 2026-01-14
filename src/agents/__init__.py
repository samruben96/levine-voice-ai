"""Agent modules for the Harry Levine Insurance Voice Agent.

This package contains specialized agents for different conversation flows:

- Assistant: Main front-desk receptionist (entry point) - handles most intents
  directly via transfer tools (quote, payment, change, cancellation, coverage)
- ClaimsAgent: Claims filing with business hours vs after-hours carrier lookup
- MortgageeCertificateAgent: Certificate of insurance and mortgagee requests
  (redirects to email/self-service, no transfer)
- AfterHoursAgent: After-hours voicemail flow for non-claims requests

Note: The Assistant now uses direct transfer tools instead of sub-agent handoffs
for most routing intents. This eliminates double-asking of questions.
"""

from agents.after_hours import AfterHoursAgent
from agents.assistant import Assistant
from agents.claims import ClaimsAgent
from agents.mortgagee import MortgageeCertificateAgent

__all__ = [
    "AfterHoursAgent",
    "Assistant",
    "ClaimsAgent",
    "MortgageeCertificateAgent",
]
