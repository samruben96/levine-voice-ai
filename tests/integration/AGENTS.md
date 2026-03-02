<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-11 | Updated: 2026-03-02 -->

# integration/

## Purpose
LLM integration tests that verify actual agent conversation behavior using real API calls to OpenAI GPT-4.1-mini. Each test file covers a specific call flow or feature. Tests take ~30 seconds each and require an `OPENAI_API_KEY`.

## Key Files

| File | Description |
|------|-------------|
| `conftest.py` | Integration-specific fixtures: `_llm()` factory, business hours context strings (`CONTEXT_OPEN`, `CONTEXT_CLOSED_*`), pre-configured session fixtures (`session_during_business_hours`, etc.) |
| `test_greeting.py` | Greeting behavior: warm welcome, identifies as Harry Levine Insurance, business hours vs after-hours greeting |
| `test_quote_flow.py` | New quote routing: business/personal detection, alpha-split to sales agents, context clue inference |
| `test_payment_flow.py` | Payment/document requests: VA ring group routing, ID cards, declarations pages |
| `test_change_flow.py` | Policy change requests: type detection, routing to Account Executives |
| `test_cancellation_flow.py` | Cancellation handling: empathy, info collection, AE routing without retention pressure |
| `test_claims_flow.py` | Claims flow: business hours transfer, after-hours carrier lookup, empathy requirements |
| `test_coverage_rate.py` | Coverage/rate questions: routing to Account Executives, capability boundaries |
| `test_something_else.py` | Catch-all routing: warm transfers, context collection for unknown intents |
| `test_mortgagee_cert.py` | Certificate and mortgagee flows: email provision, new/existing certificate routing |
| `test_after_hours.py` | After-hours behavior: voicemail routing, claims exception handling |
| `test_security.py` | Security tests: prompt injection resistance, role adherence, system prompt protection |
| `test_no_repetition.py` | Verifies agents don't repeat questions or phrases during handoffs |
| `__init__.py` | Package marker |

## For AI Agents

### Working In This Directory
- **Run selectively**: Each test file takes ~30s. Only run the file relevant to your change
- **Requires API key**: `OPENAI_API_KEY` must be set in environment
- **Command**: `.venv/bin/python -m pytest tests/integration/test_<flow>.py -v`
- **TDD required**: When modifying agent instructions or tools, write/update tests FIRST
- **Event skipping**: Always call `skip_function_events(result)` before asserting on message content

### Testing Requirements
- New transfer tools in `assistant.py` need corresponding test cases
- Agent instruction changes should be verified by running relevant flow tests
- Security-sensitive changes MUST pass `test_security.py`
- Handoff changes should pass `test_no_repetition.py`

### Common Patterns
- Session setup: `async with _llm() as llm, AgentSession(...) as session`
- Business hours: Use context strings from `conftest.py` (e.g., `CONTEXT_OPEN`)
- Assertions: Use `.expect.next_event().is_message(role="assistant").matches(intent="...")` pattern
- Multi-turn: Use `run_conversation(session, ["msg1", "msg2"])` from root conftest

## Dependencies

### Internal
- `src/agent.py` — Agent classes and models
- `../conftest.py` — Shared fixtures, event helpers, conversation helpers

### External
- `livekit.agents` — `AgentSession`, `inference.LLM`
- OpenAI API (via `OPENAI_API_KEY`) — Real LLM inference for testing

<!-- MANUAL: -->
