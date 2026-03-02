<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-11 | Updated: 2026-03-02 -->

# unit/

## Purpose
Fast unit tests that run without external API calls or LLM inference. These tests validate data models, utility functions, instruction templates, and agent configuration logic. Run in ~0.03 seconds.

## Key Files

| File | Description |
|------|-------------|
| `conftest.py` | Unit-specific fixtures: mock LLM, mock sessions with tracking, CallerInfo variants (empty, complete personal, complete business, partial) |
| `test_caller_info.py` | `CallerInfo` dataclass tests: initialization, `is_ready_for_routing()`, `has_insurance_identifier()`, `to_safe_log()` |
| `test_phone_validation.py` | Phone validation and normalization: valid formats, edge cases, international numbers |
| `test_environment.py` | Environment variable validation: missing vars, partial configs, error messages |
| `test_carrier_claims.py` | Carrier claims number lookup: exact match, case-insensitive, partial prefix, unknown carriers |
| `test_agent_instructions.py` | Agent instruction validation: security instructions present, instruction composition, template consistency |
| `test_handoff_speech.py` | Handoff speech deduplication: `_handoff_speech_delivered` flag behavior across agent transfers |
| `test_route_logging.py` | Structured route decision logging: PII masking in logs, log format validation |
| `test_lunch_hour.py` | Lunch hour handling: `is_lunch_hour()` 12-1 PM detection, `_find_next_opening()` returns 1 PM during lunch, `format_business_hours_prompt()` shows "Lunch" status, Assistant `_is_lunch`/`_is_after_hours` flags, greeting content |
| `test_collect_contact_task.py` | Tests for the contact info collection task: instructions, tool configuration |
| `test_phone_collection.py` | Tests for the DTMF+speech phone collection task: SIP and non-SIP flows |
| `__init__.py` | Package marker |

## For AI Agents

### Working In This Directory
- **Run frequently**: These tests are instant (~0.03s) — run after every code change
- **No API keys needed**: All external dependencies are mocked
- **Command**: `.venv/bin/python -m pytest tests/unit/ -v`
- **Marker**: All tests should have `@pytest.mark.unit`
- **Mock patterns**: Use `MagicMock` for sync, `AsyncMock` for async. See `conftest.py` for examples

### Testing Requirements
- New utility functions in `src/utils.py` should have corresponding tests here
- New model fields on `CallerInfo` should be tested in `test_caller_info.py`
- Lunch hour or business hours changes should be tested in `test_lunch_hour.py`
- New carrier numbers should be tested in `test_carrier_claims.py`
- Agent instruction changes should be validated in `test_agent_instructions.py`

### Common Patterns
- Fixtures from `conftest.py`: `empty_caller_info`, `complete_caller_info_personal`, `mock_llm`, `mock_agent_session_full`
- Direct function testing (no agent sessions needed for most unit tests)
- PII masking assertions: verify masked output format, never assert on raw PII

## Dependencies

### Internal
- `src/agent.py` — Re-exports used for backwards-compatible imports
- `src/models.py`, `src/utils.py`, `src/constants.py` — Direct test targets

### External
- `pytest` — Test framework
- `unittest.mock` — `MagicMock`, `AsyncMock`

<!-- MANUAL: -->
