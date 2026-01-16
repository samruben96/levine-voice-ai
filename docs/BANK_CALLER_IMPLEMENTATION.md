# Bank Caller Flow Implementation Guide

**For**: Python Developers integrating the bank caller conversation flow

---

## Overview

Bank callers are already routed to `MortgageeCertificateAgent` via the `route_call_mortgagee()` function in the Assistant agent. This document shows how the exact conversational flow integrates with existing code.

---

## Current Implementation Status

### Already In Place

```python
# In src/agents/assistant.py

@function_tool
async def route_call_mortgagee(
    self,
    context: RunContext[CallerInfo],
) -> tuple[Agent, str]:
    """Route the call for mortgagee, lienholder, or bank caller requests.

    Trigger phrases:
    - "calling from [bank]", "bank representative", "mutual client"
    - "verify coverage", "confirm renewal", "on a recorded line"
    """
    context.userdata.call_intent = CallIntent.MORTGAGEE_LIENHOLDERS
    logger.info(f"Detected mortgagee request, handing off to MortgageeCertificateAgent")

    return (
        MortgageeCertificateAgent(request_type="mortgagee"),
        "I can help you with that.",
    )
```

### Current Agent Instructions (in mortgagee.py)

```python
# The agent already has the email configured:
# - info@hlinsure.com for mortgagee/bank requests
# - Certificate@hlinsure.com for certificate requests

# Tool already exists:
@function_tool
async def provide_mortgagee_email_info(
    self,
    context: RunContext[CallerInfo],
) -> str:
    """Provide mortgagee/lienholder request email information."""
    context.userdata.call_intent = CallIntent.MORTGAGEE_LIENHOLDERS
    logger.info("Mortgagee request - provided email info")
    return (
        "Thank you for reaching out. HLI requires all mortgagee and lienholder "
        "requests to be sent in writing to info@hlinsure.com. "
        "Is there anything else I can help you with today?"
    )
```

---

## Enhanced Flow Implementation

### Option 1: Extend MortgageeCertificateAgent with Bank-Specific Handling

**New Tool to Add:**

```python
@function_tool
async def handle_bank_caller_request(
    self,
    context: RunContext[CallerInfo],
    caller_confirmed: bool,
) -> str:
    """Handle bank caller verification and documentation request.

    Call this after asking the clarifying question:
    "Let me clarify - are you requesting renewal documents
     or invoices for a mutual customer?"

    Args:
        caller_confirmed: True if caller confirmed they want documents,
                         False if they need to clarify or have other needs
    """
    context.userdata.call_intent = CallIntent.MORTGAGEE_LIENHOLDERS

    if not caller_confirmed:
        # Redirect to ask what they actually need
        logger.info("Bank caller needs clarification on request type")
        return "No problem. Can you tell me what you're calling about today?"

    # Caller confirmed they need documentation
    logger.info("Bank caller requesting mutual customer documents")
    return (
        "Perfect. All requests must be submitted in writing to Info@HLInsure.com. "
        "No, we don't have a fax number."
    )
```

**Error Recovery Tools to Add:**

```python
@function_tool
async def handle_bank_transfer_request(
    self,
    context: RunContext[CallerInfo],
) -> str:
    """Handle bank caller asking to speak with someone.

    Call this when the caller asks "Can I speak to someone?"
    """
    logger.info("Bank caller requested transfer - not available")
    return (
        "I'm not able to transfer calls for documentation requests, but the team "
        "at Info@HLInsure.com will be happy to help. They typically respond within "
        "one business day."
    )

@function_tool
async def handle_bank_urgency(
    self,
    context: RunContext[CallerInfo],
) -> str:
    """Handle bank caller indicating time sensitivity.

    Call this when the caller mentions the request is urgent.
    """
    logger.info("Bank caller indicates urgent request")
    return (
        "I understand it's urgent. Please note that in your email to "
        "Info@HLInsure.com and they'll prioritize your request."
    )

@function_tool
async def handle_bank_fax_question(
    self,
    context: RunContext[CallerInfo],
) -> str:
    """Handle bank caller asking about fax option.

    Call this if they ask about fax despite the preemptive statement.
    """
    logger.info("Bank caller asking about fax option")
    return (
        "We don't accept fax requests. Email to Info@HLInsure.com is the way to go."
    )
```

---

### Option 2: Add Bank Caller Specific Instructions Section

**In MortgageeCertificateAgent.__init__():**

Add to the instructions composition:

```python
BANK_CALLER_INSTRUCTIONS = """## BANK CALLER FLOW (Special Case of Mortgagee)

IDENTIFICATION:
- Caller will identify as: "calling from [bank]" or "bank representative"
- They're calling about a CUSTOMER'S policy, not their own
- No need to collect personal/business insurance info

CONVERSATION FLOW:
1. CLARIFY REQUEST:
   "Let me clarify - are you requesting renewal documents or invoices
    for a mutual customer?"

2. CONFIRM AND RESPOND:
   - If YES: "Perfect. All requests must be submitted in writing to
     Info@HLInsure.com. No, we don't have a fax number."
   - If UNSURE: "No problem. Can you tell me what you're calling about today?"

3. ERROR RECOVERY:
   - "Can I speak to someone?" → Use handle_bank_transfer_request tool
   - "This is urgent" → Use handle_bank_urgency tool
   - "What's your fax?" → Use handle_bank_fax_question tool

KEY POINTS:
- Email: Info@HLInsure.com (not Certificate@hlinsure.com)
- State "No fax" proactively to prevent follow-ups
- Do NOT transfer for documentation requests
- Keep responses under 25 words for natural speech pace
"""
```

