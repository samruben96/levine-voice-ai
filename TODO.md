# Harry Levine Insurance Voice Agent - TODO

## Completed

### Staff Directory & Routing (92/92 tests passing)
- [x] Create staff directory configuration (`src/staff_directory.py`)
- [x] Implement routing helper functions with alpha-split logic
- [x] Handle exception prefixes ("The", "Law office/offices of")
- [x] Add restricted transfer logic (Jason L., Fred → "not available, take a message")
- [x] Integrate staff directory into agent.py routing
- [x] Add VA ring group configuration (Ann ext 7016, Sheree ext 7008)
- [x] Add `get_ring_group()` helper function

### Intent Handlers
- [x] **New Quote Flow** (NewQuoteAgent)
  - [x] Implement new quote intent detection keywords
  - [x] Create NewQuoteAgent with business/personal flow
  - [x] Add transfer logic with agent lookup and fallback routing
  - [x] Early handoff (collect contact info only, then hand off)

- [x] **Payment/ID-Dec Flow** (PaymentIDDecAgent)
  - [x] Add `PAYMENT_IDDEC_KEYWORDS` for intent detection
  - [x] Create `PaymentIDDecAgent` class with business/personal flow
  - [x] Update `route_call_payment_or_documents` with handoff
  - [x] VA ring group priority, fallback to Account Executives
  - [x] Early handoff (collect contact info only, then hand off)

- [x] **Policy Change Flow** (MakeChangeAgent)
  - [x] Add policy change intent detection keywords (make a change, add vehicle, remove driver, swap truck, change address, add/remove coverage, endorsement)
  - [x] Create `MakeChangeAgent` class with business/personal flow
  - [x] Add `route_call_policy_change` handoff in Assistant
  - [x] Smart context detection (e.g., "work truck" auto-infers business insurance)
  - [x] Alpha-split routing to Account Executives (PL: Yarislyn A-G, Al H-M, Luis N-Z; CL: Adriana A-F, Rayvon G-O, Dionna P-Z)
  - [x] Fallback/hold handling placeholder with data sheet callback
  - [x] Write tests for policy change flow (14 new tests)

- [x] **Cancellation Flow** (CancellationAgent)
  - [x] Add cancellation intent detection keywords (cancel my policy, cancellation, cancel insurance, want to cancel, need to cancel, stop my policy, end my policy, don't need insurance anymore, switching carriers, found cheaper insurance, non-renew, don't renew)
  - [x] Create `CancellationAgent` class with empathetic tone
  - [x] Add `route_call_cancellation` handoff in Assistant
  - [x] Smart context detection for business/personal insurance
  - [x] Alpha-split routing to Account Executives (existing clients only)
  - [x] Configurable fallback options (Option A: data sheet, Option B: ring all AEs, Option C: specific backup)
  - [x] Data sheet collection for callbacks (name, phone, insurance type, business/last name, reason, callback time)
  - [x] On-hold experience with HOLD_MESSAGE
  - [x] Write tests for cancellation flow (18 new tests)

