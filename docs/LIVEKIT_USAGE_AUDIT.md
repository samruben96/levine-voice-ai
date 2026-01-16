# LiveKit Agents Best Practices Audit Report

**Project**: Harry Levine Insurance Voice Agent
**Audit Date**: 2026-01-15
**LiveKit Agents SDK Version**: Assumed 1.3.x (based on patterns used)
**Auditor**: Claude Opus 4.5

---

## Executive Summary

This audit evaluates the Harry Levine Insurance Voice Agent codebase against LiveKit Agents best practices. The codebase demonstrates **solid adherence** to core LiveKit patterns with room for improvement in several areas.

### Overall Score: **B+ (Good)**

| Category | Score | Status |
|----------|-------|--------|
| Connection Lifecycle | A | Excellent |
| VoicePipelineAgent Configuration | A | Excellent |
| Function Tools | A- | Good |
| Handoff Patterns | B+ | Good |
| Session State Management | A | Excellent |
| Resource Cleanup | B | Satisfactory |
| Error Handling | B- | Needs Improvement |
| Reconnection Handling | C | Missing |
| Timeout Configuration | C+ | Basic |

---

## 1. Connection Lifecycle

### What We Found

**File**: `src/main.py` (lines 106-218)

The session is started correctly using the modern pattern:

```python
@server.rtc_session(agent_name="Aizellee")
async def my_agent(ctx: JobContext) -> None:
    # ... session setup ...

    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(...)
    )

    await ctx.connect()
```

**Strengths**:
- Uses `@server.rtc_session()` decorator correctly
- Proper order: `session.start()` before `ctx.connect()`
- Passes `RoomOptions` with noise cancellation configuration
- Uses typed `AgentSession[CallerInfo]` for type-safe userdata access

**Issues**:
- None identified - lifecycle is implemented correctly

### Recommendation

**Status**: No changes required

---

## 2. VoicePipelineAgent Configuration

### What We Found

**File**: `src/main.py` (lines 129-169)

The AgentSession is configured with comprehensive options:

```python
session = AgentSession[CallerInfo](
    stt=inference.STT(
        model="assemblyai/universal-streaming",
        language="en",
        extra_kwargs={
            "end_of_turn_confidence_threshold": 0.5,
            "min_end_of_turn_silence_when_confident": 300,
        },
    ),
    llm=inference.LLM(model="openai/gpt-4.1-mini"),
    tts=inference.TTS(
        model="cartesia/sonic-3",
        voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        extra_kwargs={"speed": 0.85},
    ),
    turn_detection=MultilingualModel(),
    vad=ctx.proc.userdata["vad"],
    preemptive_generation=True,
    min_endpointing_delay=0.3,
    max_endpointing_delay=1.5,
    min_interruption_duration=0.3,
    userdata=caller_info,
)
```

**Strengths**:
- Uses LiveKit Inference shorthand for model configuration
- Turn detection properly configured with MultilingualModel
- VAD is prewarmed in `prewarm()` function (excellent for reducing cold start latency)
- Latency parameters tuned for responsiveness
- `preemptive_generation=True` for reduced response latency
- AssemblyAI endpointing configured via `extra_kwargs`

**Best Practice Alignment**:
- Per LiveKit docs: "VAD and turn detection are used to determine when the user is speaking and when the agent should respond" - properly implemented
- Per LiveKit docs: Preemptive generation "can reduce response latency but can incur extra compute costs if the user interrupts" - documented trade-off accepted

### Recommendation

**Status**: Excellent - no changes required

Consider documenting the latency tuning decisions in code comments or a separate document (partially done in `docs/LATENCY_TUNING.md`).

---

## 3. Room Options Configuration

### What We Found

**File**: `src/main.py` (lines 194-202)

```python
room_options=room_io.RoomOptions(
    audio_input=room_io.AudioInputOptions(
        noise_cancellation=lambda params: noise_cancellation.BVCTelephony()
        if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
        else noise_cancellation.BVC(),
    ),
),
```

**Strengths**:
- Uses dynamic noise cancellation based on participant type (SIP vs standard)
- BVCTelephony for SIP callers is a best practice for telephony apps

**Missing Options**:
- `close_on_disconnect` not explicitly set (uses default `True` which is correct)
- `delete_room_on_close` not set (default `False` is appropriate)
- `participant_kinds` not explicitly set (defaults include SIP and STANDARD)

### Recommendation

**Status**: Good - consider making settings explicit for clarity

