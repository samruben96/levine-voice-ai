"""Agent modules for the Harry Levine Insurance Voice Agent.

This package contains all specialized agents that handle different types
of caller requests:

- Assistant: Main front-desk receptionist (entry point)
- NewQuoteAgent: New insurance quote requests
- PaymentIDDecAgent: Payments and document requests (ID cards, dec pages)
- MakeChangeAgent: Policy change/modification requests
- CancellationAgent: Policy cancellation requests
- ClaimsAgent: Claims filing with business hours vs after-hours flow
- CoverageRateAgent: Coverage and rate questions
- SomethingElseAgent: Catch-all for miscellaneous requests
- MortgageeCertificateAgent: Certificate of insurance and mortgagee requests
- AfterHoursAgent: After-hours voicemail flow

WARNING: To avoid circular imports, sub-agents must import from their specific
modules (e.g., `from agents.cancellation import CancellationAgent`), NOT from
this package (e.g., NOT `from agents import CancellationAgent`).
"""

from agents.after_hours import AfterHoursAgent
from agents.assistant import Assistant
from agents.cancellation import CancellationAgent
from agents.changes import MakeChangeAgent
from agents.claims import ClaimsAgent
from agents.coverage import CoverageRateAgent
from agents.mortgagee import MortgageeCertificateAgent
from agents.payment import PaymentIDDecAgent
from agents.quote import NewQuoteAgent
from agents.something_else import SomethingElseAgent

__all__ = [
    "AfterHoursAgent",
    "Assistant",
    "CancellationAgent",
    "ClaimsAgent",
    "CoverageRateAgent",
    "MakeChangeAgent",
    "MortgageeCertificateAgent",
    "NewQuoteAgent",
    "PaymentIDDecAgent",
    "SomethingElseAgent",
]
