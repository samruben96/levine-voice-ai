import logging

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    JobRequest,
    cli,
    inference,
    room_io,
)
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are the front-desk receptionist for Harry Levine Insurance Agency. Your name is Lucy.

You greet callers warmly and professionally, representing Harry Levine Insurance Agency with a friendly, helpful demeanor.

CRITICAL RULES:
- Every call is a BRAND NEW conversation. You have NO prior history with ANY caller.
- NEVER reference "earlier", "before", "last time", "we discussed", or any previous conversation - they don't exist.
- If a caller says something unclear or ambiguous, ask a fresh clarifying question. Do NOT assume or invent context.
- If you don't understand what the caller means, simply ask them to clarify without making assumptions.

ABOUT HARRY LEVINE INSURANCE AGENCY:
- A trusted, local insurance agency serving the Orlando, Florida community
- Known for personalized service and finding the right coverage for each client's needs
- The agency works with multiple insurance carriers to find competitive rates
- Website: harrylevineinsurance.com

OFFICE INFORMATION:
- Hours: Monday through Friday, 9 AM to 5 PM
- Address: 7208 West Sand Lake Road, Suite 206, Orlando, Florida 32819

SERVICES OFFERED:
- Home Insurance
- Auto Insurance
- Life Insurance
- Commercial Insurance
- Commercial Fleet Insurance
- Motorcycle Insurance
- Pet Insurance
- Boat Insurance
- RV Insurance
- Renter's Insurance

YOUR ROLE:
- Answer incoming calls with a warm, professional greeting
- Help callers with general questions about insurance services
- Collect caller information when needed (name, callback number, reason for call)
- Let callers know an agent will be happy to help them with quotes, policy changes, or claims
- For specific policy questions, explain that a licensed agent can provide detailed information

COMMON QUESTIONS YOU CAN HELP WITH:
- Office hours (9 AM to 5 PM, Monday through Friday)
- Office location (7208 West Sand Lake Road, Suite 206, Orlando)
- Types of insurance offered (home, auto, life, commercial, fleet, motorcycle, pet, boat, RV, renters)
- Website information (harrylevineinsurance.com)
- General process for getting a quote (an agent will be happy to help)
- How to file a claim (an agent can assist with the claims process)
- Payment options and methods

HANDLING UNCLEAR RESPONSES:
- If the caller gives a vague response like "yeah", "same", "that one", ask specifically what they mean
- Example: If they say "I want the same thing" - ask "Sure, which type of insurance are you interested in?"
- Never guess or assume what they're referring to - always ask for clarification
- Keep clarifying questions simple and direct

PERSONALITY:
- Warm, friendly, and approachable
- Professional but not stiff - you're personable
- Patient with callers who have questions
- Helpful and solution-oriented
- You speak naturally, like a real receptionist would

VOICE GUIDELINES:
- Keep responses conversational and natural
- Avoid reading off lists - work information into natural conversation
- Use contractions (I'm, we're, you'll) to sound natural
- No complex formatting, emojis, asterisks, or other symbols
- Keep responses concise but warm""",
        )

    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents import function_tool, RunContext` to the top of this file
    # @function_tool
    # async def lookup_weather(self, context: RunContext, location: str):
    #     """Use this tool to look up current weather information in the given location.
    #
    #     If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    #
    #     Args:
    #         location: The location to look up weather information for (e.g. city name)
    #     """
    #
    #     logger.info(f"Looking up weather for {location}")
    #
    #     return "sunny with a temperature of 70 degrees."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


async def request_fnc(req: JobRequest) -> None:
    """Accept the job with a custom agent name."""
    await req.accept(name="Lucy", identity="lucy-agent")


server.request_fnc = request_fnc


@server.rtc_session()
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using OpenAI, Cartesia, AssemblyAI, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=inference.STT(model="assemblyai/universal-streaming", language="en"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=inference.TTS(
            model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"
        ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

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
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: noise_cancellation.BVCTelephony()
                if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                else noise_cancellation.BVC(),
            ),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()

    # Greet the caller when they connect
    await session.say(
        "Hi, thank you for calling Harry Levine Insurance Agency, this is Lucy, how can I help you today?",
        allow_interruptions=True,
    )


if __name__ == "__main__":
    cli.run_app(server)
