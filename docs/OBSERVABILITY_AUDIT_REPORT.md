# Observability, Logging & Monitoring Audit Report

**Project:** Harry Levine Insurance Voice Agent
**Date:** 2026-01-15
**Auditor:** Claude Opus 4.5

---

## Executive Summary

This audit evaluates the observability practices in the Harry Levine Insurance voice receptionist agent. The codebase demonstrates **basic logging practices** but has **significant gaps** in metrics collection, distributed tracing, alerting, and failed call tracking. The project does not leverage LiveKit's built-in observability features that are readily available.

**Overall Maturity Level:** 2/5 (Basic)

### Key Findings Summary

| Area | Current State | Gap Severity |
|------|---------------|--------------|
| Logging | Basic implementation | Medium |
| Metrics | Not implemented | High |
| Tracing | Not implemented | High |
| Alerting | Not implemented | High |
| Failed Call Tracking | Minimal | High |
| Debug/Replay Capability | Not implemented | Medium |

---

## 1. Logging

### Current Implementation

**Logger Setup:**
- Uses Python's standard `logging` module
- Single logger named "agent" across all modules: `logger = logging.getLogger("agent")`
- No structured logging configuration
- No log formatting customization

**Files using logging:**
- `src/main.py` - Session lifecycle events
- `src/agents/assistant.py` - All routing and transfer operations
- `src/agents/claims.py` - Claims lookup and transfers
- `src/agents/mortgagee.py` - Certificate/mortgagee handling
- `src/agents/after_hours.py` - After-hours voicemail flow
- `src/base_agent.py` - Base transfer/fallback operations

**Log Levels in Use:**
```python
logger.info()      # Primary - used for all normal operations
logger.warning()   # Used for missing agents, routing failures
logger.exception() # Used only in main.py for session initialization failure
logger.debug()     # Not used anywhere in production code
```

**Context Inclusion:**
- Room name added via `ctx.log_context_fields` in main.py:
  ```python
  ctx.log_context_fields = {"room": ctx.room.name}
  ```
- PII masking utilities exist (`mask_phone`, `mask_name`) and are used consistently
- CallerInfo userdata logged in many places (may include PII despite masking)

### Strengths

1. **Consistent logger naming**: All modules use `logging.getLogger("agent")`
2. **PII awareness**: `mask_phone()` and `mask_name()` utilities are used throughout
3. **Mock transfer logging**: Transfer attempts logged with `[MOCK TRANSFER]` prefix
4. **Shutdown callback**: Session end reason is logged:
   ```python
   async def on_shutdown(reason: str) -> None:
       logger.info(f"Session ended: {reason}")
   ctx.add_shutdown_callback(on_shutdown)
   ```

### Gaps vs Best Practices

1. **No structured logging (JSON format)**: Logs are plain text strings, making parsing difficult
2. **Missing correlation IDs**: No session_id, call_id, or trace_id in log entries
3. **Inconsistent log levels**: `debug` level not used; everything important is `info`
4. **No log level configuration**: Hardcoded; no runtime adjustment capability
5. **No request/response logging**: LLM prompts and responses not logged
6. **Missing key timestamps**: No duration logging for operations
7. **No log sampling**: All operations logged equally (will scale poorly)

### Recommendations

**P1 - High Priority:**
```python
# 1. Add structured logging
import json
import logging

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "session_id": getattr(record, "session_id", None),
            "room": getattr(record, "room", None),
            "intent": getattr(record, "intent", None),
        }
        return json.dumps(log_data)

# 2. Add session context adapter
class SessionLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        kwargs.setdefault("extra", {}).update(self.extra)
        return msg, kwargs

# In main.py:
session_logger = SessionLoggerAdapter(logger, {
    "session_id": ctx.room.name,
    "room": ctx.room.name,
})
```

**P2 - Medium Priority:**
- Configure log levels via environment variable
- Add request/response logging for LLM calls (with truncation)
- Add duration logging for transfer operations

---

## 2. Metrics

### Current Implementation

**Status:** NOT IMPLEMENTED

