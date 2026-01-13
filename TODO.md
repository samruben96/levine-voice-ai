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

### Conversation Intelligence
- [x] **Context awareness for insurance type**
- [x] **Confirmation before transfer**

### Testing
- [x] Write comprehensive tests for staff directory (62 tests)
- [x] Write tests for new quote flow (19 tests)
- [x] Write tests for payment/ID-Dec flow (6 tests)
- [x] Write tests for restricted transfers (3 tests)
- [x] Write tests for ring groups (4 tests)

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

### MakeChangeAgent Specific
- [ ] **AE Fallback Routing**: When assigned Account Executive is unavailable, what should happen?
  - Option A: Ring all Account Executives in the department
  - Option B: Ring a specific backup agent
  - Option C: Take a message for callback (current behavior)
  - Option D: Transfer to VA ring group
- [ ] **Hold Timeout**: How long should caller wait on hold before fallback triggers?

---

## Future Enhancements

- [ ] Add more intent handlers (claims, cancellations)
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

*Last updated: 2026-01-07 (MakeChangeAgent added)*