```python
room_options=room_io.RoomOptions(
    audio_input=room_io.AudioInputOptions(
        noise_cancellation=lambda params: noise_cancellation.BVCTelephony()
        if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
        else noise_cancellation.BVC(),
    ),
    close_on_disconnect=True,  # Explicit: close session when participant leaves
    # participant_kinds=[rtc.ParticipantKind.PARTICIPANT_KIND_SIP,
    #                    rtc.ParticipantKind.PARTICIPANT_KIND_STANDARD],
),
```

---

## 4. Shutdown Callbacks and Resource Cleanup

### What We Found

**File**: `src/main.py` (lines 207-212)

```python
async def on_shutdown(reason: str) -> None:
    logger.info(f"Session ended: {reason}")

ctx.add_shutdown_callback(on_shutdown)
```

**Strengths**:
- Shutdown callback is registered
- Callback is properly async (returns coroutine)
- Basic logging on shutdown

**Issues**:
- Shutdown callback only logs - no actual cleanup is performed
- No cleanup for potential resources (database connections, external API clients, etc.)
- Callback registered AFTER `ctx.connect()` - should be registered before for safety

### Recommendation

**Priority**: Medium

Move shutdown callback registration before `ctx.connect()` and add substantive cleanup:

```python
# Register shutdown callback BEFORE connect for safety
async def on_shutdown(reason: str) -> None:
    logger.info(f"Session ended: {reason}")
    # Add any cleanup logic here
    # e.g., close database connections, flush logs, etc.

ctx.add_shutdown_callback(on_shutdown)

# Then connect
await ctx.connect()
```

Per LiveKit docs: "Shutdown hooks should complete within a short amount of time. By default, the framework waits 60 seconds before forcefully terminating the process."

---

## 5. Reconnection Handling

### What We Found

**Status**: NOT IMPLEMENTED

The codebase does not include explicit reconnection handling. There are no event listeners for:
- `Reconnecting` event
- `Reconnected` event
- `Disconnected` event

**Per LiveKit docs**: "When this happens, LiveKit attempts to resume the connection automatically. It reconnects to the signaling WebSocket and initiates an ICE restart for the WebRTC connection."

While LiveKit handles reconnection automatically at the transport layer, the agent code should:
1. Monitor connection state changes
2. Log reconnection events for observability
3. Potentially inform the user during extended reconnection attempts

### Recommendation

**Priority**: Medium

Add reconnection event handling in `my_agent()`:

```python
@ctx.room.on("reconnecting")
def on_reconnecting():
    logger.warning("Connection lost, attempting to reconnect...")

@ctx.room.on("reconnected")
def on_reconnected():
    logger.info("Successfully reconnected to room")

@ctx.room.on("disconnected")
def on_disconnected():
    logger.info("Disconnected from room")
```

---

## 6. Timeout Configuration

### What We Found

**Status**: PARTIALLY CONFIGURED

The codebase configures latency-related timeouts but lacks explicit timeout configuration for:
- API operation timeouts
- Tool execution timeouts
- Maximum session duration
- User away timeout

**Configured**:
- `min_endpointing_delay=0.3`
- `max_endpointing_delay=1.5`
- `min_interruption_duration=0.3`
- VAD `min_silence_duration=0.3`

**Not Configured**:
- `user_away_timeout` (defaults to 15.0 seconds)
- Tool call timeouts
- Maximum conversation duration limits

### Recommendation

**Priority**: Low

Consider explicitly configuring session timeouts:

```python
session = AgentSession[CallerInfo](
    # ... existing config ...
    user_away_timeout=30.0,  # Increase for telephony (people may step away)
)
```

---

## 7. Function Tools and Return Values

### What We Found

**Files**: `src/agents/assistant.py`, `src/agents/claims.py`, `src/agents/after_hours.py`, `src/agents/mortgagee.py`

#### Correct Patterns

**Handoff with tuple return** (correct):
```python
@function_tool
async def route_call_claims(
    self,
    context: RunContext[CallerInfo],
) -> tuple[Agent, str]:
    # ...
    return (ClaimsAgent(), "")
```

**Silent completion with None return** (correct):
```python
@function_tool
async def handle_bank_caller(
    self,
    context: RunContext[CallerInfo],
) -> None:
    # Speak directly, then return None for silent completion
    await context.session.say(bank_response, allow_interruptions=False)
    # Return None implicitly
```

**String return for LLM processing** (correct):
```python
@function_tool
async def record_caller_contact_info(...) -> str:
    return f"Got it, I have {full_name} at {phone_number}."
```

#### Issues Found

1. **Inconsistent return type annotations**:
   - `transfer_cancellation` returns `str | None` - could return validation error string OR None on success
   - `_initiate_transfer` returns `None` but signature says nothing

