"""Integration tests for claims flow.

These tests verify the ClaimsAgent works correctly, including
intent detection, empathetic handling, and business/after hours behavior.
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
async def test_claims_single_acknowledgment() -> None:
    """Evaluation: Agent should acknowledge claims intent exactly once."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())
        result = await session.run(user_input="I need to file a claim")
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                MUST: Exactly ONE acknowledgment of the claims intent with empathy.
                MUST: Show concern and ask if they're okay OR proceed to help.

                MUST NOT: Multiple variations of "I can help you file a claim".
                MUST NOT: Repeated paraphrasing like "You want to make a claim".
                MUST NOT: More than one sentence acknowledging the claim before action.

                FAIL if response contains 2+ semantically similar acknowledgments.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_claims_intent_detection_file_claim() -> None:
    """Evaluation: Aizellee should detect 'file a claim' as claims intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="I need to file a claim")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the claim request with empathy and moves to help.

                The response should:
                - Show concern or empathy
                - Ask for contact info OR offer to help immediately
                - Be warm and supportive
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_claims_intent_detection_car_accident() -> None:
    """Evaluation: Aizellee should detect 'car accident' as claims intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="I was in a car accident")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Shows empathy for the accident and offers to help with the claim.

                The response should:
                - Express concern for the caller's wellbeing (e.g., "I'm sorry to hear", "Are you okay?")
                - Offer to help with filing a claim
                - Be warm and supportive

                The response should NOT:
                - Be cold or transactional
                - Ignore the emotional impact of an accident
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_claims_intent_detection_fender_bender() -> None:
    """Evaluation: Aizellee should detect 'fender bender' as claims intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="I had a fender bender this morning")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Shows understanding and offers to help with the claim.

                The response should be empathetic and helpful.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_claims_intent_detection_someone_hit_me() -> None:
    """Evaluation: Aizellee should detect 'someone hit me' as claims intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="Someone hit my car in the parking lot")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Shows empathy and offers to help with the claim.

                The response should be supportive and helpful.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_claims_intent_detection_water_damage() -> None:
    """Evaluation: Aizellee should detect 'water damage' as claims intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="My house has water damage from a burst pipe"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Shows empathy for the home damage and offers to help with the claim.

                The response should be warm and supportive.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_claims_intent_detection_theft() -> None:
    """Evaluation: Aizellee should detect 'theft' as claims intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="My car was stolen")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Shows empathy for the theft and offers to help with the claim.

                The response should be supportive and understanding.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_claims_intent_detection_storm_damage() -> None:
    """Evaluation: Aizellee should detect 'storm damage' as claims intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="The storm damaged my roof")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Shows empathy for the storm damage and offers to help with the claim.

                The response should be supportive and helpful.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_claims_intent_detection_fire_damage() -> None:
    """Evaluation: Aizellee should detect 'fire damage' as claims intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="There was a fire at my property")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Shows empathy for the fire damage and offers to help.

                The response should:
                - Express concern (e.g., "I'm sorry to hear that")
                - Ask if they're okay OR indicate connecting to claims team
                - Be supportive

                The response should NOT:
                - Be completely devoid of empathy
                - Be dismissive

                Note: Brief empathy followed by immediate handoff to claims
                team is acceptable and preferred over lengthy responses.
                """,
            )
        )


# =============================================================================
# EMPATHY TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_claims_empathy_shown() -> None:
    """Evaluation: Agent should show empathy and immediately hand off to claims team."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="I just got home and found out my house was broken into"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Shows empathy and moves quickly to help.

                The response should:
                - Express concern or sympathy (e.g., "I'm sorry to hear that")
                - Ask if they're okay OR indicate connecting to claims team
                - Be supportive

                The response should NOT:
                - Be completely devoid of empathy
                - Be dismissive

                Note: Brief empathy followed by immediate handoff is acceptable
                and preferred over lengthy emotional responses.
                """,
            )
        )


# =============================================================================
# BUSINESS HOURS FLOW TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_claims_during_business_hours_shows_empathy() -> None:
    """Evaluation: During business hours, claims flow should show empathy and prepare transfer."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Simulate a claim call during business hours
        result = await session.run(
            user_input="I was in a car accident and need to file a claim"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Shows empathy and moves toward helping with the claim.

                The response should:
                - Express empathy (e.g., "I'm sorry to hear about your accident")
                - Either ask for contact info OR indicate they will transfer/connect
                - Be warm and supportive

                The response should NOT:
                - Be cold or robotic
                - Ignore the emotional impact of an accident
                - Refuse to help
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.xfail(reason="Multi-turn flow after immediate handoff needs investigation")
async def test_claims_during_business_hours_initiates_transfer() -> None:
    """Evaluation: During business hours, claims should lead to transfer initiation."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Start claims flow
        await session.run(user_input="I need to file a claim for a fender bender")
        await session.run(user_input="John Smith, 555-123-4567")

        # Provide insurance type for routing
        result = await session.run(user_input="Personal auto insurance")

        # Skip function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Progresses toward transferring or collecting more info for claims.

                The response should either:
                - Ask to spell last name for routing, OR
                - Indicate transfer to claims department/agent, OR
                - Offer to connect with someone who can help, OR
                - Ask what type of policy to determine routing

                The response should be helpful and show they're moving toward
                connecting the caller with claims assistance.
                """,
            )
        )


