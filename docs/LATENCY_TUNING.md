# Latency Tuning Guide

This guide documents the latency optimization parameters used in the Harry Levine Insurance Voice Agent and provides guidance for further tuning.

## Table of Contents

- [Overview](#overview)
- [Current Configuration](#current-configuration)
- [Parameter Reference](#parameter-reference)
- [Common Pitfalls](#common-pitfalls)
- [Tuning Guidelines](#tuning-guidelines)
- [Troubleshooting](#troubleshooting)

---

## Overview

Voice AI agents are highly sensitive to latency. Excessive pauses between user speech and agent response create an unnatural conversation experience. The LiveKit Agents SDK provides multiple parameters to control turn detection, endpointing, and interruption handling.

This project optimizes three main components:

1. **Silero VAD** - Voice Activity Detection for speech boundary detection
2. **AssemblyAI STT** - Speech-to-text with end-of-turn detection
3. **AgentSession** - Overall conversation flow parameters

---

## Current Configuration

### Silero VAD (Voice Activity Detection)

Located in `src/agent.py` in the `prewarm()` function:

```python
proc.userdata["vad"] = silero.VAD.load(
    min_silence_duration=0.3,    # Reduced from 0.55s default
    min_speech_duration=0.05,    # Minimum speech to start a chunk
    activation_threshold=0.5,    # Speech detection sensitivity
)
```

### AssemblyAI STT (Speech-to-Text)

Located in `src/agent.py` in the `AgentSession` configuration:

```python
stt=inference.STT(
    model="assemblyai/universal-streaming",
    language="en",
    extra_kwargs={
        "end_of_turn_confidence_threshold": 0.5,
        "min_end_of_turn_silence_when_confident": 300,
    },
),
```

### AgentSession Parameters

Located in `src/agent.py` in the `AgentSession` configuration:

```python
session = AgentSession[CallerInfo](
    # ... STT, LLM, TTS config ...
    min_endpointing_delay=0.3,       # Reduced from 0.5s default
    max_endpointing_delay=1.5,       # Reduced from 3.0s default
    min_interruption_duration=0.3,   # Reduced from 0.5s default
)
```

---

## Parameter Reference

### Silero VAD Parameters

| Parameter | Default | Current | Description |
|-----------|---------|---------|-------------|
| `min_silence_duration` | 0.55s | 0.3s | Minimum silence duration to consider end of speech. Lower values detect turn completion faster but may clip speech. |
| `min_speech_duration` | 0.05s | 0.05s | Minimum speech duration to start a VAD chunk. Filters out very short sounds. |
| `activation_threshold` | 0.5 | 0.5 | Probability threshold for speech detection. Lower values are more sensitive, higher values filter more noise. |

### AssemblyAI STT Parameters (via extra_kwargs)

| Parameter | Default | Current | Description |
|-----------|---------|---------|-------------|
| `end_of_turn_confidence_threshold` | 0.8 | 0.5 | Confidence level required to end a turn. Lower values end turns faster. |
| `min_end_of_turn_silence_when_confident` | 500ms | 300ms | Minimum silence (in milliseconds) before ending turn when confidence threshold is met. |

### AgentSession Parameters

| Parameter | Default | Current | Description |
|-----------|---------|---------|-------------|
| `min_endpointing_delay` | 0.5s | 0.3s | Minimum time after VAD detects silence before the turn is considered complete. |
| `max_endpointing_delay` | 3.0s | 1.5s | Maximum time to wait for end-of-turn, even if VAD has not detected silence. Prevents infinite waiting. |
| `min_interruption_duration` | 0.5s | 0.3s | Minimum duration of user speech required to interrupt the agent. Lower values make interruptions more responsive. |

---

## Common Pitfalls

### Wrong Parameter Name for LiveKit Inference STT

When using `inference.STT()` from LiveKit Agents, you must use `extra_kwargs` for model-specific options:

```python
# WRONG - causes TypeError
stt=inference.STT(
    model="assemblyai/universal-streaming",
    model_options={  # This parameter does not exist
        "end_of_turn_confidence_threshold": 0.5,
    },
),
# Error: TypeError: STT.__init__() got an unexpected keyword argument 'model_options'

# CORRECT
stt=inference.STT(
    model="assemblyai/universal-streaming",
    extra_kwargs={  # Use extra_kwargs for model-specific options
        "end_of_turn_confidence_threshold": 0.5,
    },
),
```

### LiveKit Inference vs. Provider Plugins

Different interfaces use different parameter patterns:

| Interface | Parameter Style | Example |
|-----------|----------------|---------|
| **LiveKit Inference** (`inference.STT`) | `extra_kwargs` dict | `extra_kwargs={"end_of_turn_confidence_threshold": 0.5}` |
| **AssemblyAI Plugin** (`assemblyai.STT`) | Named parameters | `end_of_turn_confidence_threshold=0.5` |

Example using the AssemblyAI plugin directly (not LiveKit Inference):

```python
from livekit.plugins import assemblyai

# Plugin-specific class uses named parameters
stt=assemblyai.STT(
    end_of_turn_confidence_threshold=0.5,
    min_end_of_turn_silence_when_confident=300,
)
```

### Connection Options vs. Model Options

The `conn_options` parameter is for connection-level settings (timeouts, retries), not model behavior:

```python
# conn_options is for connection settings, NOT model behavior
stt=inference.STT(
    model="assemblyai/universal-streaming",
    conn_options={...},      # Connection settings (timeouts, etc.)
    extra_kwargs={...},      # Model-specific behavior options
),
```

---

## Tuning Guidelines

### Making Conversations Feel More Responsive

To reduce pauses and make the agent respond faster:

1. **Reduce VAD silence duration** (try 0.2-0.4s):
   ```python
   silero.VAD.load(min_silence_duration=0.25)
   ```

2. **Lower endpointing delays**:
   ```python
   min_endpointing_delay=0.2,
   max_endpointing_delay=1.0,
   ```

3. **Lower end-of-turn confidence** (try 0.4-0.6):
   ```python
   extra_kwargs={"end_of_turn_confidence_threshold": 0.4}
   ```

**Tradeoff**: Too aggressive settings may cause the agent to cut off users mid-sentence.

### Making Conversations Feel Less Rushed

If the agent is cutting off users or responding too quickly:

1. **Increase VAD silence duration** (try 0.4-0.6s):
   ```python
   silero.VAD.load(min_silence_duration=0.5)
   ```

2. **Raise endpointing delays**:
   ```python
   min_endpointing_delay=0.5,
   max_endpointing_delay=2.5,
   ```

3. **Raise end-of-turn confidence** (try 0.7-0.9):
   ```python
   extra_kwargs={"end_of_turn_confidence_threshold": 0.8}
   ```

**Tradeoff**: More conservative settings may feel sluggish to users.

### Handling Interruptions

To make interruptions more responsive (agent stops faster when user speaks):

```python
min_interruption_duration=0.2,  # Detect interruptions quickly
```

To reduce false interruptions from background noise:

```python
min_interruption_duration=0.5,  # Require more speech to interrupt
```

---

## Troubleshooting

### Agent Responds Before User Finishes Speaking

**Symptoms**: Agent cuts off users mid-sentence.

**Possible causes**:
- `min_silence_duration` too low
- `end_of_turn_confidence_threshold` too low
- `min_endpointing_delay` too low

**Fix**: Increase these values incrementally.

### Long Pauses Before Agent Responds

**Symptoms**: Unnatural delays after user stops speaking.

**Possible causes**:
- `min_silence_duration` too high
- `end_of_turn_confidence_threshold` too high
- `min_endpointing_delay` or `max_endpointing_delay` too high

**Fix**: Decrease these values incrementally.

### Agent Does Not Stop When User Interrupts

**Symptoms**: User speaks but agent continues talking.

**Possible causes**:
- `min_interruption_duration` too high
- VAD `activation_threshold` too high

**Fix**: Lower `min_interruption_duration` or `activation_threshold`.

### Agent Stops on Background Noise

**Symptoms**: Agent falsely detects speech from background sounds.

**Possible causes**:
- VAD `activation_threshold` too low
- `min_speech_duration` too low

**Fix**: Raise `activation_threshold` (try 0.6-0.7) or `min_speech_duration`.

### TypeError: STT.__init__() got an unexpected keyword argument

**Error**:
```
TypeError: STT.__init__() got an unexpected keyword argument 'model_options'. Did you mean 'conn_options'?
```

**Cause**: Using wrong parameter name for LiveKit Inference.

**Fix**: Use `extra_kwargs` instead of `model_options`:
```python
stt=inference.STT(
    model="assemblyai/universal-streaming",
    extra_kwargs={...},  # NOT model_options
),
```

---

## Testing Latency Changes

When tuning latency parameters:

1. **Test in console mode** first:
   ```bash
   uv run python src/agent.py console
   ```

2. **Test with realistic speech patterns**:
   - Normal conversational pace
   - Hesitant speech with "um" and pauses
   - Rapid speech
   - Interruptions mid-sentence

3. **Test with background noise** if applicable to your deployment environment

4. **Run the test suite** to ensure changes do not break existing behavior:
   ```bash
   uv run pytest tests/ -v
   ```

5. **Deploy to staging** before production if possible

---

## Voice Configuration

### Cartesia TTS Voice

The agent uses Cartesia Sonic-3 for text-to-speech with a specific voice ID configured in `src/agent.py`:

```python
tts=inference.TTS(
    model="cartesia/sonic-3",
    voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"  # Default LiveKit voice
)
```

**Voice ID:** `9626c31c-bec5-4cca-baa8-f8ba9e84c8bc`

This is the default Cartesia voice from the LiveKit examples. To customize the agent's voice:

1. Browse available voices at [Cartesia Voice Library](https://cartesia.ai/voices) (free account required)
2. Find a voice that matches your desired tone (professional, warm, authoritative, etc.)
3. Copy the voice ID from the voice details page
4. Update the `voice` parameter in the TTS configuration

**Considerations when selecting a voice:**
- **Professional tone**: For insurance receptionist, choose a clear, friendly voice
- **Speech rate**: Some voices speak faster than others; this affects conversation pacing
- **Accent**: Consider your target audience's familiarity with different accents

---

## References

- [LiveKit Agents Turn Detection](https://docs.livekit.io/agents/build/turns)
- [LiveKit Agents Audio Configuration](https://docs.livekit.io/agents/build/audio/)
- [LiveKit STT Models](https://docs.livekit.io/agents/models/stt/)
- [LiveKit TTS Models](https://docs.livekit.io/agents/models/tts/)
- [Cartesia Voice Library](https://cartesia.ai/voices)
- [AssemblyAI Streaming Documentation](https://www.assemblyai.com/docs/speech-to-text/streaming)
