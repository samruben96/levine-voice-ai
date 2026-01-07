import pytest
from livekit.agents import AgentSession, inference, llm

from agent import Assistant


def _llm() -> llm.LLM:
    return inference.LLM(model="openai/gpt-4.1-mini")


@pytest.mark.asyncio
async def test_receptionist_greeting() -> None:
    """Evaluation of Lucy's greeting as Harry Levine Insurance receptionist."""
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(Assistant())

        # Run an agent turn following the user's greeting (simulating an incoming call)
        result = await session.run(user_input="Hello")

        # Evaluate that Lucy greets as an insurance agency receptionist
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Greets the caller in a warm, professional manner as a receptionist.

                The greeting should:
                - Be friendly and welcoming
                - Identify as being from Harry Levine Insurance Agency (or similar insurance context)
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
async def test_handles_policy_questions_appropriately() -> None:
    """Evaluation of Lucy's ability to handle specific policy questions by directing to an agent."""
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(Assistant())

        # Run an agent turn following a specific policy question
        result = await session.run(
            user_input="What's the deductible on my auto insurance policy?"
        )

        # Evaluate that Lucy appropriately defers specific policy details to a licensed agent
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the question and directs the caller to speak with a licensed agent.

                The response should:
                - NOT claim to have access to the caller's specific policy details
                - Indicate that a licensed agent can help with policy specifics
                - Remain helpful and friendly

                The response may include:
                - Offering to take a message or callback number
                - Explaining that agents can look up policy details
                - Offering to transfer or connect them with an agent
                """,
            )
        )

        # Ensures there are no function calls or other unexpected events
        result.expect.no_more_events()


@pytest.mark.asyncio
async def test_answers_general_insurance_questions() -> None:
    """Evaluation of Lucy's ability to answer general questions about insurance services."""
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(Assistant())

        # Run an agent turn following a general insurance question
        result = await session.run(user_input="What types of insurance do you offer?")

        # Evaluate that Lucy provides helpful information about available services
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
                - Sound natural, not like reading a list
                - Offer to help further or connect with an agent for quotes
                """,
            )
        )

        # Ensures there are no function calls or other unexpected events
        result.expect.no_more_events()


@pytest.mark.asyncio
async def test_provides_office_hours() -> None:
    """Evaluation of Lucy's ability to provide office hours and location."""
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(Assistant())

        # Run an agent turn following a question about office hours
        result = await session.run(user_input="What are your hours?")

        # Evaluate that Lucy provides accurate office hours
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

        # Ensures there are no function calls or other unexpected events
        result.expect.no_more_events()


@pytest.mark.asyncio
async def test_stays_on_topic() -> None:
    """Evaluation of Lucy's ability to redirect off-topic requests back to insurance services."""
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(Assistant())

        # Run an agent turn following an off-topic request
        result = await session.run(
            user_input="Can you help me book a flight to Hawaii?"
        )

        # Evaluate that Lucy politely redirects to insurance topics
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Politely clarifies their role and redirects to insurance-related help.

                The response should:
                - Not pretend to be able to help with flight booking
                - Politely explain they're an insurance agency
                - Offer to help with insurance-related matters instead
                - Remain friendly and professional
                """,
            )
        )

        # Ensures there are no function calls or other unexpected events
        result.expect.no_more_events()


@pytest.mark.asyncio
async def test_no_hallucinated_prior_context() -> None:
    """Evaluation: Lucy should NEVER reference prior conversations that don't exist."""
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(Assistant())

        # First turn: user asks about a quote
        result = await session.run(user_input="I'm interested in getting a quote")

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Responds helpfully to a quote inquiry.

                The response should:
                - Acknowledge the interest in a quote
                - Ask what type of insurance OR ask for contact info
                - Be friendly and helpful
                """,
            )
        )
        result.expect.no_more_events()

        # Second turn: user gives an ambiguous response
        result = await session.run(user_input="Yeah same")

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Asks for clarification without referencing non-existent prior context.

                The response MUST:
                - Ask what type of insurance they're interested in
                - NOT reference "earlier", "before", "last time", "we discussed", or any prior conversation
                - NOT assume they know what the caller is referring to

                The response should be a fresh clarifying question like:
                - "Which type of insurance are you interested in?"
                - "What kind of coverage are you looking for?"
                """,
            )
        )
        result.expect.no_more_events()


@pytest.mark.asyncio
async def test_handles_vague_responses() -> None:
    """Evaluation: Lucy should ask for clarification on vague responses."""
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
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
                Asks for clarification on what the caller means.

                The response should:
                - Politely ask what they're referring to
                - NOT make assumptions about what "that one" means
                - NOT reference any prior conversation
                - Offer to help once they clarify

                Example good responses:
                - "I'd be happy to help! Could you tell me what you're looking for?"
                - "Sure! What type of insurance are you interested in?"
                """,
            )
        )
        result.expect.no_more_events()