---

## Python Integration Example

### Complete Enhanced on_enter() Method

```python
async def on_enter(self) -> None:
    """Called when this agent becomes active - start appropriate flow."""
    if self._request_type == "certificate":
        self.session.generate_reply(
            instructions=(
                "The caller needs a certificate of insurance. Start by informing them "
                "about the email requirement (Certificate@hlinsure.com) using the "
                "provide_certificate_email_info tool, then offer the self-service app option."
            )
        )
    elif self._request_type == "mortgagee":
        # This handles both standard mortgagee AND bank callers
        self.session.generate_reply(
            instructions=(
                "The caller has a mortgagee, lienholder, or bank caller request. "
                "\nSTART WITH: Ask the clarifying question: "
                '"Let me clarify - are you requesting renewal documents or invoices '
                'for a mutual customer?"'
                "\nBased on their response, use handle_bank_caller_request tool."
            )
        )
    else:
        self.session.generate_reply(
            instructions=(
                "Ask the caller to clarify whether they need a certificate of insurance, "
                "have a mortgagee/lienholder request, or are calling from a bank about "
                "a mutual customer."
            )
        )
```

---

## Testing the Implementation

### Unit Test Example

```python
# In tests/unit/test_bank_callers.py

import pytest
from src.agents.mortgagee import MortgageeCertificateAgent
from src.models import CallerInfo, CallIntent

@pytest.mark.unit
def test_bank_caller_clarifying_question():
    """Bank caller receives clarifying question."""
    agent = MortgageeCertificateAgent(request_type="mortgagee")
    # The on_enter should prompt for the clarifying question
    # Verify in logs or via LLM response that the exact wording is used
    assert "renewal documents or invoices" in agent.instructions

@pytest.mark.unit
def test_bank_caller_email_response():
    """Bank caller receives correct email and no-fax statement."""
    agent = MortgageeCertificateAgent(request_type="mortgagee")
    context = RunContext(userdata=CallerInfo())

    # Simulate calling the new tool
    response = agent.handle_bank_caller_request(context, caller_confirmed=True)

    assert "Info@HLInsure.com" in response
    assert "No, we don't have a fax number" in response
    assert "Perfect" in response

@pytest.mark.unit
def test_bank_caller_transfer_recovery():
    """Bank caller asking for transfer gets correct response."""
    agent = MortgageeCertificateAgent(request_type="mortgagee")
    context = RunContext(userdata=CallerInfo())

    response = agent.handle_bank_transfer_request(context)

    assert "not able to transfer" in response
    assert "Info@HLInsure.com" in response
    assert "one business day" in response
```

### Integration Test Example

```python
# In tests/integration/test_bank_callers.py

@pytest.mark.integration
async def test_bank_caller_full_flow():
    """Test complete bank caller conversation."""
    # Setup
    assistant = Assistant()

    # Simulate detection
    caller_says = "Hi, calling from First National Bank. We have a mutual customer."
    context = RunContext(userdata=CallerInfo())

    # Route to mortgagee agent
    new_agent, transition = await assistant.route_call_mortgagee(context)
    assert isinstance(new_agent, MortgageeCertificateAgent)
    assert new_agent._request_type == "mortgagee"

    # The mortgagee agent should now handle the flow
    # (In actual testing, would simulate voice conversation)
```

---

## Key Implementation Points

### 1. No Need for Collection Logic
```python
# Bank callers do NOT need:
# - record_caller_contact_info() (optional but not required)
# - Insurance type detection (they're not OUR customer)
# - Last name or business name collection
# - Alpha-split routing

# They ONLY need:
# - Clarification question
# - Email address: Info@HLInsure.com
# - Confirmation they understand email-only process
```

### 2. Tool Flow

```
Assistant.route_call_mortgagee()
        ↓
MortgageeCertificateAgent(request_type="mortgagee")
        ↓
on_enter() prompts clarifying question
        ↓
handle_bank_caller_request()
        ↓
[If error: handle_bank_transfer_request, handle_bank_urgency, etc.]
```

### 3. Exact Wording in Code

```python
# These strings must match the design doc EXACTLY:

BANK_CLARIFYING_Q = (
    "Let me clarify - are you requesting renewal documents "
    "or invoices for a mutual customer?"
)

BANK_RESPONSE_YES = (
    "Perfect. All requests must be submitted in writing to "
    "Info@HLInsure.com. No, we don't have a fax number."
)

BANK_RESPONSE_REDIRECT = (
    "No problem. Can you tell me what you're calling about today?"
)
```

---

## Deployment Checklist

- [ ] MortgageeCertificateAgent updated with bank-specific tools
- [ ] Exact wording matches design doc (verify word-for-word)
- [ ] Error recovery branches implemented
- [ ] Unit tests added for each tool
- [ ] Integration test covers full happy path
- [ ] Agent instructions include BANK_CALLER_INSTRUCTIONS section
- [ ] Email addresses verified (Info@HLInsure.com)
- [ ] Voice testing completed (rate, clarity, naturalness)
- [ ] QA testing with bank caller scenarios
- [ ] Documentation updated in OPERATIONS.md

---

## References

- **Design Doc**: `/docs/BANK_CALLER_FLOW.md`
- **Quick Ref**: `/docs/BANK_CALLER_QUICK_REFERENCE.md`
- **Dialog Flow**: `/docs/BANK_CALLER_DIALOG_FLOW.txt`
- **Agent Code**: `/src/agents/mortgagee.py`
- **Router Code**: `/src/agents/assistant.py`
