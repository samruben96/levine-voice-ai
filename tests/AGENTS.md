<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-11 -->

# tests/

## Purpose
Test suite for the Harry Levine Insurance Voice Agent. Organized into fast unit tests (no API calls) and slower integration tests (use real LLM inference). Uses pytest with pytest-asyncio for async test support.

## Key Files

| File | Description |
|------|-------------|
| `conftest.py` | **Root conftest** — Shared fixtures: agent session factories, CallerInfo presets, mock contexts, event-skipping helpers (`skip_function_events`), conversation helpers (`run_conversation`), intent templates, test markers |
| `test_agent.py` | Original monolithic test file (kept for CI compatibility). Tests error handling, caller info validation, phone validation |
| `test_staff_directory.py` | Staff directory routing tests: alpha-split logic, department lookups, restricted transfers, ring groups, prefix exceptions ("The", "Law office of"), name disambiguation (`TestGetAgentsByNamePrefix`) |
| `test_business_hours.py` | Business hours tests: open/closed checks, lunch hour, next-open-time calculations, timezone handling, prompt formatting |
| `test_utils.py` | Utility function tests: PII masking, phone validation, environment validation, email formatting, route logging |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `unit/` | Fast unit tests (~0.03s), no external API calls (see `unit/AGENTS.md`) |
| `integration/` | LLM integration tests (~30s each), require OpenAI API key (see `integration/AGENTS.md`) |

## For AI Agents

### Working In This Directory
- **NEVER run the full test suite during development** — it takes 10-20 minutes due to LLM API calls
- **Use TDD** when modifying agent instructions, tool descriptions, or handoff behavior
- **Root conftest.py** provides shared fixtures used by both unit and integration tests
- **Subdirectory conftest.py** files provide test-level-specific fixtures (mocks for unit, real LLM for integration)
- **Event skipping**: Always use `skip_function_events(result)` before checking message events in integration tests

### Quick Reference: Test Commands

| Situation | Command | Time |
|-----------|---------|------|
| During development | `.venv/bin/python -m pytest tests/unit/ -v` | ~0.03s |
| After changing a flow | `.venv/bin/python -m pytest tests/integration/test_<flow>.py -v` | ~30s |
| Before commit | `.venv/bin/python -m pytest -m smoke -v` | ~30s |
| Full suite (CI only) | `.venv/bin/python -m pytest tests/ -v` | 10-20min |

### Available Markers
```bash
-m unit          # Unit tests only
-m smoke         # Critical path smoke tests
-m security      # Security and prompt injection tests
-m "not slow"    # Skip slow tests
-m after_hours   # After-hours specific tests
-m mortgagee     # Mortgagee/bank caller tests
```

### Common Patterns
- Session fixtures: `assistant_session`, `claims_session`, `mortgagee_session`, `after_hours_session`
- Factory: `create_agent_session(AgentClass, userdata=CallerInfo(...))` for parametrized tests
- Assertion intents: Use `INTENTS` dict for consistent assertion strings
- Business hours context: Use `CONTEXT_OPEN`, `CONTEXT_CLOSED_EVENING` etc. from integration conftest

## Dependencies

### Internal
- `src/` — All agent classes, models, utilities imported via `sys.path.insert(0, "src")`

### External
- `pytest` / `pytest-asyncio` — Test framework
- `livekit.agents` — `AgentSession`, `inference` for integration tests
- `unittest.mock` — `MagicMock`, `AsyncMock` for unit tests

<!-- MANUAL: -->
