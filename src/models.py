"""Data models for the Harry Levine Insurance Voice Agent.

This module contains the core data structures used throughout the agent system:
- InsuranceType: Enum for business vs personal insurance
- CallIntent: Enum for categorizing call routing purposes
- CallerInfo: Dataclass tracking caller state throughout conversations
"""

from dataclasses import dataclass
from enum import Enum


class InsuranceType(str, Enum):
    """Type of insurance inquiry."""

    BUSINESS = "business"
    PERSONAL = "personal"


class CallIntent(str, Enum):
    """Categories for call routing based on caller's reason.

    Each intent maps to specific routing behavior and potentially a specialized
    sub-agent for handling the request. The Assistant agent detects these intents
    from the caller's initial statement and routes accordingly.

    Intent Categories
    -----------------
    - **Handoff intents** (NEW_QUOTE, MAKE_PAYMENT): Trigger handoff to specialized
      sub-agents that handle the complete workflow.
    - **Direct routing intents** (MAKE_CHANGE, CANCELLATION, etc.): Route to Account
      Executives via alpha-split after collecting caller info.
    - **Direct answer intents** (HOURS_LOCATION): Answered immediately without transfer.
    - **Special handling intents** (SPECIFIC_AGENT): Require additional lookup and
      may be restricted.

    Examples
    --------
    >>> intent = CallIntent.NEW_QUOTE
    >>> print(intent.value)
    'new_quote'

    See Also
    --------
    Assistant.route_call_new_quote : Handler for NEW_QUOTE intent
    Assistant.route_call_payment_or_documents : Handler for MAKE_PAYMENT intent
    docs/ARCHITECTURE.md : Full routing documentation
    """

    NEW_QUOTE = "new_quote"
    """New insurance quote request.

    Triggers handoff to NewQuoteAgent, which collects insurance type
    (business/personal) and appropriate identifier, then routes to
    sales agents via alpha-split.

    Trigger phrases: "new policy", "get a quote", "looking for insurance",
    "need coverage", "shopping for insurance", "pricing", "how much for"
    """

    MAKE_PAYMENT = "make_payment"
    """Payment or document request (ID cards, dec pages).

    Triggers handoff to PaymentIDDecAgent, which collects insurance type
    and identifier, then routes to VA ring group first with fallback to
    Account Executives.

    Trigger phrases: "make a payment", "pay my bill", "ID card",
    "insurance card", "proof of insurance", "declarations page", "dec page"
    """

    MAKE_CHANGE = "make_change"
    """Policy modification request.

    Routed to Account Executive via alpha-split after collecting
    caller information and insurance identifier.

    Trigger phrases: "change my policy", "update coverage", "add a vehicle",
    "remove a driver", "modify my policy"
    """

    CANCELLATION = "cancellation"
    """Policy cancellation request.

    Triggers handoff to CancellationAgent, which collects insurance type
    and identifier, then routes to Account Executives via alpha-split.
    Agent should show empathy but respect the caller's decision.

    Trigger phrases: "cancel my policy", "cancellation", "cancel insurance",
    "want to cancel", "need to cancel", "stop my policy", "end my policy",
    "don't need insurance anymore", "switching carriers", "found cheaper insurance",
    "non-renew", "don't renew", "stop my insurance", "end my coverage", "discontinue"
    """

    COVERAGE_RATE_QUESTIONS = "coverage_rate_questions"
    """Questions about coverage details or rates.

    Routed to Account Executive via alpha-split. May include questions
    about deductibles, limits, premiums, or what's covered.

    Trigger phrases: "what's my deductible", "coverage limits",
    "how much am I paying", "what does my policy cover"
    """

    POLICY_REVIEW_RENEWAL = "policy_review_renewal"
    """Annual policy review or renewal inquiry.

    Routed to Account Executive via alpha-split. Typically scheduled
    calls or proactive outreach from clients.

    Trigger phrases: "policy review", "renewal", "annual review",
    "my policy is coming up for renewal"
    """

    SOMETHING_ELSE = "something_else"
    """Request that doesn't fit other categories.

    General routing to appropriate staff. The agent should collect
    additional context about the caller's needs.

    Used when: Caller's request doesn't match any specific intent pattern
    """

    MORTGAGEE_LIENHOLDERS = "mortgagee_lienholders"
    """Questions about mortgagee or lienholder information.

    Specialized routing for mortgage company or lienholder inquiries,
    often related to proof of insurance or policy changes.

    Trigger phrases: "mortgagee clause", "lienholder", "loss payee",
    "mortgage company needs", "bank information on policy"
    """

    CERTIFICATES = "certificates"
    """Certificate of insurance requests.

    Specialized routing for COI requests, common for commercial clients
    who need proof of coverage for contracts or vendors.

    Trigger phrases: "certificate of insurance", "COI", "proof of coverage",
    "need a certificate for", "contractor certificate"
    """

    CLAIMS = "claims"
    """Claim filing or status inquiry.

    Routed to claims department during business hours via ClaimsAgent.
    After hours, ClaimsAgent helps callers find their carrier's 24/7 claims
    number and offers callback options.

    IMPORTANT: Callers reporting claims are often distressed. The agent should
    show empathy FIRST before handling the business aspect.

    Business Hours Flow (Mon-Fri, 9 AM - 5 PM Eastern):
    - Show empathy about the situation
    - Transfer to claims ring group

    After-Hours Flow:
    - Show empathy and set expectations (team not available)
    - Help caller find carrier claims number
    - Offer callback option

    Trigger phrases: "file a claim", "make a claim", "I had an accident",
    "car accident", "fender bender", "someone hit me", "got into an accident",
    "need to report a claim", "water damage", "fire damage", "theft", "break-in",
    "vandalism", "roof damage", "storm damage", "hail damage", "flooded",
    "pipe burst", "report a loss", "claim status", "my claim number"
    """

    HOURS_LOCATION = "hours_location"
    """Office hours or location inquiry.

    Answered directly by the agent without transfer. Provides standard
    office information.

    Answer: Monday-Friday 9 AM to 5 PM, 7208 West Sand Lake Road,
    Suite 206, Orlando, Florida 32819
    """

    SPECIFIC_AGENT = "specific_agent"
    """Request for a specific agent by name.

    Direct transfer if agent is available and transferable. Some agents
    (Jason L., Fred) are restricted and require message-taking instead.

    Note: Check is_transferable() before initiating transfer.
    If restricted, offer to take a message.
    """


