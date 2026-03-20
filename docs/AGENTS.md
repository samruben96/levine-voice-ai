<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-11 | Updated: 2026-03-02 -->

# docs/

## Purpose
Project documentation covering architecture, operations, audits, and feature-specific reference material. These are developer-facing documents, not user-facing docs.

## Key Files

| File | Description |
|------|-------------|
| `OPERATIONS.md` | **Primary ops guide** — Staff directory management, routing configuration, adding/removing staff, alpha-split rules |
| `ARCHITECTURE.md` | System architecture overview, agent hierarchy, data flow |
| `LATENCY_TUNING.md` | Voice latency optimization: STT, TTS, VAD, turn detection, endpointing parameters |
| `BANK_CALLER_FLOW.md` | Bank caller handling flow documentation |

## For AI Agents

### Working In This Directory
- **Read before modifying**: Check relevant docs before making architectural changes
- **OPERATIONS.md is critical**: Must be updated when staff directory or routing rules change
- **Bank caller docs**: `BANK_CALLER_FLOW.md` is the reference for the bank caller feature

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
