"""Integration tests for policy cancellation flow.

These tests verify the CancellationAgent works correctly, including
intent detection, empathetic handling, and professional tone.
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
async def test_cancellation_intent_detection_cancel_policy() -> None:
    """Evaluation: Aizellee should detect 'cancel my policy' as cancellation intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="I want to cancel my policy")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the cancellation request in a professional manner.

                The response should:
                - Show understanding or empathy about the cancellation request
                - Ask for name and phone number OR ask about business vs personal insurance
                - Be professional and not aggressive about retention

                The response should NOT:
                - Be pushy or make the caller feel guilty
                - Refuse to help with cancellation
                - Sound robotic or dismissive
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_cancellation_intent_detection_need_to_cancel() -> None:
    """Evaluation: Aizellee should detect 'I need to cancel my insurance' as cancellation intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="I need to cancel my insurance")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the cancellation request and either:
                - Asks for name and phone number
                - Asks about business vs personal insurance
                - Shows empathy and offers to help

                The response should be professional and helpful, not dismissive.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_cancellation_intent_detection_calling_to_cancel() -> None:
    """Evaluation: Aizellee should detect 'I'm calling to cancel' as cancellation intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="I'm calling to cancel")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the cancellation request and either:
                - Asks for name and phone number
                - Asks about business vs personal insurance
                - Shows understanding and offers to help

                The response should be professional and respectful.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_cancellation_intent_detection_found_cheaper() -> None:
    """Evaluation: Aizellee should detect 'found cheaper insurance' as cancellation intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="I found cheaper insurance and want to switch"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the caller's intent to switch/cancel and either:
                - Asks for name and phone number
                - Asks about business vs personal insurance
                - Shows understanding without being pushy

                The response should NOT:
                - Aggressively push back on the decision
                - Make the caller feel guilty
                - Refuse to help with the cancellation
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_cancellation_intent_detection_dont_need_anymore() -> None:
    """Evaluation: Aizellee should detect 'don't need insurance anymore' as cancellation intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="I don't need insurance anymore")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the cancellation request and either:
                - Asks for name and phone number
                - Asks about business vs personal insurance
                - Shows understanding

                The response should be professional and helpful.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_cancellation_intent_detection_dont_renew() -> None:
    """Evaluation: Aizellee should detect 'please don't renew my policy' as cancellation intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="Please don't renew my policy")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the non-renewal/cancellation request and either:
                - Asks for name and phone number
                - Asks about business vs personal insurance
                - Shows understanding and offers to help

                The response should be professional and respectful.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_cancellation_intent_detection_switching_carriers() -> None:
    """Evaluation: Aizellee should detect 'switching carriers' as cancellation intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="I'm switching carriers")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the intent to switch carriers and either:
                - Asks for name and phone number
                - Asks about business vs personal insurance
                - Shows understanding

                The response should NOT:
                - Be pushy about retention
                - Make the caller feel bad about their decision
                """,
            )
        )


# =============================================================================
# CONTEXT DETECTION TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_cancellation_business_insurance_context_detection() -> None:
    """Evaluation: Business context clues should trigger business insurance flow."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="I need to cancel our company policy, we're closing the business"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Recognizes this is BUSINESS insurance from "company policy" context.

                The response should:
                - Show empathy about the business closing
                - Either ask for the business name OR ask for contact info first
                - Confirm it's for business insurance (that's OK)

                Should NOT ask "is this business or personal?" since context is clear.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_cancellation_personal_insurance_context_detection() -> None:
    """Evaluation: Personal context clues should trigger personal insurance flow."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="I need to cancel my car insurance, I sold my vehicle"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Recognizes this is about car/auto insurance (personal context).

                The response should:
                - Show understanding about the cancellation request (selling vehicle)
                - Ask for contact info OR ask to spell last name OR both
                - Be empathetic and professional

                It's acceptable to:
                - Confirm "personal car insurance" or "your car insurance"
                - Ask for confirmation that it's personal (brief confirmation is OK)

                It should NOT:
                - Ask "is this business or personal?" as if it doesn't know the context
                - Ignore the car insurance context entirely

                Brief confirmation questions like "Is this for your personal car insurance?"
                are acceptable since they show recognition of the context.
                """,
            )
        )


# =============================================================================
# EMPATHY AND TONE TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_cancellation_empathy_shown() -> None:
    """Evaluation: Agent should show empathy for cancellation without being pushy."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="I have to cancel my policy, things are really tight financially right now"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Shows empathy and understanding about the caller's situation.

                The response should:
                - Show understanding or sympathy (e.g., "I understand", "I'm sorry to hear")
                - NOT be dismissive or cold
                - NOT push retention aggressively
                - Continue with the standard flow (contact info or insurance type)

                The response should NOT:
                - Guilt the caller
                - Aggressively try to change their mind
                - Be robotic or uncaring
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_cancellation_professional_tone_not_aggressive() -> None:
    """Evaluation: Agent should be professional and not aggressive about retention."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="I want to cancel immediately, I've made up my mind"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Respects the caller's decision and helps them proceed.

                The response should:
                - Acknowledge and respect their decision
                - Proceed with the cancellation flow
                - Be professional and helpful

                The response should NOT:
                - Try to talk them out of it
                - Ask "are you sure?" repeatedly
                - Be pushy or aggressive about retention
                - Make the caller feel bad
                """,
            )
        )


# =============================================================================
# FLOW TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_cancellation_business_flow_collects_business_name() -> None:
    """Evaluation: Business cancellation flow should collect business name."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Start cancellation request for business
        await session.run(user_input="I need to cancel my commercial insurance")
        await session.run(user_input="Sam Rubin, 818-555-1234")

        # Confirm business
        result = await session.run(user_input="Yes, it's for my business")

        # Skip function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Asks for the name of the business.

                The response should:
                - Ask "What is the name of the business?" or similar
                - Be friendly and professional
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_cancellation_personal_flow_collects_last_name() -> None:
    """Evaluation: Personal cancellation flow should ask for spelled last name."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Start cancellation request for personal
        await session.run(user_input="I need to cancel my home insurance")
        await session.run(user_input="Sam Rubin, 818-555-1234")

        # Confirm personal
        result = await session.run(user_input="It's personal insurance")

        # Skip function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Asks the caller to spell their last name.

                The response should:
                - Ask "Can you spell your last name?" or similar
                - May mention this is to connect them to the right person
                - Be friendly and professional
                """,
            )
        )


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_cancellation_edge_case_caller_wont_spell_name() -> None:
    """Evaluation: Agent should offer first letter alternative when caller won't spell name."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Start cancellation flow
        await session.run(user_input="I want to cancel my policy")
        await session.run(user_input="Sam Rubin, 818-555-1234")
        await session.run(user_input="Personal insurance")

        # Refuse to spell name
        result = await session.run(
            user_input="I don't want to spell it, can't you just look it up?"
        )

        # Skip function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Offers an alternative when caller won't spell their name.

                The response should:
                - Acknowledge the caller's reluctance
                - Offer an alternative like "just the first letter" or similar
                - OR proceed with the information they have
                - Be understanding and flexible

                Should NOT:
                - Be rigid or demanding
                - Refuse to help
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_cancellation_edge_case_unclear_business_personal() -> None:
    """Evaluation: Agent should ask when business/personal type is unclear."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Vague cancellation request
        result = await session.run(user_input="I need to cancel my policy")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Appropriately handles the vague cancellation request.

                The response should either:
                - Ask for contact info (name and phone number) first, OR
                - Ask if this is for business or personal insurance

                The response should be helpful and start the cancellation process.
                """,
            )
        )