The codebase has no custom metrics collection. The only reference to metrics is in documentation files:
- `docs/REVIEW_AUDIT_REPORT.md` contains a P3 recommendation for metrics
- `uv.lock` shows OpenTelemetry dependencies exist (from `livekit-agents` transitive deps)

### Strengths

None - metrics are not implemented.

### Gaps vs Best Practices

1. **No call success/failure rate tracking**: Cannot measure call completion
2. **No intent distribution metrics**: Cannot analyze caller needs
3. **No transfer success rate**: Cannot measure routing effectiveness
4. **No latency tracking**: Cannot identify slow operations
5. **No usage/cost tracking**: Cannot monitor LLM/TTS/STT costs
6. **No LiveKit metrics integration**: Not using `session.on("metrics_collected")`

### Recommendations

**P1 - High Priority - Implement metrics collection:**

```python
# In main.py - Add metrics collection
from livekit.agents import metrics, MetricsCollectedEvent

usage_collector = metrics.UsageCollector()

@session.on("metrics_collected")
def _on_metrics_collected(ev: MetricsCollectedEvent):
    metrics.log_metrics(ev.metrics)
    usage_collector.collect(ev.metrics)

async def log_usage():
    summary = usage_collector.get_summary()
    logger.info(f"Session usage: {summary}")

ctx.add_shutdown_callback(log_usage)
```

**P2 - Medium Priority - Add custom business metrics:**

```python
# Create metrics module: src/observability/metrics.py
from dataclasses import dataclass, field
from enum import Enum
import time

@dataclass
class CallMetrics:
    """Track metrics for a single call."""
    session_id: str
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None

    # Intent tracking
    detected_intent: str | None = None
    final_intent: str | None = None

    # Transfer tracking
    transfer_attempts: int = 0
    transfer_success: bool = False
    target_agent: str | None = None

    # Caller info collection
    collected_name: bool = False
    collected_phone: bool = False
    collected_insurance_type: bool = False

    # Error tracking
    errors: list[str] = field(default_factory=list)

    def finalize(self):
        self.end_time = time.time()
        return {
            "session_id": self.session_id,
            "duration_seconds": self.end_time - self.start_time,
            "intent": self.final_intent,
            "transfer_success": self.transfer_success,
            "info_collected": all([
                self.collected_name,
                self.collected_phone,
                self.collected_insurance_type
            ]),
            "error_count": len(self.errors),
        }
```

---

## 3. Tracing

### Current Implementation

**Status:** NOT IMPLEMENTED

The project does not use distributed tracing. LiveKit's built-in tracing and OpenTelemetry integration are not configured.

### Strengths

None - tracing is not implemented.

### Gaps vs Best Practices

1. **No span creation for operations**: Cannot trace call flow
2. **No OpenTelemetry integration**: Despite deps being available
3. **No correlation between logs**: Cannot follow a call through the system
4. **No trace export**: Cannot send traces to external systems
5. **LiveKit Cloud insights not enabled**: Not using built-in observability

### Recommendations

**P1 - High Priority - Enable LiveKit Cloud insights:**

In LiveKit Cloud dashboard:
1. Go to project settings -> Data and privacy
2. Enable "Agent observability"

This automatically provides:
- Session traces with pipeline spans
- Token counts and latencies
- Audio recordings
- Turn-by-turn transcripts

**P2 - Medium Priority - Add OpenTelemetry for custom tracing:**

```python
# In main.py - Add OpenTelemetry setup
from livekit.agents.telemetry import set_tracer_provider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

def setup_tracing():
    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter())
    )
    set_tracer_provider(tracer_provider)

# Call in prewarm:
def prewarm(proc: JobProcess) -> None:
    setup_tracing()
    # ... existing code
```

---

## 4. Alerting

### Current Implementation

**Status:** NOT IMPLEMENTED

No alerting mechanism exists. Errors are logged but no notifications are sent.

### Strengths

None - alerting is not implemented.

### Gaps vs Best Practices

1. **No error alerting**: Session failures not reported
2. **No threshold-based alerts**: Cannot detect degradation
3. **No integration with alerting services**: Datadog, PagerDuty, etc.
4. **No anomaly detection**: Cannot detect unusual patterns

