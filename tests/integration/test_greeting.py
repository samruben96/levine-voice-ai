"""Integration tests for Assistant greeting behavior.

These tests verify the Assistant's greeting and basic interaction behavior
using real LLM inference.
"""

import sys

import pytest
from livekit.agents import AgentSession, inference

sys.path.insert(0, "src")
from agent import Assistant, CallerInfo

from .conftest import skip_function_events


def _llm():
    return inference.LLM(model="openai/gpt-4.1-mini")


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.smoke
async def test_receptionist_greeting() -> None:
    """Evaluation of Aizellee's greeting as Harry Levine Insurance receptionist."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Run an agent turn following the user's greeting (simulating an incoming call)
        result = await session.run(user_input="Hello")

        # Evaluate that Aizellee greets as an insurance agency receptionist
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Greets the caller in a warm, professional manner as a receptionist.

                The greeting should:
                - Be friendly and welcoming
                - Identify as being from Harry Levine Insurance (or similar insurance context)
                - Offer to help the caller

                The greeting should NOT:
                - Sound robotic or overly scripted
                - Be too long or rambling
                """,
            )
        )

        # Ensures there are no function calls or other unexpected events
        result.expect.no_more_events()


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_handles_policy_questions_appropriately() -> None:
    """Evaluation of Aizellee's ability to handle specific policy questions by directing to an agent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Run an agent turn following a specific policy question
        result = await session.run(
            user_input="What's the deductible on my auto insurance policy?"
        )

        # Evaluate that Aizellee appropriately starts collecting contact info or defers to agent
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the question and either:
                - Asks for the caller's name and phone number (following the information collection flow)
                - OR indicates that a licensed agent can help with policy specifics

                The response should:
                - NOT claim to have access to the caller's specific policy details
                - Be helpful and friendly
                - May ask for contact info in case they get disconnected
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_answers_general_insurance_questions() -> None:
    """Evaluation of Aizellee's ability to answer general questions about insurance services."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Run an agent turn following a general insurance question
        result = await session.run(user_input="What types of insurance do you offer?")

        # Evaluate that Aizellee provides helpful information about available services
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Provides helpful information about the types of insurance offered.

                The response should mention some combination of insurance types such as:
                - Home insurance
                - Auto insurance
                - Life insurance
                - Commercial/business insurance
                - Motorcycle, boat, RV, pet, or renters insurance

                The response should:
                - Be informative and helpful
                - Offer to help further or connect with an agent for quotes
                """,
            )
        )

        # Ensures there are no function calls or other unexpected events
        result.expect.no_more_events()


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_provides_office_hours() -> None:
    """Evaluation of Aizellee's ability to provide office hours and location."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Run an agent turn following a question about office hours
        result = await session.run(user_input="What are your hours?")

        # Evaluate that Aizellee provides accurate office hours (may use function tool)
        # Skip any function calls that may occur
        result.expect.skip_next_event_if(type="function_call")
        result.expect.skip_next_event_if(type="function_call_output")

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Provides the office hours information.

                The response should include:
                - Hours are 9 AM to 5 PM (or 9 to 5)
                - Monday through Friday (weekdays)

                The response should be conversational and helpful.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_stays_on_topic() -> None:
    """Evaluation of Aizellee's ability to redirect off-topic requests back to insurance services."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Run an agent turn following an off-topic request
        result = await session.run(
            user_input="Can you help me book a flight to Hawaii?"
        )

        # Evaluate that Aizellee politely redirects to insurance topics
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Redirects to insurance-related help.

                The response should EITHER:
                - Explicitly state they cannot help with flight booking and offer insurance help, OR
                - Simply redirect to insurance by saying they're here to help with insurance

                As long as they:
                - Do NOT pretend to help with flight booking
                - Remain friendly and professional
                - Offer to help with insurance-related matters

                Any redirect to insurance topics is acceptable.
                """,
            )
        )

        # Ensures there are no function calls or other unexpected events
        result.expect.no_more_events()


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_no_hallucinated_prior_context() -> None:
    """Evaluation: Aizellee should NEVER reference prior conversations that don't exist."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # First turn: user asks about a quote
        result = await session.run(user_input="I'm interested in getting a quote")

        # Skip any function calls
        result.expect.skip_next_event_if(type="function_call")
        result.expect.skip_next_event_if(type="function_call_output")

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Responds helpfully to a quote inquiry.

                The response should:
                - Acknowledge the interest in a quote
                - Ask for contact info (name and phone number) following the information collection flow
                - OR ask what type of insurance
                - Be friendly and helpful
                """,
            )
        )

        # Second turn: user gives an ambiguous response
        result = await session.run(user_input="Yeah same")

        # Skip any function calls
        result.expect.skip_next_event_if(type="function_call")
        result.expect.skip_next_event_if(type="function_call_output")

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Asks for clarification without referencing non-existent prior context.

                The response MUST:
                - Ask for clarification or the information requested
                - NOT reference "earlier", "before", "last time", "we discussed", or any prior conversation
                - NOT assume they know what the caller is referring to

                The response should be a fresh clarifying question.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_handles_vague_responses() -> None:
    """Evaluation: Aizellee should ask for clarification on vague responses."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # User gives a vague response without prior context
        result = await session.run(user_input="I want that one")

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Responds helpfully to a vague request.

                The response should either:
                - Ask for clarification on what they're referring to
                - OR ask for their contact information to help them

                The response should be friendly and professional.
                """,
            )
        )
