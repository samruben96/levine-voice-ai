"""Server setup and entry point for the Harry Levine Insurance Voice Agent.

This module contains the LiveKit Agents server configuration, including:
- Server initialization
- Prewarm function for loading models
- Request handler for accepting jobs
- Main agent entry point (my_agent)

Usage
-----
Development mode (auto-reload)::

    uv run python src/main.py dev

Production mode::

    uv run python src/main.py start

Interactive testing::

    uv run python src/main.py console

Download required models::

    uv run python src/main.py download-files
"""

import logging

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    JobRequest,
    MetricsCollectedEvent,
    cli,
    inference,
    metrics,
    room_io,
)
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from agents.assistant import Assistant
from models import CallerInfo
from utils import validate_environment

logger = logging.getLogger("agent")

load_dotenv(".env.local")


# =============================================================================
# SERVER SETUP
# =============================================================================

# num_idle_processes=2 keeps warm worker processes ready to handle calls immediately
# This prevents cold start latency on the first call of the day
server = AgentServer(num_idle_processes=2)


def prewarm(proc: JobProcess) -> None:
    """Prewarm the agent process by loading required models.

    This function is called when the agent process starts. It:
    - Validates environment variables
    - Loads the VAD model with optimized latency parameters

    Note: MultilingualModel (turn detector) cannot be prewarmed as it requires
    a job context. On LiveKit Cloud it uses remote inference anyway, so the
    latency impact is minimal.

    Args:
        proc: The job process to initialize.
    """
    # Validate environment variables before starting
    validate_environment()

    # Load VAD model with optimized latency parameters
    # - min_silence_duration: Reduced from 0.55s default for faster turn detection
    # - min_speech_duration: Keep default - minimum speech to start chunk
    # - activation_threshold: Keep default - speech detection sensitivity
    proc.userdata["vad"] = silero.VAD.load(
        min_silence_duration=0.3,
        min_speech_duration=0.05,
        activation_threshold=0.5,
    )


server.setup_fnc = prewarm


async def request_fnc(req: JobRequest) -> None:
    """Accept the job with a custom agent name.

    Args:
        req: The job request to accept.
    """
    await req.accept(name="Aizellee", identity="aizellee-agent")


server.request_fnc = request_fnc


@server.rtc_session(agent_name="Aizellee")
async def my_agent(ctx: JobContext) -> None:
    """Main agent entry point for handling voice sessions.

    This function is called when a new voice session starts. It:
    - Sets up logging context
    - Initializes the voice AI pipeline
    - Starts the session with the Assistant agent
    - Connects to the LiveKit room

    Args:
        ctx: The job context containing room and session information.
    """
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Initialize caller info to track collected data
    caller_info = CallerInfo()

    # Register shutdown callback for graceful session termination BEFORE connecting
    # Note: callback must be async (returns coroutine, not None)
    async def on_shutdown(reason: str) -> None:
        logger.info(f"Session ended: {reason}")

    ctx.add_shutdown_callback(on_shutdown)

    # Set up a voice AI pipeline using OpenAI, Cartesia, AssemblyAI, and the LiveKit turn detector
    session = AgentSession[CallerInfo](
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        # extra_kwargs optimize AssemblyAI endpointing for faster turn detection
        stt=inference.STT(
            model="assemblyai/universal-streaming",
            language="en",
            extra_kwargs={
                "end_of_turn_confidence_threshold": 0.5,
                "min_end_of_turn_silence_when_confident": 300,
                "max_turn_silence": 1000,  # Safety net for long pauses
            },
        ),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=inference.LLM(
            model="openai/gpt-4.1"
        ),  # Upgraded from gpt-4.1-mini for better instruction following
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        # Voice ID: Default Cartesia voice from LiveKit examples. Browse available voices at:
        # https://cartesia.ai/voices (requires free account) and copy the voice ID to customize.
        tts=inference.TTS(
            model="cartesia/sonic-3",
            voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
        # Latency optimization parameters for more responsive conversation
        # - min_endpointing_delay: Reduced from 0.5s default for faster turn completion
        # - max_endpointing_delay: Reduced from 3.0s default to avoid long pauses
        # - min_interruption_duration: Reduced from 0.5s for more responsive interruptions
        min_endpointing_delay=0.3,
        max_endpointing_delay=1.5,
        min_interruption_duration=0.3,
        # Store caller information for the session
        userdata=caller_info,
    )

    # Subscribe to metrics collection for observability
    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    try:
        await session.start(
            agent=Assistant(),
            room=ctx.room,
            room_options=room_io.RoomOptions(
                audio_input=room_io.AudioInputOptions(
                    noise_cancellation=lambda params: noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC(),
                ),
            ),
        )

        # Join the room and connect to the user
        await ctx.connect()

        # Set up reconnection event handlers for connection state monitoring
        @ctx.room.on("reconnecting")
        def on_reconnecting():
            logger.warning("Connection lost, attempting to reconnect...")

        @ctx.room.on("reconnected")
        def on_reconnected():
            logger.info("Successfully reconnected to room")

        @ctx.room.on("disconnected")
        def on_disconnected():
            logger.info("Disconnected from room")

        # Note: The initial greeting is handled by Assistant.on_enter() which calls
        # session.generate_reply() - this is the proper pattern for agent greetings.
    except Exception as e:
        logger.exception(f"Session initialization failed: {e}")
        raise


if __name__ == "__main__":
    cli.run_app(server)