2. **Missing await on generate_reply**:
   - In `complete_specific_agent_transfer`, line 734 calls `context.session.say()` without storing the handle

3. **Handoff empty transition message**:
   - Multiple handoffs return `("", )` as the second element - this is intentional to avoid duplicate greetings but should be documented

### Recommendation

**Priority**: Medium

Per LiveKit docs: "Return None or nothing at all to complete the tool silently without requiring a reply from the LLM."

The pattern used is correct. Consider adding docstring clarification:

```python
@function_tool
async def route_call_claims(
    self,
    context: RunContext[CallerInfo],
) -> tuple[Agent, str]:
    """Route the call for claims.

    Returns:
        tuple[Agent, str]: (ClaimsAgent instance, empty transition message).
        Empty message prevents duplicate greetings since ClaimsAgent has on_enter.
    """
```

---

## 8. Handoff Patterns

### What We Found

**Files**: `src/agents/assistant.py` (handoff sources), `src/agents/claims.py`, `src/agents/after_hours.py`, `src/agents/mortgagee.py` (handoff targets)

#### Correct Patterns

**Tool-based handoff** (correct per LiveKit docs):
```python
@function_tool
async def route_call_claims(self, context: RunContext[CallerInfo]) -> tuple[Agent, str]:
    return (ClaimsAgent(), "")
```

**on_enter for greeting** (correct per LiveKit docs):
```python
class ClaimsAgent(Agent):
    async def on_enter(self) -> None:
        self.session.generate_reply(
            instructions="Call transfer_to_claims IMMEDIATELY..."
        )
```

**Context preservation NOT used** - each sub-agent starts with fresh context. This appears intentional for this use case since sub-agents have specialized instructions.

#### Issues Found

1. **Missing `await` on `generate_reply` in on_enter**:

   Per LiveKit docs example:
   ```python
   async def on_enter(self) -> None:
       await self.session.generate_reply(instructions="...")
   ```

   Current code (missing await):
   ```python
   async def on_enter(self) -> None:
       self.session.generate_reply(...)  # Missing await!
   ```

   This is present in ALL agent `on_enter` methods:
   - `src/agents/assistant.py` line 208
   - `src/agents/claims.py` lines 106, 110
   - `src/agents/after_hours.py` line 88
   - `src/agents/mortgagee.py` lines 102, 107, 112

2. **Context not passed to sub-agents**:

   Sub-agents are created without `chat_ctx`:
   ```python
   return (ClaimsAgent(), "")
   ```

   Per LiveKit docs best practice: "To include the prior conversation, set the chat_ctx parameter in the Agent constructor."

   However, for this use case (specialized sub-agents with distinct instructions), fresh context may be intentional.

### Recommendation

**Priority**: HIGH for missing await issue

Fix missing `await` in all `on_enter` methods:

```python
# BEFORE (incorrect)
async def on_enter(self) -> None:
    self.session.generate_reply(instructions="...")

# AFTER (correct)
async def on_enter(self) -> None:
    await self.session.generate_reply(instructions="...")
```

Note: The code may still work due to Python's async behavior, but awaiting ensures proper execution order and error handling.

---

## 9. Userdata Management

### What We Found

**Files**: `src/models.py`, `src/main.py`, all agent files

#### Excellent Implementation

The codebase demonstrates excellent userdata management:

1. **Typed dataclass** (`src/models.py`):
```python
@dataclass(slots=True)
class CallerInfo:
    name: str | None = None
    first_name: str | None = None
    # ... extensive fields with documentation
```

2. **Typed AgentSession** (`src/main.py`):
```python
session = AgentSession[CallerInfo](
    userdata=caller_info,
)
```

3. **Typed RunContext in tools**:
```python
@function_tool
async def record_caller_contact_info(
    self,
    context: RunContext[CallerInfo],  # Properly typed!
    first_name: str,
    ...
) -> str:
    context.userdata.first_name = first_name  # Type-safe access
```

4. **Slots for memory efficiency**:
```python
@dataclass(slots=True)  # Excellent for performance
class CallerInfo:
```

### Recommendation

**Status**: Excellent - this is exemplary implementation

---

## 10. Error Handling

### What We Found

**File**: `src/main.py` (lines 190-218)

```python
try:
    await session.start(...)
    await ctx.connect()
    # ... setup ...
except Exception as e:
    logger.exception(f"Session initialization failed: {e}")
    raise
```

**Issues**:
- Broad `Exception` catch - could be more specific
- Re-raises after logging but doesn't differentiate recoverable vs fatal errors
- No error handling in individual tool functions

