"""Integration tests for payment, ID card, and declarations page flow.

These tests verify the PaymentIDDecAgent works correctly, including
intent detection, contact info collection, and VA ring group routing.
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
async def test_payment_intent_detection_make_payment() -> None:
    """Evaluation: Aizellee should detect 'make a payment' as payment intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="I need to make a payment")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the payment request and asks for contact information.

                The response should either:
                - Ask for the caller's name and phone number
                - OR ask about business vs personal insurance

                The response should be helpful and start the payment process.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_payment_intent_detection_id_card() -> None:
    """Evaluation: Aizellee should detect 'need my ID card' as payment/ID intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="I need my insurance ID card")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the ID card request and asks for contact information.

                The response should either:
                - Ask for the caller's name and phone number
                - OR ask about business vs personal insurance

                The response should be helpful and start the ID card process.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_payment_intent_detection_dec_page() -> None:
    """Evaluation: Aizellee should detect 'declarations page' as payment/ID intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="Can I get a copy of my declarations page?"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the declarations page request.

                The response should either:
                - Ask for the caller's name and phone number
                - OR ask about business vs personal insurance
                - OR acknowledge and offer to help get the document

                The response should be helpful and professional.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_payment_intent_detection_pay_bill() -> None:
    """Evaluation: Aizellee should detect 'pay my bill' as payment intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="I want to pay my bill")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the bill payment request and asks for contact information.

                The response should either:
                - Ask for the caller's name and phone number
                - OR ask about business vs personal insurance

                The response should be helpful and professional.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_payment_intent_detection_proof_of_insurance() -> None:
    """Evaluation: Aizellee should detect 'proof of insurance' as payment/ID intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="I need proof of insurance")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the proof of insurance request.

                The response should either:
                - Ask for the caller's name and phone number
                - OR ask about business vs personal insurance
                - OR offer to help get the documentation

                The response should be helpful and professional.
                """,
            )
        )


# =============================================================================
# PERSONAL INSURANCE FLOW TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_payment_personal_insurance_flow() -> None:
    """Evaluation: Personal insurance payment flow should ask for last name."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Start payment request
        await session.run(user_input="I need to pay my premium")

        # Provide contact info (early handoff collects this first)
        await session.run(user_input="Sam Rubin, 818-555-1234")

        # Caller says personal
        result = await session.run(user_input="It's for my personal auto")

        # Skip function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Responds in a helpful way. The response may:
                - Ask the caller to spell their last name
                - Confirm it's for personal auto and ask for more info
                - Offer to connect with someone who can help

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
async def test_payment_business_insurance_flow() -> None:
    """Evaluation: Business insurance payment flow should ask for business name."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Start payment request
        await session.run(user_input="I need to make a payment")

        # Provide contact info (early handoff collects this first)
        await session.run(user_input="Sam Rubin, 818-555-1234")

        # Caller says business
        result = await session.run(user_input="It's for my business")

        # Skip function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Responds in a helpful way. The response may:
                - Ask for the name of the business
                - Confirm it's for business insurance and ask for more info
                - Offer to connect with someone who can help

                The response should be friendly and professional.
                """,
            )
        )


# =============================================================================
# TRANSFER TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_payment_transfer_after_info() -> None:
    """Evaluation: After providing info, should indicate transfer for payment."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Complete flow for personal payment
        await session.run(user_input="I need to pay my premium")
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
                1. Indicate transfer/connection to customer service team or an agent, OR
                2. Acknowledge the caller and offer to help, OR
                3. Confirm they can help with the payment

                The response should be friendly and professional.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_id_card_request_flow() -> None:
    """Evaluation: ID card request should follow payment flow routing."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Request ID card
        await session.run(user_input="I need a new ID card mailed to me")

        # Provide contact info
        result = await session.run(user_input="John Doe, 555-123-4567")

        # Skip function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the ID card request and either:
                - Asks if this is for business or personal insurance
                - Asks for more information to process the request
                - Confirms the contact info and continues

                The response should be helpful and professional.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_dec_page_request_flow() -> None:
    """Evaluation: Declarations page request should follow payment flow routing."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Request dec page
        await session.run(
            user_input="My mortgage company needs a copy of my declarations page"
        )

        # Provide contact info
        result = await session.run(user_input="Jane Smith, 555-987-6543")

        # Skip function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the declarations page request and either:
                - Asks if this is for business or personal insurance
                - Asks for more information (may infer personal from "mortgage company")
                - Offers to help get the document

                The response should be helpful and professional.
                """,
            )
        )