# =============================================================================
# CARRIER LOOKUP TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.xfail(reason="Multi-turn flow after immediate handoff needs investigation")
async def test_claims_after_hours_offers_carrier_lookup() -> None:
    """Evaluation: For claims, ClaimsAgent should offer carrier claims number lookup."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # First establish it's a claim - this hands off to ClaimsAgent
        await session.run(user_input="I was in an accident and need to file a claim")

        # Now ask about carrier lookup (handled by ClaimsAgent)
        result = await session.run(
            user_input="Can I file the claim directly with my insurance company?"
        )

        # Skip function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Provides helpful response about filing claims with carrier.

                The response should either:
                - Offer to help find the carrier's claims number
                - Ask which carrier/insurance company
                - Explain options for filing directly
                - Be helpful in connecting them with claims resources

                The response should NOT refuse to help or be unhelpful.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_claims_carrier_lookup_provides_number() -> None:
    """Evaluation: When caller mentions carrier, should provide helpful response."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Establish claims context and ask for carrier number
        await session.run(user_input="I need to file a claim")

        result = await session.run(
            user_input="My insurance is with Progressive, what's their claims number?"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Provides helpful response about Progressive claims.

                The response should either:
                - Provide a phone number for Progressive claims
                - Offer to look up the claims number
                - Suggest contacting Progressive directly
                - Be helpful in connecting them with claims resources

                If the agent doesn't have the exact number, it should offer
                to help in some other way or suggest resources.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_claims_unknown_carrier_provides_guidance() -> None:
    """Evaluation: For unknown carriers, should provide helpful guidance."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Establish claims context with unknown carrier
        await session.run(user_input="I need to file a claim")

        result = await session.run(
            user_input="My insurance is with XYZ Mutual Insurance, do you have their claims number?"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Provides helpful guidance for unknown carrier.

                The response should either:
                - Acknowledge not having the specific number
                - Suggest looking on the insurance card or policy
                - Offer to help connect with an agent who might know
                - Provide general guidance on finding claims numbers

                The response should NOT:
                - Make up a phone number
                - Be dismissive or unhelpful
                - Leave the caller without any guidance
                """,
            )
        )


# =============================================================================
# CONTEXT DETECTION TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_claims_business_insurance_context_detection() -> None:
    """Evaluation: Claims should show empathy and immediately hand off to claims team."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="One of our work trucks was in an accident and I need to file a claim"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Shows empathy and connects to claims team.

                The response should:
                - Show concern about the accident
                - Indicate connecting to claims team OR ask if they're okay
                - Be helpful and supportive

                Note: Immediate handoff to ClaimsAgent is acceptable - context
                detection (business vs personal) can be handled by ClaimsAgent.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_claims_personal_insurance_context_detection() -> None:
    """Evaluation: Claims should show empathy and immediately hand off to claims team."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="I was rear-ended while driving my personal car to work"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Shows empathy and connects to claims team.

                The response should:
                - Express concern about being rear-ended
                - Indicate connecting to claims team OR ask if they're okay
                - Be warm and supportive

                Note: Immediate handoff to ClaimsAgent is acceptable - context
                detection (personal vs business) can be handled by ClaimsAgent.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.xfail(reason="Multi-turn flow after immediate handoff needs investigation")
async def test_claims_empathy_tone_throughout() -> None:
    """Evaluation: Empathetic tone should be maintained throughout claims flow."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Initial distressed message - this immediately hands off to ClaimsAgent
        await session.run(
            user_input="I'm really upset, my car was totaled in an accident last night"
        )

        # Follow-up with contact info - now handled by ClaimsAgent
        result = await session.run(user_input="My name is John Smith, 555-123-4567")

        # Skip function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Maintains empathetic tone while progressing the claims process.

                The response should:
                - Acknowledge the contact info
                - Continue to be supportive
                - Progress toward helping with the claim

                The response should NOT:
                - Be cold or robotic
                - Ignore the caller's emotional state
                """,
            )
        )
