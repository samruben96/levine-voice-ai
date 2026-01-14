"""Integration tests for 'something else' general inquiry flow.

These tests verify the SomethingElseAgent handles miscellaneous
inquiries that don't fit other categories.
"""

import sys

import pytest
from livekit.agents import AgentSession, inference

sys.path.insert(0, "src")
from agent import Assistant, CallerInfo

from .conftest import skip_function_events


def _llm():
    return inference.LLM(model="openai/gpt-4.1-mini")


# =============================================================================
# INTENT DETECTION TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_something_else_intent_detection_vague_request() -> None:
    """Evaluation: Aizellee should handle vague requests appropriately."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="I have a question about my account")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the account question and asks for clarification.

                The response should either:
                - Ask what specifically they need help with
                - Ask for contact info to assist them
                - Ask about business vs personal

                The response should be helpful and professional.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_something_else_intent_detection_general_inquiry() -> None:
    """Evaluation: Aizellee should handle general inquiries."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="I need some help with something")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the help request and offers assistance.

                The response should be helpful and ask what they need.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_something_else_asks_for_summary() -> None:
    """Evaluation: Agent should ask for a summary of what caller needs."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Vague request
        await session.run(user_input="I need to talk to someone about my policy")

        # Provide contact info
        result = await session.run(user_input="John Smith, 555-123-4567")

        # Skip function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Asks for more information about what they need.

                The response should either:
                - Ask what they need help with
                - Ask about business vs personal insurance
                - Ask for a summary of their inquiry

                The response should be helpful and professional.
                """,
            )
        )


# =============================================================================
# BUSINESS FLOW TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_something_else_business_flow_collects_business_name() -> None:
    """Evaluation: Business flow should collect business name."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Start with general inquiry
        await session.run(user_input="I need help with my policy")
        await session.run(user_input="Sam Rubin, 818-555-1234")

        # Confirm business
        result = await session.run(user_input="It's for my company")

        # Skip function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Asks for the name of the business.

                The response should be friendly and professional.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_something_else_business_transfer_to_correct_ae() -> None:
    """Evaluation: After business name, should transfer to Account Executive."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Complete flow
        await session.run(user_input="I have a question about my business policy")
        await session.run(user_input="Business")

        # Provide business name
        result = await session.run(user_input="Acme Corporation")

        # Skip all function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Indicates transfer to Account Executive.

                The response should be friendly and professional.
                """,
            )
        )


# =============================================================================
# PERSONAL FLOW TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_something_else_personal_insurance_context_detection() -> None:
    """Evaluation: Personal context should be detected."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="I have a question about my home insurance policy"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Recognizes personal context from "home insurance".

                The response should be helpful and professional.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_something_else_personal_flow_collects_last_name() -> None:
    """Evaluation: Personal flow should ask for spelled last name."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Start inquiry
        await session.run(user_input="I need help understanding my policy")
        await session.run(user_input="Sam Rubin, 818-555-1234")

        # Confirm personal
        result = await session.run(user_input="Personal insurance")

        # Skip function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Asks the caller to spell their last name.

                The response should be friendly and professional.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_something_else_personal_transfer_to_correct_ae() -> None:
    """Evaluation: After spelling last name, should transfer to Account Executive."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Complete flow
        await session.run(user_input="I have a question about my auto policy")
        await session.run(user_input="Personal")

        # Spell last name
        result = await session.run(user_input="S M I T H")

        # Skip all function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Indicates transfer to Account Executive.

                The response should be friendly and professional.
                """,
            )
        )


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_something_else_warm_transfer_collects_summary() -> None:
    """Evaluation: Should collect a summary for warm transfer."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Start with vague request
        await session.run(user_input="I need to discuss something with my agent")

        # Provide contact info
        await session.run(user_input="John Smith, 555-123-4567")

        # Ask what they need
        result = await session.run(user_input="Personal insurance")

        # Skip function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Either asks to spell last name OR asks for more details about their inquiry.

                The response should be helpful and professional.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_something_else_edge_case_caller_wont_spell_name() -> None:
    """Evaluation: Should offer alternatives when caller won't spell name."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Start flow
        await session.run(user_input="I need help with my policy")
        await session.run(user_input="Sam Rubin, 818-555-1234")
        await session.run(user_input="Personal")

        # Refuse to spell
        result = await session.run(user_input="I don't want to spell my name")

        # Skip function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Offers alternative or proceeds with what they have.

                The response should:
                - Be understanding
                - Offer alternative like first letter only
                - OR proceed to help them

                Should NOT refuse to help.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_something_else_multiple_topics() -> None:
    """Evaluation: Should handle caller with multiple topics."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="I need to talk about my bill and also ask about adding a driver"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the multiple topics and offers to help.

                The response should:
                - Acknowledge both requests
                - Either prioritize one OR offer to address both
                - Be helpful and professional
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_something_else_routes_to_ae_not_va() -> None:
    """Evaluation: General inquiries should route to AE, not VA team."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Complete flow for general inquiry
        await session.run(user_input="I have a general question about my policy")
        await session.run(user_input="Personal")

        # Spell last name
        result = await session.run(user_input="J O N E S")

        # Skip all function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Indicates transfer to Account Executive (not customer service team).

                General inquiries should go to AEs, not the VA team.
                The response should be friendly and professional.
                """,
            )
        )