### Recommendations

**P1 - High Priority - Configure log forwarding with alerting:**

```bash
# Forward logs to Datadog (has built-in alerting)
lk agent update-secrets --secrets "DATADOG_TOKEN=your-token"

# Or forward to Sentry (automatic error tracking)
lk agent update-secrets --secrets "SENTRY_DSN=your-dsn"
```

**P2 - Medium Priority - Add critical error detection:**

```python
# In main.py - Add error tracking
CRITICAL_ERRORS = []

async def on_session_error(error: Exception) -> None:
    CRITICAL_ERRORS.append({
        "timestamp": time.time(),
        "error": str(error),
        "traceback": traceback.format_exc(),
    })
    # Log for alerting systems to pick up
    logger.error(f"CRITICAL: Session error - {error}", extra={
        "alert_level": "critical",
        "requires_attention": True,
    })
```

---

## 5. Failed/Abandoned Call Tracking

### Current Implementation

**Minimal tracking exists:**

- Session end logged via shutdown callback:
  ```python
  async def on_shutdown(reason: str) -> None:
      logger.info(f"Session ended: {reason}")
  ctx.add_shutdown_callback(on_shutdown)
  ```

- Exception handling in session start:
  ```python
  except Exception as e:
      logger.exception(f"Session initialization failed: {e}")
      raise
  ```

**What is NOT tracked:**
- Caller hangup during conversation
- Transfer failures
- Long hold times leading to abandonment
- Incomplete information collection
- Agent unavailability situations

### Strengths

1. Shutdown reason captured
2. Session initialization failures logged with stack trace

### Gaps vs Best Practices

1. **No call outcome classification**: success/failure/abandoned/transferred
2. **No abandonment point tracking**: When did caller leave?
3. **No incomplete call tracking**: What info was missing?
4. **No retry tracking**: Did caller call back?
5. **No SLA monitoring**: Were targets met?

### Recommendations

**P1 - High Priority - Track call outcomes:**

```python
# Create call outcome tracking
from enum import Enum

class CallOutcome(str, Enum):
    COMPLETED_TRANSFER = "completed_transfer"
    COMPLETED_NO_TRANSFER = "completed_no_transfer"  # e.g., hours/location query
    ABANDONED_GREETING = "abandoned_greeting"
    ABANDONED_INFO_COLLECTION = "abandoned_info_collection"
    ABANDONED_HOLD = "abandoned_hold"
    ERROR = "error"
    UNKNOWN = "unknown"

# In shutdown callback:
async def on_shutdown(reason: str) -> None:
    outcome = determine_call_outcome(caller_info, reason)
    logger.info(f"Session ended", extra={
        "outcome": outcome.value,
        "reason": reason,
        "intent": caller_info.call_intent.value if caller_info.call_intent else None,
        "info_collected": {
            "name": caller_info.name is not None,
            "phone": caller_info.phone_number is not None,
            "insurance_type": caller_info.insurance_type is not None,
        },
    })
```

**P2 - Medium Priority - Use LiveKit session reports:**

```python
from livekit.agents import JobContext

async def on_session_end(ctx: JobContext) -> None:
    report = ctx.make_session_report()
    report_dict = report.to_dict()

    # Log structured report
    logger.info("Session report", extra={
        "session_report": report_dict,
    })

    # Save to storage for analysis
    # ... upload to S3/GCS or send to analytics system

@server.rtc_session(on_session_end=on_session_end)
async def my_agent(ctx: JobContext) -> None:
    # ... existing code
```

---

## 6. Debug/Replay Capability

### Current Implementation

**Status:** NOT IMPLEMENTED

No mechanism exists to replay or debug calls after they occur.

### Strengths

None - replay capability is not implemented.

### Gaps vs Best Practices

1. **No audio recording**: Cannot listen to calls after the fact
2. **No transcript storage**: Conversation history not persisted
3. **No state snapshots**: Cannot reconstruct call flow
4. **No timeline view**: Cannot see event sequence
5. **LiveKit Cloud recordings not enabled**: Built-in feature unused

