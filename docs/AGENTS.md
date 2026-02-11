<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-11 -->

# docs/

## Purpose
Project documentation covering architecture, operations, audits, and feature-specific reference material. These are developer-facing documents, not user-facing docs.

## Key Files

| File | Description |
|------|-------------|
| `OPERATIONS.md` | **Primary ops guide** — Staff directory management, routing configuration, adding/removing staff, alpha-split rules |
| `ARCHITECTURE.md` | System architecture overview, agent hierarchy, data flow |
| `LATENCY_TUNING.md` | Voice latency optimization: STT, TTS, VAD, turn detection, endpointing parameters |
| `LATENCY_AUDIT.md` | Latency audit findings and recommendations |
| `LIVEKIT_USAGE_AUDIT.md` | Audit of LiveKit SDK usage patterns and best practices compliance |
| `OBSERVABILITY_AUDIT_REPORT.md` | Logging and observability audit |
| `PROMPT_ENGINEERING_AUDIT.md` | LLM prompt optimization analysis and recommendations |
| `CALL_FLOW_UX_AUDIT.md` | Call flow UX review and improvement suggestions |
| `REVIEW_AUDIT_REPORT.md` | Comprehensive code review findings |
| `BASE_ROUTING_AGENT_DESIGN.md` | Historical design doc for `BaseRoutingAgent` (superseded by single-agent architecture) |
| `TEST_RESTRUCTURING_PLAN.md` | Test suite restructuring plan (completed) |
| `BANK_CALLER_FLOW.md` | Bank caller handling flow documentation |
| `BANK_CALLER_IMPLEMENTATION.md` | Bank caller feature implementation details |
| `BANK_CALLER_QUICK_REFERENCE.md` | Quick reference card for bank caller handling |
| `BANK_CALLER_DIALOG_FLOW.txt` | Dialog flow diagram for bank callers |
| `BANK_CALLER_REFERENCE_CARD.txt` | Text reference card for bank caller scenarios |

## For AI Agents

### Working In This Directory
- **Read before modifying**: Check relevant docs before making architectural changes
- **OPERATIONS.md is critical**: Must be updated when staff directory or routing rules change
- **Audit docs are read-only**: Audit reports are historical snapshots; don't modify them
- **Bank caller docs**: Comprehensive reference for the bank caller feature; consult before modifying that flow
- **Historical docs**: `BASE_ROUTING_AGENT_DESIGN.md` and `TEST_RESTRUCTURING_PLAN.md` document past decisions

### When to Update
- Staff changes: Update `OPERATIONS.md`
- Latency parameter changes: Update `LATENCY_TUNING.md`
- New features: Consider adding architecture documentation
- Do NOT create new docs unless explicitly requested

## Dependencies

### Internal
- References `src/staff_directory.py` for routing rules
- References `src/main.py` for pipeline configuration

<!-- MANUAL: -->