- [x] **Coverage & Rate Questions Flow** (CoverageRateAgent) - Added 2026-01-13
  - [x] Add intent detection keywords (coverage question, rate question, why did my rate go up, premium increase, what's covered, am I covered for, does my policy cover, deductible, what are my limits, liability coverage, comprehensive, collision, why is my bill higher, rate change, policy limits, coverage limits, what does my policy include)
  - [x] Create `CoverageRateAgent` class following existing patterns
  - [x] Add `route_call_coverage_rate` handoff in Assistant
  - [x] Smart context detection for business/personal insurance
  - [x] Alpha-split routing to Account Executives ONLY (NOT VAs/CSRs - requires licensed professionals)
    - Personal Lines: Yarislyn (A-G), Al (H-M), Luis (N-Z)
    - Commercial Lines: Adriana (A-F), Rayvon (G-O), Dionna (P-Z)
  - [x] Data sheet fallback for callbacks when AE unavailable
  - [x] Write tests for coverage/rate flow (16 new tests - all passing)

- [x] **Something Else Flow** (SomethingElseAgent) - Added 2026-01-13
  - [x] Create `SomethingElseAgent` as catch-all/fallback for requests that don't match other intents
  - [x] Add `route_call_something_else` handoff in Assistant
  - [x] Flow: Confirm insurance type → Gather summary → Collect identifier → Transfer
  - [x] `record_request_summary()` tool to capture what the caller needs (stored in `additional_notes`)
  - [x] Smart context detection for business/personal insurance
  - [x] Alpha-split routing to Account Executives (same as MakeChange/Cancellation):
    - Personal Lines: Yarislyn (A-G), Al (H-M), Luis (N-Z)
    - Commercial Lines: Adriana (A-F), Rayvon (G-O), Dionna (P-Z)
  - [x] **WARM TRANSFER** with context relay:
    - Logs warm transfer intro: "Hi [Agent Name], I have [Caller Name] on the line. They're calling about [summary]."
    - Passes caller context (name, phone, insurance type, summary) to receiving agent
    - TODO: Implement actual SIP warm transfer (conference call or whisper) when phone system configured
  - [x] Data sheet fallback for callbacks when AE unavailable
  - [x] Write tests for something else flow (12 new tests - all passing)

- [x] **Mortgagee, Lienholder & Certificate Requests Flow** (MortgageeCertificateAgent) - Added 2026-01-13
  - [x] Create `MortgageeCertificateAgent` class (DOES NOT TRANSFER - redirects to email/self-service)
  - [x] Certificate request flow:
    - Provides Certificate@hlinsure.com email for written requests
    - Offers self-service option (Harry Levine Insurance app for 24/7 certificate issuance)
    - Offers login help (resend credentials or transfer to VA for assistance)
  - [x] Mortgagee/lienholder request flow:
    - Provides info@hlinsure.com email for written requests
    - Offers additional help
  - [x] Add `route_call_certificate` handoff in Assistant
    - Keywords: certificate of insurance, COI, need a certificate, proof of insurance, additional insured, vendor certificate, certificate for a job
  - [x] Add `route_call_mortgagee` handoff in Assistant
    - Keywords: mortgagee, lienholder, mortgage company, lender needs, bank needs proof, loss payee, mortgage clause
  - [x] Function tools:
    - `provide_certificate_email_info()` - certificate email + app info
    - `provide_mortgagee_email_info()` - mortgagee email info
    - `check_login_status()` - app login assistance flow
    - `collect_email_for_credentials()` - collect email to resend app credentials
    - `transfer_for_login_help()` - transfer to VA ring group for login help
  - [x] Write tests for certificate/mortgagee flow (26 new tests - all passing)

- [x] **Claims Flow** (ClaimsAgent) - Added 2026-01-13
  - [x] Create `ClaimsAgent` class with business hours vs after-hours behavior
  - [x] Business hours flow (Mon-Fri, 9 AM - 5 PM Eastern):
    - Show empathy for the caller's situation
    - Transfer to claims ring group via `transfer_to_claims()` tool
    - TODO: Needs extension(s) for claims ring group from client
  - [x] After-hours flow:
    - Show empathy and explain team is not available
    - Help caller find their carrier's 24/7 claims number via `record_carrier_name()` tool
    - Offer callback option via `request_callback()` tool
  - [x] Add `is_office_open()` utility function for business hours check
  - [x] Add `CARRIER_CLAIMS_NUMBERS` config dict (placeholder with Progressive, Travelers, Hartford, Liberty Mutual)
  - [x] Add `get_carrier_claims_number()` helper with case-insensitive lookup
  - [x] Add `route_call_claims` handoff in Assistant (routes immediately with empathy)
  - [x] Update `CallIntent.CLAIMS` docstring with comprehensive trigger phrases
  - [x] Trigger phrases: file a claim, make a claim, I had an accident, car accident, fender bender, someone hit me, got into an accident, water damage, fire damage, theft, break-in, vandalism, roof damage, storm damage, hail damage, flooded, pipe burst, need to report a claim
  - [x] Write tests for claims flow (25 tests passing, 3 skipped for pending carrier numbers)
  - [x] TODO markers added for pending client input:
    - Claims ring group extension(s) for business hours
    - Full list of carrier claims phone numbers
    - Holiday schedule for after-hours definition

### Conversation Intelligence
- [x] **Context awareness for insurance type**
- [x] **Confirmation before transfer**

### Testing
- [x] Write comprehensive tests for staff directory (62 tests)
- [x] Write tests for new quote flow (19 tests)
- [x] Write tests for payment/ID-Dec flow (6 tests)
- [x] Write tests for restricted transfers (3 tests)
- [x] Write tests for ring groups (4 tests)

### Business Hours Awareness (Completed 2026-01-13)
- [x] Create `src/business_hours.py` module with comprehensive configuration
  - Timezone: America/New_York (Eastern Time)
  - Schedule: Monday-Friday, 9 AM to 5 PM
  - Saturday/Sunday: Closed
- [x] Implement core helper functions:
  - `get_current_time()` - Returns current time in Eastern timezone
  - `is_office_open(now=None)` - Returns True/False for business hours (testable with optional datetime)
  - `get_next_open_time(now=None)` - Returns human-friendly string ("tomorrow at 9 AM", "Monday at 9 AM", "in about 30 minutes")
  - `get_business_hours_context()` - Returns dict with current_time, is_open, next_open_time, office_hours
  - `format_business_hours_prompt()` - Returns formatted prompt context block
- [x] Inject business hours context into LLM prompts:
  - Assistant instructions include `CURRENT TIME` and `OFFICE STATUS` headers
  - Example: "CURRENT TIME: 3:45 PM ET, Tuesday" / "OFFICE STATUS: Open (closes at 5 PM)"
  - Contextual guidance for hours questions (responds differently if open vs closed)
- [x] Update `provide_hours_and_location` tool for contextual responses
- [x] Write comprehensive tests (129 tests in test_business_hours.py):
  - Edge cases: exactly at 9 AM (open), exactly at 5 PM (closed)
  - DST handling (spring forward, fall back)
  - Year boundary handling (New Year's)
  - Timezone consistency tests
- [x] TODO markers added for pending client input:
  - Holiday schedule support (future enhancement)
  - Special hours (early close days)

### After-Hours Voicemail Flow (Completed 2026-01-13)
- [x] Create `AfterHoursAgent` class for handling after-hours callers
  - After-hours greeting: "Our office is currently closed. We're open Monday through Friday, 9am to 5pm Eastern."
  - Collects name, phone, business/personal, identifier (business name or spelled last name)
  - Offers voicemail transfer to appropriate agent
- [x] Implement `transfer_to_voicemail` function with alpha-split routing
  - Personal Lines: A-G → Yarislyn, H-M → Al, N-Z → Luis (Account Executives)
  - Commercial Lines: A-F → Adriana, G-O → Rayvon, P-Z → Dionna (Account Executives)
  - Routes to Account Executives (not sales agents) since existing clients call after hours
- [x] Update Assistant with `on_enter` method for automatic after-hours detection
  - Uses `_is_after_hours` flag (testable via `is_after_hours` parameter)
  - Generates appropriate greeting based on office status
- [x] Add `route_call_after_hours` function tool for manual routing
- [x] Exception intents that skip voicemail (handled normally after hours):
  - CLAIMS → ClaimsAgent (provides carrier numbers after hours)
  - HOURS_LOCATION → Answered directly by `provide_hours_and_location`
  - CERTIFICATES → MortgageeCertificateAgent (provides email)
  - MORTGAGEE → MortgageeCertificateAgent (provides email)
- [x] Write tests for after-hours voicemail flow (20+ tests in TestAfterHoursVoicemailFlow)
  - Note: Some LLM-judged tests have strict rubrics that may cause flaky failures
- [x] TODO marker added: Voicemail extension format (same as agent ext, or separate system?)

### Latency Optimizations (Completed 2026-01-13)
- [x] Tune Silero VAD parameters (min_silence_duration=0.3s, min_speech_duration=0.05s)
- [x] Configure AssemblyAI STT via extra_kwargs (end_of_turn_confidence_threshold=0.5, min_end_of_turn_silence_when_confident=300ms)
- [x] Optimize AgentSession timing (min_endpointing_delay=0.3s, max_endpointing_delay=1.5s, min_interruption_duration=0.3s)
- [x] Create `docs/LATENCY_TUNING.md` with parameter reference and tuning guidelines

### P0 Bug Fixes (Completed 2026-01-07)
- [x] Fix IndexError on empty last name string (4 locations - now uses `len() > 0` check)
- [x] Fix type mismatch in fallback transfer (simplified to use data sheet fallback)
- [x] Remove duplicate `AgentConfig`/`AlphaSplitConfig` classes (replaced with `HOLD_MESSAGE`)
- [x] Fix agent name mismatch in `livekit.toml` (changed "Lucy" to "Aizellee")
- [x] Update ruff `target-version` from "py39" to "py310" in `pyproject.toml`
- [x] Replace generic README.md with project-specific version
- [x] Add return type annotations (`-> str`) to all `@function_tool` methods
- [x] Add PII masking utilities for logging (`mask_phone()`, `mask_name()`)
- [x] Add error handling try/catch blocks to session initialization
- [x] Add environment variable validation on startup (`validate_environment()`)
- [x] Create `tests/conftest.py` with shared fixtures
- [x] Add security tests (prompt injection resistance)
- [x] Add edge case tests (17 new tests for unicode, special chars, etc.)
- [x] Create `docs/OPERATIONS.md` (comprehensive operator guide)
- [x] Add pytest markers (slow, unit, integration)

---

## Critical (P0) - Must Fix Before Production

### Configuration
- [ ] Commit `uv.lock` and `livekit.toml` to version control

---

## High Priority (P1) - Should Fix

### Code Quality
- [ ] Consolidate 8 routing tools into single parameterized tool (~400 token savings)

### Testing
- [ ] Add error handling tests

---

## Medium Priority (P2) - Recommended

### Features
- [ ] Implement time block awareness for agent availability
- [ ] Implement actual ring group calling logic
- [ ] Externalize staff directory to JSON config file

### Code Quality
- [ ] Replace `Optional[X]` with `X | None` syntax throughout
- [ ] Use match statements for fallback mode handling
- [ ] Add state validation to CallerInfo dataclass
- [ ] Fix bidirectional name matching in `get_agent_by_name`
- [ ] Add phone number format validation

### Testing
- [ ] Strengthen LLM-judged test intents with negative constraints
- [ ] Add test helper functions to reduce code duplication

### Documentation
- [x] Create `docs/ARCHITECTURE.md` (system architecture)
- [x] Add module docstring to `agent.py`
- [x] Document CallIntent enum with routing descriptions

### Prompts
- [ ] Remove duplicate personality sections from sub-agents (~240 token savings)
- [ ] Move static info (hours, address) to tool outputs (~150 token savings)
- [ ] Add edge case handling instructions to prompts
- [ ] **Improve business context detection**: "work truck", "company vehicle", "fleet" should auto-infer business insurance without asking (currently asks for confirmation)

---

## Low Priority (P3) - Nice to Have

### Code Quality
- [ ] Add `slots=True` to dataclasses for performance
- [ ] Split large `agent.py` into smaller modules
- [ ] Add mypy configuration to `pyproject.toml`
- [ ] Remove unused `NEW_QUOTE_KEYWORDS` and `PAYMENT_IDDEC_KEYWORDS` constants
- [ ] Move hardcoded Cartesia voice ID to config

### Architecture
- [ ] Pre-instantiate sub-agents instead of creating on handoff
- [ ] Add structured logging with correlation IDs
- [ ] Add custom metrics (intent distribution, transfer success rate)

### Documentation
- [ ] Create CHANGELOG.md
- [ ] Standardize confirmation template across all agents

---

## Pending - Needs Client Input

- [ ] **Fallback routing**: Confirm preferred fallback mode
- [ ] **SIP transfer**: Implement actual SIP transfer when phone system configured
- [ ] **SIP domain**: Get PBX domain for transfer URLs

### MakeChangeAgent, CancellationAgent & SomethingElseAgent Specific
- [ ] **AE Fallback Routing**: When assigned Account Executive is unavailable, what should happen?
  - Option A: Take a message/data sheet for callback (current behavior)
  - Option B: Ring all Account Executives in the department simultaneously
  - Option C: Ring a specific backup agent
  - Option D: Transfer to VA ring group
- [ ] **Hold Timeout**: How long should caller wait on hold before fallback triggers?
- [ ] **Data Sheet Storage**: Where should data sheets be sent/stored? (email, CRM, database)

### Warm Transfer (SomethingElseAgent)
- [ ] **Warm Transfer Method**: How should the warm transfer handoff work technically?
  - Option A: Conference call (agent stays on briefly to introduce caller)
  - Option B: Whisper to agent first (agent hears context before caller joins)
  - Option C: Consultation room pattern (LiveKit native, full context exchange)
- [ ] **Context Relay Format**: What info should be relayed to the receiving agent?
  - Caller name, phone number, insurance type, summary (current implementation)
  - Additional context: caller mood, urgency level, previous attempts?

### MortgageeCertificateAgent Specific
- [ ] **Login Credential Resend**: If caller needs login credentials resent, who handles that?
  - Option A (current): Collect email and trigger automated resend
  - Option B: Transfer to VA/CSR ring group for manual credential reset
- [ ] **App Download Links**: Should we provide download links for the Harry Levine Insurance app?
  - iOS App Store link?
  - Google Play link?

### ClaimsAgent Specific
- [ ] **Claims Ring Group Extension(s)**: What extension(s) should handle claims during business hours?
  - TODO: Get claims team extension(s) from client
  - Current behavior: Mock transfer with log message
- [ ] **Verify Carrier Claims Numbers**: Placeholder numbers added for all major carriers - VERIFY before production
  - National carriers (need verification): Progressive, Travelers, Hartford, Liberty Mutual, State Farm, Allstate, GEICO, Nationwide, USAA, Farmers, American Family, Auto-Owners, Erie, Safeco
  - Florida regional carriers (FAKE 555 numbers): Citizens, Florida Peninsula, Universal Property, Tower Hill, Heritage, People's Trust, Security First

### Business Hours Specific
- [ ] **Holiday Schedule**: Does the office close for holidays?
  - Current: Only weekends (Sat/Sun) are after-hours
  - Needed: Federal holidays, office-specific closures
  - Implementation ready: Add holiday dates to `business_hours.py`
- [ ] **Special Hours Days**: Any early close days (e.g., close at 3pm on Fridays)?
  - Current: M-F 9am-5pm standard hours
  - Implementation: Modify WEEKLY_SCHEDULE in business_hours.py
- [ ] **Holiday Calendar Format**: Preferred format for holiday configuration?
  - Option A: Hard-coded Python dict (simple, requires code update annually)
  - Option B: External JSON/YAML config file (easier updates)
  - Option C: API integration (e.g., Google Calendar, iCalendar feed)

---

## Future Enhancements

- [ ] Implement on-hold music/periodic check-in during transfers
- [ ] Add call recording and transcription logging
- [ ] Implement agent availability checking (phone system integration)
- [ ] Add analytics and reporting for call routing
- [ ] Implement semantic caching for common queries
- [ ] Add feature flag system

---

## Review Report

See `docs/REVIEW_AUDIT_REPORT.md` for the full multi-agent analysis including:
- Code quality assessment
- Test coverage gaps
- Documentation requirements
- Prompt optimization opportunities
- Architecture recommendations

---

*Last updated: 2026-01-13 (Business Hours Awareness module added with prompt context injection)*
