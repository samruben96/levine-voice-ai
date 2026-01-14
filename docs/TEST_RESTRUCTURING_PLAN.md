# Test Restructuring Plan

![Status: IMPLEMENTED](https://img.shields.io/badge/Status-IMPLEMENTED-brightgreen)

**Completed:** 2026-01-14 (Phase 4)

This document outlines the comprehensive test restructuring that was implemented for the Harry Levine Insurance Voice Agent project.

> **Status:** This plan has been fully implemented. The test suite has been reorganized into a modular structure with 270 tests across unit and integration directories, plus 121 tests in the original compatibility files.

## Executive Summary

**Current State:**
- `tests/test_agent.py`: ~6,800 lines, 159 async tests, ALL hitting external OpenAI API
- `tests/test_staff_directory.py`: ~745 lines, 62 unit tests (good - no changes needed)
- `tests/test_business_hours.py`: ~1,500 lines, 129 tests (good - no changes needed)
- `tests/test_base_routing.py`: ~1,063 lines, 41 tests (NEW - BaseRoutingAgent tests)
- `tests/conftest.py`: 97 lines, shared fixtures

**Key Problems:**
1. `test_agent.py` is monolithic and unmaintainable
2. Every test hits external LLM APIs (slow, expensive, flaky)
3. No test markers being used effectively
4. Repeated boilerplate in every test (event skipping, session setup)
5. No mocking strategy - all full integration tests
6. No test isolation - tests cannot run in parallel

**Goals:**
- Split `test_agent.py` into logical, maintainable modules
- Introduce mocking to enable fast unit tests
- Establish clear test categories with pytest markers
- Reduce boilerplate through shared fixtures and helpers
- Enable parallel test execution where safe
- Maintain 100% test coverage during migration

---

## 1. Proposed File Structure

### New Test Directory Layout

```
tests/
  conftest.py                    # Shared fixtures (expanded)

  # Unit tests (no external API calls)
  unit/
    __init__.py
    test_caller_info.py          # CallerInfo dataclass unit tests
    test_phone_validation.py     # validate_phone, mask_phone, mask_name
    test_environment.py          # validate_environment tests
    test_carrier_claims.py       # get_carrier_claims_number tests
    test_agent_instructions.py   # Agent instruction generation tests
    conftest.py                  # Unit test fixtures (mocks)

  # Integration tests (hit external LLM APIs)
  integration/
    __init__.py
    conftest.py                  # Integration test fixtures

    # Core flows (essential)
    test_greeting.py             # Basic greeting tests (~5 tests)
    test_routing.py              # Agent routing tests (~5 tests)
    test_security.py             # Security/prompt injection tests (~5 tests)

    # Intent detection (one file per major intent)
    test_quote_flow.py           # NEW_QUOTE flow (~15 tests)
    test_payment_flow.py         # MAKE_PAYMENT flow (~10 tests)
    test_change_flow.py          # MAKE_CHANGE flow (~20 tests)
    test_cancellation_flow.py    # CANCELLATION flow (~15 tests)
    test_claims_flow.py          # CLAIMS flow (~20 tests)
    test_coverage_rate_flow.py   # COVERAGE_RATE_QUESTIONS flow (~15 tests)
    test_certificate_flow.py     # CERTIFICATES flow (~20 tests)
    test_mortgagee_flow.py       # MORTGAGEE_LIENHOLDERS flow (~15 tests)
    test_something_else_flow.py  # SOMETHING_ELSE flow (~15 tests)

    # After-hours (separate because requires mocked time context)
    test_after_hours.py          # After-hours voicemail flow (~25 tests)
    test_business_hours_context.py # Business hours context injection (~10 tests)

  # Existing files (unchanged)
  test_staff_directory.py        # Keep as-is (pure unit tests)
  test_business_hours.py         # Keep as-is (pure unit tests)
```

### File Size Targets

| File | Current Size | Target Size | Test Count |
|------|-------------|-------------|------------|
| test_agent.py | 6,783 lines | 0 (deleted) | 159 -> 0 |
| unit/test_caller_info.py | N/A | ~100 lines | ~10 |
| unit/test_phone_validation.py | N/A | ~80 lines | ~8 |
| unit/test_environment.py | N/A | ~50 lines | ~5 |
| integration/test_quote_flow.py | N/A | ~400 lines | ~15 |
| integration/test_claims_flow.py | N/A | ~500 lines | ~20 |
| (etc.) | | | |

---

## 2. Test Categorization Strategy

### Pytest Markers

Add the following markers to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    "unit: Unit tests that don't require external services",
    "integration: Integration tests that require LLM API access",
    "slow: Tests that take >5 seconds (all LLM tests)",
    "security: Security and prompt injection tests",
    "after_hours: After-hours specific tests",
    "smoke: Critical path smoke tests (~10 tests)",
]
```

### Marker Application Strategy

| Test Type | Markers | Example |
|-----------|---------|---------|
| CallerInfo validation | `@pytest.mark.unit` | `test_is_ready_for_routing_complete` |
| Phone validation | `@pytest.mark.unit` | `test_validate_phone_valid_10_digits` |
| Environment validation | `@pytest.mark.unit` | `test_validate_environment_missing_vars` |
| Basic greeting | `@pytest.mark.integration`, `@pytest.mark.slow`, `@pytest.mark.smoke` | `test_receptionist_greeting` |
| Security tests | `@pytest.mark.integration`, `@pytest.mark.slow`, `@pytest.mark.security` | `test_agent_resists_role_override` |
| Quote flow | `@pytest.mark.integration`, `@pytest.mark.slow` | `test_new_quote_asks_business_or_personal` |
| After-hours | `@pytest.mark.integration`, `@pytest.mark.slow`, `@pytest.mark.after_hours` | `test_after_hours_greeting_mentions_closure` |

### Running Test Subsets

```bash
# Fast unit tests only (~2 seconds)
pytest -m unit

