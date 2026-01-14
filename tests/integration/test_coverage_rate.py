"""Integration tests for coverage and rate question flow.

These tests verify the CoverageRateAgent works correctly for
questions about policy coverage, rates, deductibles, and limits.
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
async def test_coverage_rate_intent_detection_coverage_question() -> None:
    """Evaluation: Aizellee should detect coverage questions."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="What does my policy cover?")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the coverage question and offers to help.

                The response should either:
                - Ask for contact info to look up their policy
                - Ask about business vs personal insurance
                - Offer to connect with someone who can help

                The response should be helpful and professional.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_coverage_rate_intent_detection_rate_increase() -> None:
    """Evaluation: Aizellee should detect rate increase questions."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="Why did my rates go up?")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the rate question and offers to help investigate.

                The response should be understanding and helpful.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_coverage_rate_intent_detection_premium_question() -> None:
    """Evaluation: Aizellee should detect premium questions."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="I have a question about my premium")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the premium question and offers to help.

                The response should be helpful and professional.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_coverage_rate_intent_detection_deductible() -> None:
    """Evaluation: Aizellee should detect deductible questions."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="What's my deductible?")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the deductible question and offers to help.

                The response should be helpful and professional.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_coverage_rate_intent_detection_am_i_covered() -> None:
    """Evaluation: Aizellee should detect 'am I covered' questions."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="Am I covered for flood damage?")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the coverage question and offers to help check.

                The response should be helpful and offer to investigate.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_coverage_rate_intent_detection_policy_limits() -> None:
    """Evaluation: Aizellee should detect policy limits questions."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="What are my liability limits?")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the limits question and offers to help.

                The response should be helpful and professional.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_coverage_rate_intent_detection_bill_higher() -> None:
    """Evaluation: Aizellee should detect bill questions."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="Why is my bill higher this month?")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the billing question and offers to help investigate.

                The response should be understanding and helpful.
                """,
            )
        )


# =============================================================================
# CONTEXT DETECTION TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_coverage_rate_business_context_detection() -> None:
    """Evaluation: Business context should be recognized in coverage questions."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="Does our commercial liability cover employee injuries?"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Recognizes business context and offers to help.

                The response should:
                - Recognize "commercial liability" implies business insurance
                - Ask for business name or contact info
                - Offer to connect with Account Executive

                Should NOT ask "business or personal?" since context is clear.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_coverage_rate_personal_context_detection() -> None:
    """Evaluation: Personal context should be recognized in coverage questions."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="Does my homeowners policy cover my shed?"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Recognizes personal context and offers to help.

                The response should:
                - Recognize "homeowners" implies personal insurance
                - Ask for contact info or last name
                - Offer to connect with Account Executive

                Should NOT ask "business or personal?" since context is clear.
                """,
            )
        )


# =============================================================================
# FLOW TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_coverage_rate_personal_flow_asks_last_name() -> None:
    """Evaluation: Personal coverage flow should ask for spelled last name."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Start coverage question
        await session.run(user_input="What's my coverage limit on my home insurance?")
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

                The response should be friendly and professional.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_coverage_rate_business_flow_asks_business_name() -> None:
    """Evaluation: Business coverage flow should ask for business name."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Start coverage question
        await session.run(user_input="I need to know my business liability limits")
        await session.run(user_input="Sam Rubin, 818-555-1234")

        # Confirm business
        result = await session.run(user_input="It's for my business")

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
async def test_coverage_rate_personal_transfer_to_ae() -> None:
    """Evaluation: After last name, should transfer to Account Executive."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Complete flow
        await session.run(user_input="What's my coverage for rental cars?")
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


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_coverage_rate_business_transfer_to_ae() -> None:
    """Evaluation: After business name, should transfer to Account Executive."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Complete flow
        await session.run(user_input="What's our workers comp coverage?")
        await session.run(user_input="Business")

        # Provide business name
        result = await session.run(user_input="Smith Construction LLC")

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
