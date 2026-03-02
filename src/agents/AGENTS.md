<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-11 | Updated: 2026-03-02 -->

# agents/

## Purpose
Specialized agent classes for handling different conversation flows in the voice agent. Each agent handles a specific caller intent or scenario, receiving handoffs from the main Assistant agent.

## Key Files

| File | Description |
|------|-------------|
| `assistant.py` | **Main entry point agent**. Front-desk receptionist that handles initial intake, intent detection, and most routing directly via transfer tools. Hands off to sub-agents only for claims, mortgagee/certificates, and after-hours flows |
| `claims.py` | `ClaimsAgent` — Handles claims with business-hours detection. During hours: transfers to claims ring group. After hours: looks up carrier 24/7 claims numbers |
| `mortgagee.py` | `MortgageeCertificateAgent` — Handles COI and mortgagee requests. New certificates: provides email. Existing certificates: transfers to AE. Mortgagee: provides email |
| `after_hours.py` | `AfterHoursAgent` — After-hours voicemail flow. Collects caller info, routes to appropriate agent's voicemail via alpha-split |
| `__init__.py` | Exports all 4 agent classes: `Assistant`, `ClaimsAgent`, `MortgageeCertificateAgent`, `AfterHoursAgent` |

## Agent Architecture

```
Assistant (main entry point)
├── Direct transfer tools (quote, payment, change, cancellation, coverage, something_else, bank_caller)
├── Handoff → ClaimsAgent (claims flow)
├── Handoff → MortgageeCertificateAgent (certificates, mortgagee)
└── Handoff → AfterHoursAgent (after-hours voicemail)
```

## For AI Agents

### Working In This Directory
- **Single-agent architecture**: The `Assistant` handles most routing directly via `@function_tool` transfer functions. Only 3 sub-agents receive handoffs
- **No double-asking**: Transfer tools in `assistant.py` already have caller info from the Assistant's conversation context. Sub-agents should NOT re-collect info already gathered
- **Agent screening**: ALL specific agent requests go through a "what is this in reference to?" screening step before transfer
- **Name disambiguation**: When multiple agents share a name prefix (e.g., "Rachel"), `get_agents_by_name_prefix()` returns all matches for disambiguation. Exact matches via `get_agent_by_name()` take priority
- **Handoff speech**: The `_handoff_speech_delivered` flag on `CallerInfo` prevents duplicate transfer messages during handoffs
- **Business hours**: `ClaimsAgent` and `Assistant` both check business hours. Assistant also imports `is_lunch_hour` to distinguish lunch break from after-hours in greetings. Use constructor params (`is_business_hours`, `is_after_hours`) for testability
- **Instruction composition**: Use `compose_instructions()` and template fragments from `instruction_templates.py` for prompt construction
- **Security instructions**: Every agent MUST include `SECURITY_INSTRUCTIONS` from `instruction_templates.py`

### Testing Requirements
- After modifying `assistant.py`: Run relevant integration tests (e.g., `tests/integration/test_quote_flow.py`)
- After modifying `claims.py`: `.venv/bin/python -m pytest tests/integration/test_claims_flow.py -v`
- After modifying `mortgagee.py`: `.venv/bin/python -m pytest tests/integration/test_mortgagee_cert.py -v`
- After modifying `after_hours.py`: `.venv/bin/python -m pytest tests/integration/test_after_hours.py -v`
- Always run unit tests: `.venv/bin/python -m pytest tests/unit/ -v`

### Common Patterns
- Agents inherit from `Agent` (LiveKit) with `instructions` kwarg
- `on_enter()` handles initial greeting/behavior when agent becomes active
- `@function_tool` for transfer/routing tools; return strings for TTS output
- `RunContext[CallerInfo]` provides typed access to caller state
- `AgentSession.generate_reply()` triggers the LLM to speak after programmatic actions

## Dependencies

### Internal
- `../models.py` — `CallerInfo`, `CallIntent`, `InsuranceType`
- `../staff_directory.py` — Alpha-split routing, agent lookup
- `../business_hours.py` — Office hours checks and prompt context
- `../instruction_templates.py` — Shared prompt fragments
- `../constants.py` — Hold messages, carrier claims numbers
- `../utils.py` — PII masking, route logging, email formatting

### External
- `livekit.agents` — `Agent`, `RunContext`, `function_tool`, `AgentSession`
- `livekit.agents.beta.tools` — `EndCallTool` (used in `after_hours.py` to end calls)

<!-- MANUAL: -->