# Smoke tests for CI (~60 seconds)
pytest -m smoke

# All integration tests (~20 minutes)
pytest -m integration

# Skip slow tests for quick feedback
pytest -m "not slow"

# Security tests only
pytest -m security

# After-hours tests only
pytest -m after_hours
```

---

## 3. Mocking Strategy

### What Can Be Mocked

#### 3.1 LLM Responses (for Unit Tests)

Create mock LLM that returns predictable responses:

```python
# tests/unit/conftest.py

from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_llm():
    """Mock LLM that returns predictable responses."""
    llm = MagicMock()
    llm.__aenter__ = AsyncMock(return_value=llm)
    llm.__aexit__ = AsyncMock()
    return llm

@pytest.fixture
def mock_llm_response():
    """Factory for creating mock LLM responses."""
    def _create_response(content: str):
        response = MagicMock()
        response.content = content
        return response
    return _create_response
```

#### 3.2 AgentSession (for Unit Tests)

Create a mock session that tracks calls without hitting APIs:

```python
# tests/unit/conftest.py

@pytest.fixture
def mock_agent_session():
    """Mock AgentSession for testing agent logic without LLM."""
    session = MagicMock()
    session.say = AsyncMock()
    session.run = AsyncMock()
    session.start = AsyncMock()

    # Track function calls
    session.function_calls = []

    def track_call(name, args):
        session.function_calls.append((name, args))

    session.track_call = track_call
    return session
```

#### 3.3 Business Hours (Already Mockable)

The business hours module already supports time injection:

```python
# Already works - pass custom time to functions
from business_hours import is_office_open
from datetime import datetime

# Mock time for testing
mock_time = datetime(2024, 1, 8, 14, 30)  # Monday 2:30 PM
assert is_office_open(mock_time) is True
```

#### 3.4 Staff Directory (Pure Functions - No Mocking Needed)

Staff directory functions are already pure and testable without mocks.

### What Should NOT Be Mocked (Integration Tests)

The following should use real LLM calls in integration tests:

1. **Intent detection** - LLM must understand natural language
2. **Response quality** - LLM must generate appropriate responses
3. **Conversation flow** - Multi-turn conversations must work end-to-end
4. **Security tests** - Must verify LLM resists injection attacks

### Unit Tests for Tool Functions

Extract and test tool logic separately:

```python
# tests/unit/test_tool_functions.py

