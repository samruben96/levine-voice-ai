<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-11 | Updated: 2026-03-02 -->

# src/

## Purpose
Application source code for the Harry Levine Insurance Voice Agent. Contains the LiveKit Agents voice pipeline, all agent classes, routing logic, business hours management, and supporting utilities. This is where all production runtime code lives.

## Key Files

| File | Description |
|------|-------------|
| `main.py` | Server entry point: `AgentServer` setup, prewarm, `my_agent()` session handler. Run with `uv run python src/main.py dev` |
| `agent.py` | Backwards-compatibility wrapper that re-exports all public symbols. Also serves as CLI entry point (`uv run python src/agent.py dev`) |
| `models.py` | Core data models: `CallerInfo` (call state dataclass), `CallIntent` (16 routing intents), `InsuranceType` enum |
| `staff_directory.py` | Staff directory data (18 members) and alpha-split routing functions (`find_agent_by_alpha`, `get_alpha_route_key`, `get_agents_by_name_prefix` for disambiguation, etc.) |
| `business_hours.py` | Business hours logic (M-F 9-5 ET), lunch hour detection (`is_lunch_hour()` for 12-1 PM), timezone handling, LLM context generation (`format_business_hours_prompt` with Lunch/Open/Closed status) |
| `instruction_templates.py` | Reusable LLM instruction fragments and composition helpers. Reduces token duplication ~8-14% across agent prompts |
| `constants.py` | Hold messages, carrier claims phone numbers dict, `get_carrier_claims_number()` lookup |
| `utils.py` | PII masking (`mask_phone`, `mask_name`), phone validation, email formatting for TTS (`format_email_for_speech` — reads normally then spells), structured route logging |
| `__init__.py` | Package init, exports `__version__ = "1.0.0"` |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `agents/` | Specialized agent classes (see `agents/AGENTS.md`) |
| `tasks/` | LiveKit task modules for scoped sub-conversations (see `tasks/AGENTS.md`) |

## For AI Agents

### Working In This Directory
- **Entry point**: `main.py` is the real entry point; `agent.py` is a compatibility wrapper
- **Imports**: All modules use flat imports (e.g., `from models import CallerInfo`) because `pyproject.toml` sets `pythonpath = src/`
- **Voice pipeline**: Configured in `main.py` — STT (AssemblyAI → Deepgram fallback), LLM (GPT-4.1 → GPT-4.1-mini fallback), TTS (Cartesia Sonic-3 with fallback voice), VAD (Silero), Turn Detection (Multilingual). All providers wrapped in FallbackAdapters for resilience
- **Staff routing**: Alpha-split logic in `staff_directory.py` handles "The" and "Law office(s) of" prefix exceptions
- **Business hours**: Always use `business_hours.py` functions; never hardcode time checks
- **Instruction templates**: Use `compose_instructions()` from `instruction_templates.py` for new agent prompts to maintain consistency

### Testing Requirements
- Unit tests: `.venv/bin/python -m pytest tests/unit/ -v` (~0.03s)
- After changing routing logic: `.venv/bin/python -m pytest tests/unit/test_staff_directory.py -v`
- After changing business hours: `.venv/bin/python -m pytest tests/unit/test_business_hours.py -v`
- After changing agent behavior: Run the relevant integration test file

### Common Patterns
- Agents inherit from `Agent` (LiveKit)
- `CallerInfo` is passed as `userdata` on `AgentSession` and accessed via `context.userdata`
- PII is always masked before logging using `mask_name()` / `mask_phone()`
- Transfer tools use `@function_tool` decorator from LiveKit Agents
- Route decisions are logged via `log_route_decision()` for observability

## Dependencies

### Internal
- `agents/` — all specialized agent classes
- `tasks/` — scoped task modules for sub-conversations

### External
- `livekit-agents[silero,turn-detector]~=1.4` — LiveKit Agents framework (SDK 1.4.1)
- `livekit-plugins-noise-cancellation~=0.2` — Background voice cancellation
- `python-dotenv` — Environment variable loading

<!-- MANUAL: -->