### Recommendations

**P1 - High Priority - Enable LiveKit Cloud recordings:**

Ensure agent observability is enabled in LiveKit Cloud settings. This provides:
- Audio recordings (both agent and user)
- Turn-by-turn transcripts
- Trace timeline with events
- 30-day retention

**P2 - Medium Priority - Add local transcript storage:**

```python
from datetime import datetime
import json

async def write_transcript():
    current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"/tmp/transcript_{ctx.room.name}_{current_date}.json"

    transcript_data = {
        "session_id": ctx.room.name,
        "timestamp": current_date,
        "history": session.history.to_dict(),
        "caller_info": {
            "name": caller_info.name,
            "phone": mask_phone(caller_info.phone_number) if caller_info.phone_number else None,
            "intent": caller_info.call_intent.value if caller_info.call_intent else None,
            "insurance_type": caller_info.insurance_type.value if caller_info.insurance_type else None,
        },
    }

    with open(filename, 'w') as f:
        json.dump(transcript_data, f, indent=2)

ctx.add_shutdown_callback(write_transcript)
```

**P3 - Lower Priority - Add conversation event logging:**

```python
@session.on("conversation_item_added")
def _on_item_added(ev):
    logger.info("Conversation item added", extra={
        "item_type": ev.item.type,
        "role": ev.item.role,
        "content_preview": str(ev.item.content)[:100] if ev.item.content else None,
    })

@session.on("user_input_transcribed")
def _on_transcribed(ev):
    logger.info("User transcription", extra={
        "text": ev.text,
        "is_final": ev.is_final,
    })
```

---

## Summary of Recommendations

### Priority 1 (Implement Immediately)

| Item | Effort | Impact |
|------|--------|--------|
| Enable LiveKit Cloud Agent Observability | Low | High |
| Add metrics collection via `session.on("metrics_collected")` | Low | High |
| Configure log forwarding (Datadog/Sentry) | Low | High |
| Track call outcomes in shutdown callback | Medium | High |

### Priority 2 (Implement Soon)

| Item | Effort | Impact |
|------|--------|--------|
| Add structured JSON logging | Medium | Medium |
| Add OpenTelemetry custom tracing | Medium | Medium |
| Implement session report capture | Low | Medium |
| Add custom business metrics | Medium | Medium |

### Priority 3 (Future Enhancement)

| Item | Effort | Impact |
|------|--------|--------|
| Add conversation event logging | Low | Low |
| Implement audio recording to S3 | Medium | Medium |
| Add anomaly detection | High | Medium |
| Create observability dashboard | High | Medium |

---

## Code Changes Required

### Minimal Implementation (P1 items)

The following code changes implement all P1 recommendations:

```python
# Add to main.py

from livekit.agents import metrics, MetricsCollectedEvent
import json
from datetime import datetime
from enum import Enum

# 1. Call outcome classification
class CallOutcome(str, Enum):
    COMPLETED_TRANSFER = "completed_transfer"
    COMPLETED_NO_TRANSFER = "completed_no_transfer"
    ABANDONED = "abandoned"
    ERROR = "error"
    UNKNOWN = "unknown"

# 2. Usage collector (module level)
usage_collector = None  # Initialized per session

# 3. In my_agent function, after session creation:
async def my_agent(ctx: JobContext) -> None:
    # ... existing setup ...

    # Initialize usage collector for this session
    global usage_collector
    usage_collector = metrics.UsageCollector()

    # Subscribe to metrics events
    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    # Enhanced shutdown callback with outcome tracking
    async def on_shutdown_with_metrics(reason: str) -> None:
        # Determine call outcome
        if "error" in reason.lower() or "exception" in reason.lower():
            outcome = CallOutcome.ERROR
        elif caller_info.assigned_agent:
            outcome = CallOutcome.COMPLETED_TRANSFER
        elif caller_info.call_intent:
            outcome = CallOutcome.COMPLETED_NO_TRANSFER
        else:
            outcome = CallOutcome.ABANDONED

        # Get usage summary
        usage_summary = usage_collector.get_summary() if usage_collector else {}

        # Log structured session end
        logger.info(json.dumps({
            "event": "session_end",
            "session_id": ctx.room.name,
            "timestamp": datetime.now().isoformat(),
            "outcome": outcome.value,
            "reason": reason,
            "intent": caller_info.call_intent.value if caller_info.call_intent else None,
            "insurance_type": caller_info.insurance_type.value if caller_info.insurance_type else None,
            "assigned_agent": caller_info.assigned_agent,
            "info_collected": {
                "name": caller_info.name is not None,
                "phone": caller_info.phone_number is not None,
                "insurance_type": caller_info.insurance_type is not None,
            },
            "usage": usage_summary,
        }))

    ctx.add_shutdown_callback(on_shutdown_with_metrics)

    # ... rest of existing code ...
```