from unittest.mock import MagicMock
from agent import CallerInfo, InsuranceType

class TestRecordContactInfoLogic:
    """Test the logic of record_contact_info without LLM."""

    def test_records_name_and_phone(self):
        """Test that name and phone are recorded to CallerInfo."""
        caller = CallerInfo()
        # Test the logic directly
        caller.name = "John Smith"
        caller.phone_number = "555-123-4567"
        assert caller.is_ready_for_routing() is True

    def test_validates_phone_format(self):
        """Test phone validation logic."""
        from agent import validate_phone
        is_valid, normalized = validate_phone("(555) 123-4567")
        assert is_valid is True
        assert normalized == "5551234567"

class TestRecordInsuranceTypeLogic:
    """Test insurance type recording logic."""

    def test_business_sets_type_correctly(self):
        caller = CallerInfo()
        caller.insurance_type = InsuranceType.BUSINESS
        assert caller.insurance_type == InsuranceType.BUSINESS

    def test_personal_sets_type_correctly(self):
        caller = CallerInfo()
        caller.insurance_type = InsuranceType.PERSONAL
        assert caller.insurance_type == InsuranceType.PERSONAL
```

### Creating Deterministic Integration Tests

For integration tests that need LLM, create deterministic scenarios:

```python
# tests/integration/conftest.py

@pytest.fixture
def llm():
    """Real LLM for integration tests."""
    return inference.LLM(model="openai/gpt-4.1-mini")

@pytest.fixture
def deterministic_caller_info():
    """Pre-populated CallerInfo for predictable routing tests."""
    return CallerInfo(
        name="John Smith",
        phone_number="555-123-4567",
        insurance_type=InsuranceType.PERSONAL,
        last_name_spelled="SMITH",  # Routes to M-Z range
    )
```

---

## 4. Parallel Execution Recommendations

### Install pytest-xdist

```bash
uv add pytest-xdist --dev
```

### Tests Safe for Parallel Execution

| Test Category | Safe for Parallel | Reason |
|---------------|-------------------|--------|
| Unit tests (`tests/unit/`) | YES | No shared state |
| Integration tests (different flows) | YES | Each creates own session |
| After-hours tests | YES | Each injects own time context |
| Security tests | YES | Isolated sessions |

### Tests Requiring Isolation

None of the current tests share state that would require isolation. Each test creates its own `AgentSession` and `CallerInfo`.

### Running Tests in Parallel

```bash
# Run with 4 parallel workers
pytest -n 4

# Auto-detect CPU count
pytest -n auto

# Run unit tests in parallel (fastest)
pytest -n auto -m unit

# Run integration tests in parallel (still slow, but faster than serial)
pytest -n 4 -m integration
```

### Estimated Time Savings

| Scenario | Serial Time | Parallel (4 workers) | Savings |
|----------|-------------|---------------------|---------|
| Unit tests only | ~5 sec | ~2 sec | 60% |
| Smoke tests | ~3 min | ~1 min | 66% |
| All integration | ~25 min | ~8 min | 68% |
| Full suite | ~30 min | ~10 min | 66% |

---

## 5. Boilerplate Reduction

### Current Boilerplate Issues

Every test has this repeated pattern (30+ lines per test):

```python
@pytest.mark.asyncio
async def test_something() -> None:
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="...")

        # Skip function calls (10+ lines)
        for _ in range(10):
            result.expect.skip_next_event_if(type="function_call")
            result.expect.skip_next_event_if(type="function_call_output")
        result.expect.skip_next_event_if(type="agent_handoff")

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(llm, intent="...")
        )
```

### Solution 1: Enhanced conftest.py Fixtures

```python
# tests/conftest.py (expanded)

import pytest
from livekit.agents import AgentSession, inference

from agent import Assistant, CallerInfo

@pytest.fixture
def llm():
    """Create LLM instance for tests."""
    return inference.LLM(model="openai/gpt-4.1-mini")

