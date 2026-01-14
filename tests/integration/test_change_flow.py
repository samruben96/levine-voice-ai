"""Integration tests for policy change flow.

These tests verify the MakeChangeAgent works correctly, including
intent detection for various change types and smart context detection.
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
async def test_policy_change_intent_detection_make_change() -> None:
    """Evaluation: Aizellee should detect 'make a change' as policy change intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="I need to make a change to my policy")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the policy change request and either:
                - Asks for name and phone number
                - Asks about business vs personal insurance
                - Offers to help with the change

                The response should be helpful and start the policy change process.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_policy_change_intent_detection_add_vehicle() -> None:
    """Evaluation: Aizellee should detect 'add a vehicle' as policy change intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="I want to add a vehicle to my policy")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the request to add a vehicle and either:
                - Asks for name and phone number
                - Asks about business vs personal insurance
                - Offers to help with the change

                The response should be helpful and start the policy change process.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_policy_change_intent_detection_remove_driver() -> None:
    """Evaluation: Aizellee should detect 'remove a driver' as policy change intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="I need to remove a driver from my auto insurance"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the request to remove a driver and either:
                - Asks for name and phone number
                - Asks about business vs personal insurance
                - Offers to help with the change

                The response should be helpful and start the policy change process.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_policy_change_intent_detection_change_address() -> None:
    """Evaluation: Aizellee should detect 'change address' as policy change intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="I need to update my address on my policy"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the address update request and either:
                - Asks for name and phone number
                - Asks about business vs personal insurance
                - Offers to help with the change

                The response should be helpful and start the policy change process.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_policy_change_intent_detection_add_coverage() -> None:
    """Evaluation: Aizellee should detect 'add coverage' as policy change intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="I want to add coverage to my home insurance"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the request to add coverage and either:
                - Asks for name and phone number
                - Asks about business vs personal insurance
                - Offers to help with the change

                Since "home insurance" implies personal, may skip asking business/personal.
                The response should be helpful and start the policy change process.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_policy_change_intent_detection_endorsement() -> None:
    """Evaluation: Aizellee should detect 'endorsement' as policy change intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="I need an endorsement on my policy")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the endorsement request and either:
                - Asks for name and phone number
                - Asks about business vs personal insurance
                - Offers to help with the endorsement

                The response should be helpful and start the policy change process.
                """,
            )
        )


# =============================================================================
# SMART CONTEXT DETECTION TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_policy_change_intent_detection_swap_truck() -> None:
    """Evaluation: Aizellee should detect 'swap a work truck' as policy change AND infer business."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="I need to swap a work truck on my policy"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the request to swap a work truck. The response should:
                - Recognize this is likely BUSINESS insurance (work truck implies commercial)
                - Either ask for name/phone OR ask for the business name OR confirm it's business
                - May ask to confirm business insurance (that's OK - just shouldn't ask "business or personal?")

                The response should be helpful and start the policy change process.
                The key is the agent should INFER business context from "work truck".
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_policy_change_smart_context_company_vehicle() -> None:
    """Evaluation: 'company vehicle' should trigger business insurance inference."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="I need to add a company vehicle to my fleet policy"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Recognizes this is BUSINESS insurance (company vehicle + fleet = commercial).
                Should either:
                - Ask for business name directly
                - Ask for contact info first
                - Confirm this is for their business policy

                Should NOT ask "is this business or personal?" since context is clear.
                """,
            )
        )


# =============================================================================
# PERSONAL INSURANCE FLOW TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_policy_change_personal_insurance_flow() -> None:
    """Evaluation: Personal insurance change flow should ask for last name."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Start policy change request
        await session.run(user_input="I want to make a change to my policy")

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
                Either:
                - Asks the caller to spell their last name
                - OR confirms it's for personal insurance and asks for more info
                - OR offers to connect with an Account Executive

                The response should be friendly and professional.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_policy_change_transfer_after_personal_info() -> None:
    """Evaluation: After spelling last name for personal change, should transfer to AE."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Complete flow for personal policy change
        await session.run(user_input="I need to remove a driver from my policy")
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
                1. Indicate transfer/connection to an Account Executive, OR
                2. Acknowledge the caller and confirm the change request, OR
                3. Offer to connect them with someone who can help

                Should mention connecting to someone (Account Executive) for the change.
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
async def test_policy_change_business_insurance_flow() -> None:
    """Evaluation: Business insurance change flow should ask for business name."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Start policy change request
        await session.run(user_input="I need to update my policy")

        # Provide contact info
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
                - Offer to connect with an Account Executive

                The response should be friendly and professional.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_policy_change_transfer_after_business_info() -> None:
    """Evaluation: After providing business name for change, should transfer to AE."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Complete flow for business policy change
        await session.run(user_input="I need to add a vehicle to our fleet")
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
                1. Indicate transfer/connection to an Account Executive, OR
                2. Acknowledge the business name and confirm the change request, OR
                3. Offer to connect them with someone who can help

                Should mention connecting to someone (Account Executive) for the change.
                The response should be friendly and professional.
                """,
            )
        )
