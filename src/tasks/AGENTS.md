<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-11 | Updated: 2026-03-02 -->

# tasks/

## Purpose
Reusable LiveKit task modules for scoped sub-conversations within the voice agent. Tasks temporarily take control of the session to accomplish a specific goal (e.g., collecting contact info, capturing DTMF input) and return structured results to the parent agent.

## Key Files

| File | Description |
|------|-------------|
| `collect_contact.py` | `CollectContactInfoTask` — AgentTask that collects first name, last name, and phone number one question at a time. Returns `ContactInfoResult` dataclass and writes to `CallerInfo` userdata |
| `phone_collection.py` | `collect_phone_number_dtmf()` — Collects phone numbers via DTMF keypad entry (with speech fallback) for SIP/telephony callers using `GetDtmfTask`. Also provides `is_sip_caller()` utility |
| `__init__.py` | Exports `CollectContactInfoTask` and `ContactInfoResult` |

## For AI Agents

### Working In This Directory
- **Tasks vs Agents**: Tasks are short-lived, scoped sub-conversations. They take control of the session briefly and return a result. Agents handle entire conversation flows
- **AgentTask pattern**: `CollectContactInfoTask` extends `AgentTask[T]` and calls `self.complete(result)` when done
- **DTMF module**: `phone_collection.py` uses LiveKit's beta `GetDtmfTask` API with graceful fallback if unavailable
- **SIP detection**: Use `is_sip_caller()` to check if the caller is on a phone (vs web/app) before offering keypad input
- **Chat context**: Both tasks accept `chat_ctx` to maintain conversation continuity

### Testing Requirements
- Unit tests: `.venv/bin/python -m pytest tests/unit/test_collect_contact_task.py tests/unit/test_phone_collection.py -v`
- Tasks use `CallerInfo` userdata — ensure `context.userdata` fields are set correctly

### Common Patterns
- `AgentTask[ContactInfoResult]` with typed result via `self.complete()`
- `@function_tool` for the LLM to call when info is collected
- `chat_ctx.copy(exclude_instructions=True)` for clean context passing to sub-tasks
- Graceful fallback: try beta API, catch exception, return None

## Dependencies

### Internal
- `../models.py` — `CallerInfo` (userdata type for RunContext)
- `../utils.py` — `mask_name`, `mask_phone` for PII-safe logging

### External
- `livekit.agents` — `AgentTask`, `RunContext`, `function_tool`, `get_job_context`
- `livekit.agents.beta.workflows.dtmf_inputs` — `GetDtmfTask` (beta API)
- `livekit.rtc` — `ParticipantKind` for SIP detection

<!-- MANUAL: -->