@pytest.fixture
async def assistant_session(llm):
    """Create a started Assistant session."""
    async with (
        llm as llm_ctx,
        AgentSession[CallerInfo](llm=llm_ctx, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())
        yield session, llm_ctx

@pytest.fixture
async def after_hours_session(llm):
    """Create a started Assistant session with after-hours context."""
    context = "CURRENT TIME: 7:30 PM ET, Tuesday\nOFFICE STATUS: Closed (reopens tomorrow at 9 AM)"
    async with (
        llm as llm_ctx,
        AgentSession[CallerInfo](llm=llm_ctx, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant(business_hours_context=context))
        yield session, llm_ctx
```

### Solution 2: Helper Functions in conftest.py

```python
# tests/conftest.py

def skip_function_events(result, max_calls: int = 10, skip_handoff: bool = True):
    """Skip function call events in test results.

    Args:
        result: The test result object.
        max_calls: Maximum number of function calls to skip.
        skip_handoff: Whether to also skip agent_handoff events.
    """
    for _ in range(max_calls):
        result.expect.skip_next_event_if(type="function_call")
        result.expect.skip_next_event_if(type="function_call_output")
    if skip_handoff:
        result.expect.skip_next_event_if(type="agent_handoff")

async def run_and_expect_message(session, llm, user_input: str, intent: str):
    """Run a turn and expect an assistant message matching intent.

    Args:
        session: The AgentSession.
        llm: The LLM for judging.
        user_input: What the user says.
        intent: The expected intent description.
    """
    result = await session.run(user_input=user_input)
    skip_function_events(result)
    await (
        result.expect.next_event()
        .is_message(role="assistant")
        .judge(llm, intent=intent)
    )
    return result
```

### Solution 3: Simplified Test Pattern

With these helpers, tests become:

```python
# Before: 40+ lines
@pytest.mark.asyncio
async def test_receptionist_greeting() -> None:
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())
        result = await session.run(user_input="Hello")
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(llm, intent="...")
        )
        result.expect.no_more_events()

# After: 10 lines
@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.smoke
async def test_receptionist_greeting(assistant_session) -> None:
    session, llm = assistant_session
    await run_and_expect_message(
        session, llm,
        user_input="Hello",
        intent="""
        Greets the caller warmly as Harry Levine Insurance receptionist.
        Should be friendly and offer to help.
        """
    )
```

### Solution 4: Common Intent Patterns

Create reusable intent templates:

```python
# tests/conftest.py