@dataclass(slots=True)
class CallerInfo:
    """Information collected from the caller.

    This dataclass tracks all information gathered during a call, including
    contact details, insurance type, routing information, and any additional
    notes. It is passed through the agent system as userdata.

    Attributes:
        name: Caller's full name
        phone_number: Caller's phone number for callback
        insurance_type: Business or personal insurance
        business_name: Name of business (for business insurance)
        last_name_spelled: Caller's last name as spelled (for personal insurance)
        call_intent: Detected call intent for routing
        specific_agent_name: Name of specific agent requested (if any)
        additional_notes: Any additional context or notes
        assigned_agent: Agent assigned via alpha-split routing
    """

    name: str | None = None
    phone_number: str | None = None
    insurance_type: InsuranceType | None = None
    business_name: str | None = None
    last_name_spelled: str | None = None
    call_intent: CallIntent | None = None
    specific_agent_name: str | None = None
    additional_notes: str = ""
    assigned_agent: str | None = None  # Agent assigned via alpha-split

    def is_ready_for_routing(self) -> bool:
        """Check if caller info has minimum required data for routing.

        Returns:
            True if both name and phone_number are set, False otherwise.
        """
        return bool(self.name) and bool(self.phone_number)

    def has_insurance_identifier(self) -> bool:
        """Check if caller has provided an insurance identifier.

        For business insurance, this is the business name.
        For personal insurance, this is the spelled last name.

        Returns:
            True if business_name or last_name_spelled is set, False otherwise.
        """
        return bool(self.business_name) or bool(self.last_name_spelled)