**In tool functions** (various files):
- No `ToolError` usage for communicating errors back to LLM
- Validation errors return strings which is correct, but could be more explicit

### Recommendation

**Priority**: Medium

Consider using `ToolError` for explicit error communication:

```python
from livekit.agents import ToolError

@function_tool
async def transfer_cancellation(self, context: RunContext[CallerInfo]) -> str | None:
    validation_error = self._validate_transfer_requirements(context)
    if validation_error:
        # Current: returns string (acceptable)
        return validation_error
        # Alternative: raise ToolError for explicit LLM error handling
        # raise ToolError(validation_error)
```

Per LiveKit docs: "Raise the ToolError exception to return an error to the LLM in place of a response."

---

## 11. Prewarm Function

### What We Found

**File**: `src/main.py` (lines 63-91)

```python
def prewarm(proc: JobProcess) -> None:
    validate_environment()
    proc.userdata["vad"] = silero.VAD.load(
        min_silence_duration=0.3,
        min_speech_duration=0.05,
        activation_threshold=0.5,
    )

server.setup_fnc = prewarm
```

**Strengths**:
- VAD model preloaded during worker startup
- Environment validation before first call
- `num_idle_processes=2` keeps warm workers ready

**Best Practice Alignment**:
Per LiveKit docs: "Prewarm function: Load the VAD model during worker startup to avoid cold start latency on the first call."

### Recommendation

**Status**: Excellent - properly implemented

---

## 12. Session Speech Methods

### What We Found

**Usage of `session.say()` and `session.generate_reply()`**:

1. **session.say() with allow_interruptions=False** (correct for announcements):
```python
await context.session.say(transfer_message, allow_interruptions=False)
```

2. **session.generate_reply() in on_enter** (correct for greetings):
```python
self.session.generate_reply(
    instructions="Deliver the GREETING as specified..."
)
```

Per LiveKit docs:
- `say()`: "To have the agent speak a predefined message"
- `generate_reply()`: "To make conversations more dynamic, use session.generate_reply() to prompt the LLM to generate a response"

The codebase correctly uses `say()` for scripted messages (transfers, bank caller responses) and `generate_reply()` for dynamic responses.

### Recommendation

**Status**: Good implementation

---

## Summary of Findings

### Critical Issues (Fix Immediately)

1. **Missing `await` on `generate_reply()` in all `on_enter()` methods**
   - Files: assistant.py, claims.py, after_hours.py, mortgagee.py
   - Risk: Potential race conditions, unhandled errors

### High Priority Issues

2. **No reconnection event handling**
   - Missing observability for connection drops
   - Users won't be informed during reconnection attempts

### Medium Priority Issues

3. **Shutdown callback registered after connect**
   - Should be registered before for reliability

4. **Broad exception handling**
   - Consider more specific error types

5. **Tool return type documentation**
   - Add docstrings explaining handoff patterns

### Low Priority / Suggestions

6. **Make RoomOptions explicit**
   - Document default behaviors explicitly in code

7. **Add user_away_timeout configuration**
   - Consider telephony use case (users may step away)

8. **Consider ToolError for validation failures**
   - More explicit error handling for LLM

---

## Appendix: Best Practice Checklist

| Practice | Status | Notes |
|----------|--------|-------|
| Use `@server.rtc_session()` decorator | PASS | Correctly implemented |
| Prewarm VAD model | PASS | Properly configured |
| Use typed AgentSession | PASS | `AgentSession[CallerInfo]` |
| Configure RoomOptions | PASS | Noise cancellation configured |
| Register shutdown callbacks | PARTIAL | Registered but after connect |
| Handle reconnection events | FAIL | Not implemented |
| Use typed RunContext in tools | PASS | All tools properly typed |
| Return None for silent completion | PASS | Correctly implemented |
| Use tuple for handoffs | PASS | Correct pattern |
| Await generate_reply in on_enter | FAIL | Missing in all agents |
| Use session.say() for scripted speech | PASS | Correctly used |
| Configure latency parameters | PASS | Well-tuned values |
| Use userdata dataclass | PASS | Excellent implementation |

---

## References

- [LiveKit Agents Documentation](https://docs.livekit.io/agents/)
- [Agent Session](https://docs.livekit.io/agents/logic/sessions/)
- [Tool Definition and Use](https://docs.livekit.io/agents/logic/tools/)
- [Agents and Handoffs](https://docs.livekit.io/agents/logic/agents-handoffs/)
- [Job Lifecycle](https://docs.livekit.io/agents/server/job/)
- [Workflows](https://docs.livekit.io/agents/logic/workflows/)