### Log Forwarding Setup (CLI commands)

```bash
# Option 1: Datadog (recommended for full observability)
lk agent update-secrets --secrets "DATADOG_TOKEN=your-datadog-client-token"

# Option 2: Sentry (recommended for error tracking)
lk agent update-secrets --secrets "SENTRY_DSN=https://your-sentry-dsn"

# Option 3: CloudWatch (if using AWS)
lk agent update-secrets \
  --secrets "AWS_ACCESS_KEY_ID=your-key" \
  --secrets "AWS_SECRET_ACCESS_KEY=your-secret"
```

### LiveKit Cloud Setup (Dashboard)

1. Navigate to: https://cloud.livekit.io/projects/p_/settings/project
2. Find "Data and privacy" section
3. Enable "Agent observability"
4. Verify agent SDK version >= 1.3.0 (current: ~1.3)

---

## Conclusion

The Harry Levine Insurance voice agent has a functional but minimal observability implementation. The most impactful improvement would be enabling LiveKit Cloud's built-in agent observability features, which require almost no code changes and provide comprehensive session insights.

**Recommended Implementation Path:**

1. Enable LiveKit Cloud observability (5 minutes)
2. Add metrics collection hook (30 minutes)
3. Configure log forwarding to Datadog/Sentry (15 minutes)
4. Enhance shutdown callback for outcome tracking (1 hour)

**Total estimated effort for P1 items: ~2 hours**

---

## Appendix: Current Log Statements Inventory

| File | Log Level | Message Pattern | Context |
|------|-----------|-----------------|---------|
| `main.py:210` | info | "Session ended: {reason}" | Shutdown |
| `main.py:217` | exception | "Session initialization failed" | Error |
| `assistant.py:239` | info | "Recorded caller info" | Contact |
| `assistant.py:261` | info | "Business insurance inquiry recorded" | Routing |
| `assistant.py:293` | warning | "Spelled name mismatch" | STT error |
| `assistant.py:336` | info | "Detected claims request" | Intent |
| `assistant.py:367` | info | "Detected certificate request" | Intent |
| `assistant.py:442` | info | "Bank caller detected" | Intent |
| `assistant.py:630` | info | "Restricted transfer requested" | Routing |
| `assistant.py:776` | info | "[MOCK TRANSFER]" | Transfer |
| `assistant.py:820` | warning | "Ring group not found" | Error |
| `assistant.py:885` | warning | "No insurance type set" | Routing |
| `assistant.py:983` | warning | "No agent found for cancellation" | Routing |
| `claims.py:134` | info | "Claims lookup - Found carrier" | Lookup |
| `claims.py:167` | info | "[MOCK TRANSFER] Transferring claims" | Transfer |
| `claims.py:214` | info | "Claims callback requested" | Callback |
| `after_hours.py:118` | info | "After-hours contact recorded" | Contact |
| `mortgagee.py:278` | info | "Mortgagee request - provided email" | Info |
| `base_agent.py:90` | info | "[MOCK TRANSFER] Initiating transfer" | Transfer |
| `base_agent.py:122` | info | "Agent unavailable, using fallback" | Fallback |
| `base_agent.py:160` | info | "Taking data sheet" | Fallback |
