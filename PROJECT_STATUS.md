# Project Status

**Harry Levine Insurance Voice Agent**
**Last Updated:** 2026-03-19
**Status:** Production-ready single-agent architecture with LiveKit SDK 1.4.1

---

## Current Architecture

Single-agent design where the Assistant handles all routing directly using transfer tools. Specialized sub-agents handle only claims, mortgagee/certificate, and after-hours flows.

```
Agent (LiveKit base)
    |
    +-- Assistant (Main agent - handles ALL routing)
    |       +-- transfer_new_quote (tool)
    |       +-- transfer_payment (tool)
    |       +-- transfer_policy_change (tool)
    |       +-- transfer_cancellation (tool)
    |       +-- transfer_coverage_question (tool)
    |       +-- transfer_something_else (tool)
    |       +-- handle_bank_caller (tool)
    |
    +-- ClaimsAgent (handoff for claims-specific flow)
    +-- MortgageeCertificateAgent (handoff for email/self-service)
    +-- AfterHoursAgent (handoff for voicemail routing)
```

### Key Metrics

| Metric | Value |
|--------|-------|
| Agent classes | 4 |
| Transfer tools | 7 (including handle_bank_caller) |
| Unit tests | 490+ (~0.2s) |
| Integration tests | 131 (by feature) |

### Voice Pipeline

| Component | Primary | Fallback |
|-----------|---------|----------|
| STT | AssemblyAI Universal Streaming | Deepgram Nova-3 |
| LLM | OpenAI GPT-4.1 | GPT-4.1-mini |
| TTS | Cartesia Sonic-3 | Alternate Cartesia voice |
| Turn Detection | LiveKit Multilingual Turn Detector | - |
| VAD | Silero VAD | - |

---

## Completed Work

| Phase | Description | Date |
|-------|-------------|------|
| Architecture Simplification | Single-agent with direct transfer tools (eliminated double-asking bug) | 2026-01-14 |
| Test Restructuring | Modular unit/integration test suite with pytest markers | 2026-01-14 |
| Cold Start Fix | `num_idle_processes=2` for warm workers | 2026-01-14 |
| Bank Caller Handling | Direct email response for bank representatives | 2026-01-14 |
| LiveKit Best Practices | SDK 1.4.1, FallbackAdapters, session error handling, observability | 2026-02-11 |
| Client Feedback (Rounds 1-4) | TTS speed, staff routing, pronunciation, pipeline tuning | 2026-03-19 |

---

## Open Items

### Needs Client Input

1. **Claims Ring Group Extensions** - Which extensions handle claims during business hours?
2. **Carrier Claims Numbers** - Some Florida regional carriers may need real numbers verified.

### Remaining Technical Debt

- Few-shot examples for intent disambiguation
- POLICY_REVIEW_RENEWAL intent routing (currently falls through to generic)
- Participant event handlers (disconnection, track changes)

---

## Reference

- **Task backlog:** `TODO.md` (authoritative source for planned work)
- **Staff directory ops:** `docs/OPERATIONS.md`
- **Latency tuning:** `docs/LATENCY_TUNING.md`
- **Architecture details:** `docs/ARCHITECTURE.md`
- **LiveKit conventions:** `AGENTS.md`