INTENTS = {
    "warm_greeting": """
        Greets the caller in a warm, professional manner as a receptionist.
        Should be friendly, identify as Harry Levine Insurance, and offer to help.
    """,
    "asks_contact_info": """
        Asks for the caller's name and phone number.
        Should mention in case they get disconnected.
    """,
    "asks_business_or_personal": """
        Asks whether this is for business or personal insurance.
        Should be conversational and professional.
    """,
    "shows_empathy": """
        Shows empathy and understanding about the caller's situation.
        Should be warm and supportive, not robotic.
    """,
    "offers_to_transfer": """
        Offers to transfer or connect the caller to the appropriate person.
        Should be helpful and professional.
    """,
}
```

---

## 6. Implementation Order

### Phase 1: Setup Infrastructure (1-2 days)

**Goal:** Prepare the foundation without breaking existing tests.

1. **Add pytest markers to pyproject.toml**
   ```toml
   [tool.pytest.ini_options]
   markers = [
       "unit: Unit tests that don't require external services",
       "integration: Integration tests that require LLM API access",
       "slow: Tests that take >5 seconds (all LLM tests)",
       "security: Security and prompt injection tests",
       "after_hours: After-hours specific tests",
       "smoke: Critical path smoke tests",
   ]
   ```

2. **Install pytest-xdist**
   ```bash
   uv add pytest-xdist --dev
   ```

3. **Create directory structure**
   ```bash
   mkdir -p tests/unit tests/integration
   touch tests/unit/__init__.py tests/integration/__init__.py
   touch tests/unit/conftest.py tests/integration/conftest.py
   ```

4. **Expand tests/conftest.py with helper functions**
   - Add `skip_function_events()` helper
   - Add `run_and_expect_message()` helper
   - Add common fixtures
   - Add intent templates

**Verification:** All existing tests still pass with `pytest tests/`

### Phase 2: Extract Unit Tests (1 day)

**Goal:** Move pure unit tests to `tests/unit/`, reducing `test_agent.py` size.

1. **Create tests/unit/test_caller_info.py**
   - Move `TestCallerInfoValidation` class
   - Add `@pytest.mark.unit` marker

2. **Create tests/unit/test_phone_validation.py**
   - Move `TestPhoneValidation` class
   - Move `test_mask_phone_*` tests
   - Move `test_mask_name_*` tests
   - Add `@pytest.mark.unit` marker

3. **Create tests/unit/test_environment.py**
   - Move `TestErrorHandling` class (env validation)
   - Add `@pytest.mark.unit` marker

4. **Create tests/unit/test_carrier_claims.py**
   - Move `test_carrier_claims_number_lookup_*` tests
   - Add `@pytest.mark.unit` marker

5. **Create tests/unit/test_agent_instructions.py**
   - Move `TestAssistantBusinessHoursContext` class
   - Add `@pytest.mark.unit` marker

**Verification:**
- `pytest tests/unit/` passes (~20 tests)
- `pytest tests/test_agent.py` passes (remaining tests)
- Total test count unchanged

### Phase 3: Extract Integration Test Files (2-3 days)

**Goal:** Split remaining `test_agent.py` into logical feature files.

#### Day 1: Core & Security

1. **Create tests/integration/test_greeting.py** (~5 tests)
   - `test_receptionist_greeting`
   - `test_handles_policy_questions_appropriately`
   - `test_answers_general_insurance_questions`
   - `test_provides_office_hours`
   - `test_stays_on_topic`

2. **Create tests/integration/test_routing.py** (~5 tests)
   - `test_routes_to_claims`
   - `test_routes_to_specific_agent`
   - `test_restricted_transfer_jason`
   - `test_restricted_transfer_fred`
   - `test_normal_agent_transfer`

3. **Create tests/integration/test_security.py** (~5 tests)
   - `test_agent_does_not_reveal_system_prompt`
   - `test_agent_resists_role_override`
   - `test_agent_resists_data_extraction`
   - `test_agent_resists_prompt_injection_in_name`
   - `test_no_hallucinated_prior_context`
   - `test_handles_vague_responses`

#### Day 2: Quote, Payment, Change Flows

4. **Create tests/integration/test_quote_flow.py** (~15 tests)
   - All `test_new_quote_*` tests
   - All `test_*_quote_*` tests
   - `test_collects_contact_info_for_quote`
   - `test_asks_business_or_personal`

5. **Create tests/integration/test_payment_flow.py** (~10 tests)
   - All `test_payment_*` tests

6. **Create tests/integration/test_change_flow.py** (~15 tests)
   - All `test_policy_change_*` tests

#### Day 3: Remaining Flows

7. **Create tests/integration/test_cancellation_flow.py** (~15 tests)
   - All `test_cancellation_*` tests

8. **Create tests/integration/test_claims_flow.py** (~20 tests)
   - All `test_claims_*` tests

9. **Create tests/integration/test_coverage_rate_flow.py** (~15 tests)
   - All `test_coverage_rate_*` tests

10. **Create tests/integration/test_certificate_flow.py** (~15 tests)
    - All `test_certificate_*` tests

11. **Create tests/integration/test_mortgagee_flow.py** (~15 tests)
    - All `test_mortgagee_*` tests
    - `test_unclear_certificate_vs_mortgagee_request`

12. **Create tests/integration/test_something_else_flow.py** (~10 tests)
    - All `test_something_else_*` tests

### Phase 4: After-Hours Tests (1 day)

**Goal:** Extract after-hours tests into dedicated files.

1. **Create tests/integration/test_after_hours.py**
   - Move entire `TestAfterHoursVoicemailFlow` class
   - Add `@pytest.mark.after_hours` marker to all tests

2. **Create tests/integration/test_business_hours_context.py**
   - `test_hours_response_contextual_when_open`
   - `test_hours_response_contextual_when_closed`
   - Business hours context injection tests

### Phase 5: Delete Original & Verify (1 day)

**Goal:** Complete migration and verify coverage.

1. **Verify all tests migrated**
   ```bash
   # Should have same total test count
   pytest --collect-only | grep "test session starts"
   ```

2. **Delete test_agent.py**
   ```bash
   git rm tests/test_agent.py
   ```

3. **Run full test suite**
   ```bash
   pytest tests/
   ```

4. **Run tests by category**
   ```bash
   pytest -m unit           # Fast unit tests
   pytest -m smoke          # Smoke tests
   pytest -m integration    # All integration tests
   pytest -m security       # Security tests
   pytest -m after_hours    # After-hours tests
   ```

5. **Run parallel tests**
   ```bash
   pytest -n 4              # Parallel execution
   ```

### Phase 6: Add Missing Unit Tests (Optional, 1-2 days)

**Goal:** Increase unit test coverage by adding mocked tests.

1. **Add mocked AgentSession tests**
   - Test agent initialization
   - Test instruction generation
   - Test handoff conditions

2. **Add tool function unit tests**
   - Test recording functions logic
   - Test routing decision logic
   - Test transfer conditions

---

## 7. Risk Mitigation

### During Migration

1. **Never delete tests until verified migrated**
   - Copy tests to new location
   - Run both old and new tests
   - Delete old only when confident

2. **Use git branches**
   ```bash
   git checkout -b test-restructure
   # Do work
   git checkout main
   pytest tests/  # Verify main still works
   git merge test-restructure
   ```

3. **Track test count**
   ```bash
   # Before migration
   pytest --collect-only 2>&1 | grep "tests collected"
   # 159 tests collected

   # After each phase
   pytest --collect-only 2>&1 | grep "tests collected"
   # Should always equal or exceed 159
   ```

### Test Coverage Verification

1. **Install pytest-cov**
   ```bash
   uv add pytest-cov --dev
   ```

2. **Run coverage before migration**
   ```bash
   pytest --cov=src --cov-report=html tests/
   # Save report as baseline
   ```

3. **Run coverage after migration**
   ```bash
   pytest --cov=src --cov-report=html tests/
   # Compare with baseline
   ```

### Rollback Plan

If issues arise during migration:

```bash
# Revert to main branch state
git checkout main

