"""Integration tests for new quote flow.

These tests verify the NewQuoteAgent and quote intent detection work correctly,
including contact info collection, business/personal routing, and alpha-split.
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
async def test_new_quote_intent_detection_get_quote() -> None:
    """Evaluation: Aizellee should detect 'get a quote' as new quote intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="I want to get a quote")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the quote request and asks for contact information.

                The response should either:
                - Ask for the caller's name and phone number
                - OR ask what type of insurance they need a quote for

                The response should be helpful and start the quote process.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_new_quote_intent_detection_new_policy() -> None:
    """Evaluation: Aizellee should detect 'new policy' as new quote intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="I'm looking to start a new policy")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the new policy request and asks for contact information.

                The response should either:
                - Ask for the caller's name and phone number
                - OR ask what type of insurance they need

                The response should be helpful and start the quote process.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_new_quote_intent_detection_pricing() -> None:
    """Evaluation: Aizellee should detect 'pricing on insurance' as new quote intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="Can I get pricing on auto insurance?")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the auto insurance pricing request.

                The response should either:
                - Ask for the caller's name and phone number
                - OR ask follow-up questions about the quote

                The response should be helpful and start the quote process.
                """,
            )
        )


# =============================================================================
# FLOW TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_collects_contact_info_for_quote() -> None:
    """Evaluation: Aizellee should collect name and phone for a quote request."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Ask for a quote
        await session.run(user_input="I want a quote")

        # Provide name and phone
        result = await session.run(user_input="John Smith, 555-123-4567")

        # Skip any function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the provided contact information and asks follow-up.

                The response should either:
                - Ask if this is for business or personal insurance
                - OR acknowledge the info and ask what type of insurance they need

                The response should be helpful and continue the quote process.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_new_quote_asks_business_or_personal() -> None:
    """Evaluation: Quote flow should ask business or personal insurance."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Start quote request
        await session.run(user_input="I need insurance")

        # Provide contact info
        result = await session.run(user_input="Sam Rubin, 818-555-1234")

        # Skip any function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Either:
                1. Asks if this is for business or personal insurance, OR
                2. Acknowledges the contact info and asks about what they need, OR
                3. Asks what type of insurance they're looking for

                The response should be conversational and helpful.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_asks_business_or_personal() -> None:
    """Evaluation: Aizellee should determine insurance type for routing."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Start with a vague request
        result = await session.run(user_input="I need help with my insurance")

        # Skip function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Asks clarifying questions about the insurance need.

                The response should either:
                - Ask for contact info (name and phone)
                - OR ask what type of insurance help they need
                - OR ask if this is for business or personal insurance

                The response should be helpful and begin the assistance process.
                """,
            )
        )


# =============================================================================
# PERSONAL INSURANCE FLOW TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_personal_insurance_asks_for_last_name() -> None:
    """Evaluation: Personal insurance flow should ask for spelled last name."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Start quote request
        await session.run(user_input="I need a quote")

        # Provide contact info
        await session.run(user_input="Sam Rubin, 818-555-1234")

        # Caller says personal
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

                The response should:
                - Ask the caller to spell out their last name letter by letter
                - May mention this is to connect them to the right agent
                - Be friendly and helpful
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_personal_quote_transfers_after_last_name() -> None:
    """Evaluation: After spelling last name, should transfer to sales agent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Complete flow for personal quote
        await session.run(user_input="I want to get a quote")
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
                The response should either:
                1. Indicate transfer/connection to a Sales Agent, OR
                2. Acknowledge the spelled name and confirm routing, OR
                3. Confirm they can help with the quote and continue

                The response should be friendly and professional.
                """,
            )
        )


# =============================================================================
# BUSINESS INSURANCE FLOW TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_business_insurance_asks_for_business_name() -> None:
    """Evaluation: Business insurance flow should ask for business name."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Start quote request
        await session.run(user_input="I need a quote")

        # Provide contact info
        await session.run(user_input="Sam Rubin, 818-555-1234")

        # Caller says business
        result = await session.run(user_input="Business insurance")

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
                - Be friendly and helpful
                - May mention this is to connect them to the right person
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_business_quote_transfers_after_business_name() -> None:
    """Evaluation: After providing business name, should transfer to sales agent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Complete flow for business quote
        await session.run(user_input="I need a quote for my business")
        await session.run(user_input="Business")

        # Provide business name
        result = await session.run(user_input="Smith Trucking LLC")

        # Skip all function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                The response should either:
                1. Indicate transfer/connection to a Sales Agent, OR
                2. Acknowledge the business name and confirm routing, OR
                3. Confirm they can help with the quote and continue

                The response should be friendly and professional.
                """,
            )
        )


# =============================================================================
# RESTRICTED TRANSFER TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_restricted_transfer_jason() -> None:
    """Evaluation: Requesting Jason should get special handling (restricted transfer)."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="Can I speak to Jason?")

        # Skip any function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Responds appropriately to request for Jason (management).

                The response should:
                - Acknowledge the request for Jason
                - Either ask for more info OR explain that Jason requires a direct call
                - Be helpful and professional

                Note: Jason may have restricted transfer requirements.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_restricted_transfer_fred() -> None:
    """Evaluation: Requesting Fred should get special handling (restricted transfer)."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="I need to talk to Fred please")

        # Skip any function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Responds appropriately to request for Fred.

                The response should:
                - Acknowledge the request for Fred
                - Either ask for more info OR explain transfer process
                - Be helpful and professional

                Note: Fred may have restricted transfer requirements.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_normal_agent_transfer() -> None:
    """Evaluation: Requesting a normal agent should proceed with transfer."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="Can I speak to Adriana?")

        # Skip any function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Responds to request for Adriana with helpful transfer handling.

                The response should either:
                - Confirm transfer to Adriana
                - Ask for additional info before transferring
                - Acknowledge the request and help connect

                The response should be friendly and helpful.
                """,
            )
        )
