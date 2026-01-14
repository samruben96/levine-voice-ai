# Architecture Documentation

This document describes the architecture of the Harry Levine Insurance Voice Agent, including system components, data flow, routing logic, and state management.

---

## Table of Contents

- [System Overview](#system-overview)
- [Agent Architecture](#agent-architecture)
- [Data Flow](#data-flow)
- [Routing Logic](#routing-logic)
- [Call Intent Categories](#call-intent-categories)
- [Staff Directory Integration](#staff-directory-integration)
- [Conversation State Diagram](#conversation-state-diagram)
- [Error Handling](#error-handling)
- [Security Considerations](#security-considerations)

---

## System Overview

The Harry Levine Insurance Voice Agent is a voice AI system built on the LiveKit Agents framework. It serves as an automated front-desk receptionist that handles incoming calls, collects caller information, and routes calls to the appropriate staff member.

### Core Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| Speech-to-Text (STT) | AssemblyAI | Converts caller speech to text |
| Large Language Model (LLM) | GPT-4.1-mini | Processes intent and generates responses |
| Text-to-Speech (TTS) | Cartesia Sonic-3 | Converts agent responses to speech |
| Voice Activity Detection (VAD) | Silero | Detects when caller is speaking |
| Turn Detection | LiveKit Multilingual | Manages conversation turn-taking |
| Noise Cancellation | LiveKit BVC | Removes background noise (telephony-optimized) |

### Key Features

- **Single-agent architecture**: Assistant handles all routing directly via transfer tools
- **Alpha-split routing**: Calls routed based on business/last name first letter
- **Ring group support**: Multiple agents can be called simultaneously
- **Restricted transfers**: Certain staff require live-person handling
- **PII masking**: Caller information masked in logs
- **No double-asking**: Callers provide information once (fixed in Phase 5)

---

## Agent Architecture

The system uses a **single-agent architecture** where the Assistant handles all routing directly via transfer tools. This design eliminates the "double-asking" bug where callers were asked the same questions twice after handoffs.

```
+---------------------------------------------------------------------+
|                         Incoming Call                               |
+---------------------------------------------------------------------+
                                |
                                v
+---------------------------------------------------------------------+
|                        Voice Pipeline                               |
|  +------------+  +------------+  +------------+  +--------------+   |
|  |    STT     |->|    LLM     |->|    TTS     |->|    Audio     |   |
|  | AssemblyAI |  | GPT-4.1    |  |  Cartesia  |  |   Output     |   |
|  +------------+  +------------+  +------------+  +--------------+   |
+---------------------------------------------------------------------+
                                |
                                v
+---------------------------------------------------------------------+
|                       Assistant Agent                               |
|              (Front Desk Receptionist - Aizellee)                   |
|                                                                     |
|   Intent Detection --> Information Collection --> Direct Transfer   |
|                                                                     |
|   Transfer Tools:                                                   |
|   - transfer_new_quote       (routes to Sales Agents)               |
|   - transfer_payment         (routes to VA or Account Execs)        |
|   - transfer_policy_change   (routes to Account Executives)         |
|   - transfer_cancellation    (routes to Account Executives)         |
|   - transfer_coverage_question (routes to Account Executives)       |
|   - transfer_something_else  (warm transfer to Account Execs)       |
+---------------------------------------------------------------------+
             |                                       |
             | (handoff only for specialized flows)  |
             v                                       v
+------------------------+             +---------------------------+
|    ClaimsAgent         |             |  MortgageeCertificateAgent|
|                        |             |                           |
| - Business hours check |             | - Provides email info     |
| - Carrier claims lookup|             | - Self-service app option |
| - Empathy handling     |             | - No transfer needed      |
+------------------------+             +---------------------------+
             |
             v
+------------------------+
|   AfterHoursAgent      |
|                        |
| - Voicemail routing    |
| - Alpha-split to AEs   |
+------------------------+
```

### Agent Responsibilities

#### Assistant (Main Agent)

The primary entry point for all calls. Handles ALL routing directly:

- Greet callers with standard greeting
- Detect call intent from initial request
- Collect contact information (name, phone)
- Collect insurance type and identifier (business name or last name)
- **Execute direct transfers** using transfer tools (no handoff)
- Handle direct answers (hours, location)
- Process specific agent requests
- Handoff ONLY for: Claims, Certificates/Mortgagee, After-hours

#### Transfer Tools (in Assistant)

| Tool | Purpose | Routing |
|------|---------|---------|
| `transfer_new_quote` | New quote requests | Alpha-split to Sales Agents |
| `transfer_payment` | Payments, ID cards, dec pages | VA ring group or Account Execs |
| `transfer_policy_change` | Policy modifications | Alpha-split to Account Execs |
| `transfer_cancellation` | Policy cancellations | Alpha-split to Account Execs |
| `transfer_coverage_question` | Coverage/rate questions | Alpha-split to Account Execs |
| `transfer_something_else` | Other inquiries | Warm transfer to Account Execs |

#### ClaimsAgent

Handles claims with business hours awareness:

- During business hours: Show empathy, transfer to claims team
- After hours: Show empathy, provide carrier's 24/7 claims number

#### MortgageeCertificateAgent

Handles certificate and mortgagee requests (no transfer needed):

- Provides Certificate@hlinsure.com for certificate requests
- Provides info@hlinsure.com for mortgagee requests
- Offers self-service app option

#### AfterHoursAgent

Handles after-hours calls:

- Informs caller the office is closed
- Collects name, phone, insurance type, identifier
- Routes to voicemail via alpha-split

---

## Data Flow

### CallerInfo State Object

The `CallerInfo` dataclass tracks all information collected during a call:

```python
@dataclass
class CallerInfo:
    name: str | None                    # Caller's full name
    phone_number: str | None            # Callback number
    insurance_type: InsuranceType | None # BUSINESS or PERSONAL
    business_name: str | None           # For business insurance
    last_name_spelled: str | None       # For personal insurance
    call_intent: CallIntent | None      # Detected intent category
    specific_agent_name: str | None     # If requesting specific agent
    additional_notes: str               # Miscellaneous notes
    assigned_agent: str | None          # Agent determined by routing
```

### State Flow (Single-Agent Design)

```
Assistant (handles everything)
    |
    | 1. Greet caller
    | 2. Detect intent
    | 3. Collect name/phone
    | 4. Collect insurance type
    | 5. Collect business name OR last name
    | 6. Execute transfer tool
    |
    v
+-- Direct Transfer (no handoff) ---+
    |                               |
    | OR (for specialized flows):   |
    |                               |
    v                               v
ClaimsAgent                MortgageeCertificateAgent
AfterHoursAgent
```

The `CallerInfo` object is maintained in `RunContext[CallerInfo]` throughout the conversation. With the single-agent design, there are no handoffs for most call types - the Assistant collects all information and executes transfers directly.

### What Data is Preserved vs Reset

| Data Type | Preserved | Reset |
|-----------|-----------|-------|
| Caller name | Yes | - |
| Phone number | Yes | - |
| Insurance type | Yes | - |
| Business name | Yes | - |
| Last name | Yes | - |
| Call intent | Yes | - |
| Session ID | Yes | - |
| Conversation history | Yes | - |
| Agent instructions | - | Per-agent |
| Available tools | - | Per-agent |

---

## Routing Logic

### Alpha-Split Routing

Calls are routed to specific agents based on alphabetical ranges of business names or last names.

#### Commercial Lines (CL)

Both new business AND existing clients route to CL Account Executives based on business name:

```
Business Name First Letter --> Agent
         A-F              --> Adriana (ext 7002)
         G-O              --> Rayvon (ext 7018)
         P-Z              --> Dionna (ext 7006)
       Platinum           --> Rachel T. (ext 7005)
```

#### Personal Lines (PL) - New Business

New quotes route to Sales Agents based on caller's last name:

```
Last Name First Letter --> Agent
         A-L           --> Queens (ext 7010)
         M-Z           --> Brad (ext 7007)
```

#### Personal Lines (PL) - Existing Clients

Service requests route to Account Executives based on caller's last name:

```
Last Name First Letter --> Agent
         A-G           --> Yarislyn (ext 7011)
         H-M           --> Al (ext 7015)
         N-Z           --> Luis (ext 7017)
```

### Alpha Exception Prefixes

Certain business name prefixes are skipped when determining the routing letter:

| Prefix | Example | Routes On |
|--------|---------|-----------|
| "The" | "The Great Company" | G |
| "Law office of" | "Law office of Smith" | S |
| "Law offices of" | "Law Offices of Harry Levine" | H |

Implementation in `get_alpha_route_key()`:

```python
# "The ABC Company" routes on "A", not "T"
# "Law Offices of Brown" routes on "B", not "L"
```

### Ring Group Priority

For payment/document requests:

1. **Primary**: Try VA ring group (Ann ext 7016, Sheree ext 7008)
2. **Fallback**: Route to Account Executive via alpha-split

### Restricted Transfers

Some staff members cannot receive direct AI transfers:

| Name | Extension | Handling |
|------|-----------|----------|
| Jason L. | 7000 | Take message |
| Fred | 7012 | Take message |

When a caller requests these individuals, the agent offers to take a message instead of transferring.

---

## Call Intent Categories

The `CallIntent` enum defines 12 categories for call routing:

| Intent | Value | Description | Routing Behavior |
|--------|-------|-------------|------------------|
| NEW_QUOTE | `new_quote` | New insurance quote request | Handoff to NewQuoteAgent |
| MAKE_PAYMENT | `make_payment` | Payment or document request | Handoff to PaymentIDDecAgent |
| MAKE_CHANGE | `make_change` | Policy modification | Route to Account Executive |
| CANCELLATION | `cancellation` | Policy cancellation | Route to Account Executive |
| COVERAGE_RATE_QUESTIONS | `coverage_rate_questions` | Coverage/rate inquiries | Route to Account Executive |
| POLICY_REVIEW_RENEWAL | `policy_review_renewal` | Policy review or renewal | Route to Account Executive |
| SOMETHING_ELSE | `something_else` | Unclassified request | General routing |
| MORTGAGEE_LIENHOLDERS | `mortgagee_lienholders` | Mortgagee/lienholder questions | Specialized routing |
| CERTIFICATES | `certificates` | Certificate of insurance | Specialized routing |
| CLAIMS | `claims` | Claim filing or status | Claims department |
| HOURS_LOCATION | `hours_location` | Office hours or directions | Direct answer (no transfer) |
| SPECIFIC_AGENT | `specific_agent` | Request for specific agent | Direct transfer or message |

### Intent Detection Keywords

The agent uses keyword matching as supplementary signals for intent detection:

**New Quote Keywords**:
- "new policy", "get a quote", "looking for insurance", "need coverage"
- "shopping for insurance", "get insured", "pricing", "how much for"
- "start a policy", "want a quote", "insurance quote", "buy insurance"

**Payment/ID-Dec Keywords**:
- "make a payment", "pay my bill", "payment", "pay premium"
- "ID card", "insurance card", "proof of insurance"
- "declarations page", "dec page", "need my cards"

---

## Staff Directory Integration

The `staff_directory.py` module provides routing configuration and helper functions.

### Core Data Structure

```python
STAFF_DIRECTORY: StaffDirectoryConfig = {
    "staff": [...],                    # List of StaffMember entries
    "restrictedTransfers": [...],      # Names that can't receive AI transfers
    "alphaExceptionPrefixes": [...],   # Prefixes to skip in routing
    "ringGroups": {...},               # Named ring group configurations
}
```

### Routing Helper Functions

| Function | Purpose | Usage |
|----------|---------|-------|
| `get_alpha_route_key(business_name)` | Extract routing letter from business name | Called before `find_agent_by_alpha` |
| `find_agent_by_alpha(letter, dept, is_new)` | Find agent by alpha range and department | Main routing function |
| `is_transferable(agent_name)` | Check if agent can receive AI transfers | Called before transfer |
| `get_agent_by_name(name)` | Look up agent by name (partial match) | For specific agent requests |
| `get_agent_by_extension(ext)` | Look up agent by extension | For extension lookups |
| `get_agents_by_department(dept)` | Get all agents in a department | For ring groups |
| `get_ring_group(name)` | Get ring group configuration | For VA team routing |

### Integration Example

```python
# In NewQuoteAgent.record_business_quote_info():

# 1. Extract routing letter from business name
route_key = get_alpha_route_key(business_name)  # "The Great Co" -> "G"

# 2. Find agent in Commercial Lines for new business
agent = find_agent_by_alpha(route_key, "CL", is_new_business=True)

# 3. Store assigned agent for transfer
context.userdata.assigned_agent = agent["name"]
```

---

## Conversation State Diagram

With the single-agent architecture, the conversation flow is streamlined:

```
                          +-------------+
                          |   START     |
                          +------+------+
                                 |
                                 v
                          +-------------+
                          |  GREETING   |
                          | "Thank you  |
                          | for calling"|
                          +------+------+
                                 |
                                 v
                    +------------+------------+
                    |    INTENT DETECTION     |
                    |  (What can I help with?)|
                    +------------+------------+
                                 |
          +----------------------+----------------------+
          |                      |                      |
          v                      v                      v
   +------+------+        +------+------+        +------+------+
   | DIRECT      |        | TRANSFER    |        | SPECIALIZED |
   | ANSWER      |        | FLOW        |        | HANDOFF     |
   | (hours/loc) |        | (quote/pay/ |        | (claims/    |
   +------+------+        |  change/etc)|        |  certs)     |
          |               +------+------+        +------+------+
          v                      |                      |
   +------+------+               v                      v
   | COMPLETE    |        +------+------+        +------+------+
   | (answered)  |        | CONTACT     |        | AGENT       |
   +-------------+        | INFO        |        | HANDOFF     |
                         | (name/phone)|        +------+------+
                         +------+------+               |
                                |                      v
                                v               (ClaimsAgent,
                         +------+------+        MortgageeCert,
                         | INSURANCE   |        AfterHours)
                         | TYPE        |
                         | (bus/pers)  |
                         +------+------+
                                |
                                v
                         +------+------+
                         | IDENTIFIER  |
                         | COLLECTION  |
                         | (name/biz)  |
                         +------+------+
                                |
                                v
                         +------+------+
                         | DIRECT      |
                         | TRANSFER    |
                         | (via tool)  |
                         +------+------+
                                |
                                v
                         +------+------+
                         |    END      |
                         | (call ends) |
                         +-------------+
```

### State Transitions (Single-Agent)

| From State | Event | To State |
|------------|-------|----------|
| START | Call connected | GREETING |
| GREETING | Greeting delivered | INTENT DETECTION |
| INTENT DETECTION | Hours/location request | DIRECT ANSWER |
| INTENT DETECTION | Quote/Payment/Change/etc | TRANSFER FLOW |
| INTENT DETECTION | Claims/Certs/After-hours | SPECIALIZED HANDOFF |
| DIRECT ANSWER | Question answered | COMPLETE |
| TRANSFER FLOW | Intent detected | CONTACT INFO |
| CONTACT INFO | Name/phone collected | INSURANCE TYPE |
| INSURANCE TYPE | Type confirmed | IDENTIFIER COLLECTION |
| IDENTIFIER COLLECTION | Business name or last name collected | DIRECT TRANSFER |
| DIRECT TRANSFER | Transfer tool executed | END |
| SPECIALIZED HANDOFF | Agent handoff | (Agent-specific flow) |

### Key Difference from Previous Architecture

Previously, the flow included "SUB-AGENT HANDOFF" states where the conversation context was passed to another agent (NewQuoteAgent, MakeChangeAgent, etc.). This caused the "double-asking" bug because sub-agents would re-confirm information.

Now, the Assistant handles the entire TRANSFER FLOW directly and executes transfers via tools without handoffs.

---

## Error Handling

### Session Initialization

```python
try:
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_options,
    )
    await ctx.connect()
    await session.say("Thank you for calling...")
except Exception as e:
    logger.exception(f"Session initialization failed: {e}")
    raise
```

### Environment Validation

At startup, the agent validates required environment variables:

```python
REQUIRED_ENV = ["LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET"]

def validate_environment() -> None:
    missing = [v for v in REQUIRED_ENV if not os.getenv(v)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {missing}")
```

### Fallback Behaviors

| Scenario | Fallback Behavior |
|----------|-------------------|
| No agent found for alpha range | Use default message, log warning |
| Assigned agent unavailable | Take data sheet for callback |
| VA ring group unavailable | Route to Account Executive |
| Restricted transfer requested | Offer to take message |
| Unknown intent | Route to general queue |

### Logging

All significant events are logged with appropriate severity:

```python
logger.info(f"Routing call for policy change: {context.userdata}")
logger.info(f"Restricted transfer requested: {agent['name']} - offering to take message")
logger.exception(f"Session initialization failed: {e}")
```

---

## Security Considerations

### PII Masking

Caller information is masked in logs to protect privacy:

```python
def mask_phone(phone: str) -> str:
    """Mask phone number, showing only last 4 digits."""
    return "***-***-" + phone[-4:] if phone and len(phone) >= 4 else "***"

def mask_name(name: str) -> str:
    """Mask name, showing only first character."""
    return name[0] + "*" * (len(name) - 1) if name else "***"
```

Log output example:
```
INFO - Recorded caller info: J***, ***-***-1234
INFO - New quote - Personal insurance, last name: S**** (letter: S) -> Queens ext 7010
```

### Restricted Transfers

Certain staff members are protected from direct AI transfers:

```python
"restrictedTransfers": ["Jason L.", "Fred"]
```

This prevents:
- Automated calls reaching executives without screening
- Special project staff being interrupted
- Potential abuse of direct transfer capabilities

The `is_transferable()` function checks both:
1. The `restrictedTransfers` list
2. The `transferable` field on individual staff entries

### Prompt Injection Resistance

The agent instructions include safeguards:

1. **Session isolation**: "Every call is a BRAND NEW conversation. You have NO prior history with ANY caller."

2. **No reference to previous conversations**: "NEVER reference 'earlier', 'before', 'last time', or any previous conversation."

3. **Clarification over assumption**: "If a caller says something unclear or ambiguous, ask a fresh clarifying question."

### Data Handling

| Data Type | Storage | Retention |
|-----------|---------|-----------|
| Caller name | Session memory | Session duration |
| Phone number | Session memory | Session duration |
| Business name | Session memory | Session duration |
| Call recordings | LiveKit Cloud | Per policy |
| Transfer logs | Application logs | Per retention policy |

### Environment Variables

Sensitive configuration is stored in environment variables, never hardcoded:

```python
LIVEKIT_URL          # LiveKit server WebSocket URL
LIVEKIT_API_KEY      # LiveKit API key
LIVEKIT_API_SECRET   # LiveKit API secret
```

---

## Appendix: File Structure

```
src/
  __init__.py              # Package init
  models.py                # CallerInfo, CallIntent, InsuranceType
  utils.py                 # PII masking utilities
  constants.py             # HOLD_MESSAGE, CARRIER_CLAIMS_NUMBERS
  main.py                  # Server setup, entry point
  agent.py                 # Backwards compatibility wrapper
  instruction_templates.py # Token-optimized instruction fragments
  business_hours.py        # Business hours utilities
  staff_directory.py       # Staff data and routing logic
  agents/
    __init__.py            # Exports: Assistant, ClaimsAgent, MortgageeCertificateAgent, AfterHoursAgent
    assistant.py           # Main Assistant with transfer tools
    claims.py              # ClaimsAgent
    mortgagee.py           # MortgageeCertificateAgent
    after_hours.py         # AfterHoursAgent

tests/
  conftest.py              # Shared fixtures
  test_utils.py            # Utility function tests
  unit/                    # Fast unit tests
  integration/             # LLM integration tests
  test_agent.py            # Original (compatibility)
  test_staff_directory.py  # Routing logic tests
  test_business_hours.py   # Business hours tests

docs/
  ARCHITECTURE.md          # This document
  OPERATIONS.md            # Operational guide
  LATENCY_TUNING.md        # Voice latency optimization
  BASE_ROUTING_AGENT_DESIGN.md # Historical (superseded by Phase 5)
```

---

*Last updated: 2026-01-14 (Phase 5: Single-Agent Architecture)*