# Or revert specific changes
git revert <commit-hash>
```

---

## 8. CI/CD Integration

### Recommended CI Workflow

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Install dependencies
        run: uv sync --dev
      - name: Run unit tests
        run: uv run pytest -m unit -v

  smoke-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Install dependencies
        run: uv sync --dev
      - name: Run smoke tests
        run: uv run pytest -m smoke -v
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

  full-tests:
    runs-on: ubuntu-latest
    needs: smoke-tests
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Install dependencies
        run: uv sync --dev
      - name: Run all tests
        run: uv run pytest -n 4 -v
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

---

## 9. Success Metrics

### Quantitative Goals

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Largest test file | 6,783 lines | <500 lines | Achieved |
| Unit test count | ~40 | ~60 | +50% |
| Unit test runtime | ~5s | ~3s | -40% |
| Integration test runtime (serial) | ~25min | ~25min | Same |
| Integration test runtime (parallel, 4 workers) | N/A | ~8min | New |
| Test files | 4 | 20+ | Modular |

### Qualitative Goals

- [ ] Any test file can be understood in <5 minutes
- [ ] New tests can be added without reading entire codebase
- [ ] Tests can be run selectively by feature area
- [ ] CI provides fast feedback (unit tests in <1 min)
- [ ] Full test suite runs in CI within 15 minutes (parallel)
- [ ] Test failures clearly indicate which feature is broken

---

## 10. Timeline Summary

| Phase | Duration | Outcome |
|-------|----------|---------|
| Phase 1: Setup | 1-2 days | Infrastructure ready, no tests broken |
| Phase 2: Unit Tests | 1 day | ~40 tests extracted to `tests/unit/` |
| Phase 3: Integration Tests | 2-3 days | ~100 tests split into feature files |
| Phase 4: After-Hours | 1 day | ~25 tests in dedicated files |
| Phase 5: Cleanup | 1 day | `test_agent.py` deleted, full verification |
| Phase 6: Enhancement | 1-2 days | Additional unit tests added |
| **Total** | **7-10 days** | **Complete restructure** |

---

## Appendix A: Test File Migration Mapping

| Current Test | New Location |
|--------------|--------------|
| `test_receptionist_greeting` | `integration/test_greeting.py` |
| `test_handles_policy_questions_appropriately` | `integration/test_greeting.py` |
| `test_answers_general_insurance_questions` | `integration/test_greeting.py` |
| `test_provides_office_hours` | `integration/test_greeting.py` |
| `test_stays_on_topic` | `integration/test_greeting.py` |
| `test_no_hallucinated_prior_context` | `integration/test_security.py` |
| `test_handles_vague_responses` | `integration/test_security.py` |
| `test_collects_contact_info_for_quote` | `integration/test_quote_flow.py` |
| `test_asks_business_or_personal` | `integration/test_quote_flow.py` |
| `test_routes_to_claims` | `integration/test_routing.py` |
| `test_routes_to_specific_agent` | `integration/test_routing.py` |
| `test_new_quote_*` | `integration/test_quote_flow.py` |
| `test_personal_insurance_asks_for_last_name` | `integration/test_quote_flow.py` |
| `test_business_insurance_asks_for_business_name` | `integration/test_quote_flow.py` |
| `test_personal_quote_transfers_after_last_name` | `integration/test_quote_flow.py` |
| `test_business_quote_transfers_after_business_name` | `integration/test_quote_flow.py` |
| `test_restricted_transfer_*` | `integration/test_routing.py` |
| `test_normal_agent_transfer` | `integration/test_routing.py` |
| `test_payment_*` | `integration/test_payment_flow.py` |
| `test_policy_change_*` | `integration/test_change_flow.py` |
| `test_agent_does_not_reveal_system_prompt` | `integration/test_security.py` |
| `test_agent_resists_*` | `integration/test_security.py` |
| `test_cancellation_*` | `integration/test_cancellation_flow.py` |
| `test_coverage_rate_*` | `integration/test_coverage_rate_flow.py` |
| `test_something_else_*` | `integration/test_something_else_flow.py` |
| `test_certificate_*` | `integration/test_certificate_flow.py` |
| `test_mortgagee_*` | `integration/test_mortgagee_flow.py` |
| `test_claims_*` | `integration/test_claims_flow.py` |
| `test_hours_response_contextual_*` | `integration/test_business_hours_context.py` |
| `TestAfterHoursVoicemailFlow.*` | `integration/test_after_hours.py` |
| `TestErrorHandling.*` | `unit/test_environment.py` |
| `TestCallerInfoValidation.*` | `unit/test_caller_info.py` |
| `TestPhoneValidation.*` | `unit/test_phone_validation.py` |
| `TestAssistantBusinessHoursContext.*` | `unit/test_agent_instructions.py` |
| `test_carrier_claims_number_lookup_*` | `unit/test_carrier_claims.py` |

---

## Appendix B: Fixture Reference

### Current Fixtures (conftest.py)

```python
skip_function_events(result, max_calls, skip_handoff)  # Helper function
caller_info()                    # Empty CallerInfo
caller_info_with_contact()       # CallerInfo with name/phone
caller_info_business()           # CallerInfo for business insurance
caller_info_personal()           # CallerInfo for personal insurance
mock_context()                   # Mock RunContext
mock_agent_session()             # Mock AgentSession
env_with_livekit()               # Patched env vars
```

### Proposed New Fixtures

```python
# tests/conftest.py
llm()                           # Real LLM instance
assistant_session()             # Started Assistant session
after_hours_session()           # Assistant with after-hours context

# tests/unit/conftest.py
mock_llm()                      # Mock LLM
mock_llm_response()             # Factory for mock responses
mock_agent_session_full()       # Full mock session with tracking

# tests/integration/conftest.py
business_hours_context_open()   # "CURRENT TIME: 2:30 PM..."
business_hours_context_closed() # "CURRENT TIME: 7:30 PM..."
weekend_context()               # "CURRENT TIME: 11:00 AM, Saturday..."
```
