"""Integration tests for certificate and mortgagee/lienholder flow.

These tests verify the MortgageeCertificateAgent handles certificate
of insurance requests and mortgagee/lienholder inquiries.
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
# CERTIFICATE INTENT DETECTION TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_certificate_intent_detection_certificate_of_insurance() -> None:
    """Evaluation: Should detect 'certificate of insurance' as certificate intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="I need a certificate of insurance")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the certificate request and offers to help.

                The response should either:
                - Provide email address for certificate requests
                - Ask for more details about the certificate needed
                - Offer self-service options

                The response should be helpful and professional.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_certificate_intent_detection_coi() -> None:
    """Evaluation: Should detect 'COI' as certificate intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="I need a COI")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the COI request and offers to help.

                The response should be helpful and professional.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_certificate_intent_detection_need_certificate() -> None:
    """Evaluation: Should detect 'need certificate' as certificate intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="A vendor is asking for my certificate")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the certificate request and offers to help.

                The response should be helpful and professional.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_certificate_intent_detection_additional_insured() -> None:
    """Evaluation: Should detect 'additional insured' as certificate intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="I need to add a company as an additional insured on my certificate"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the additional insured request and offers to help.

                The response should be helpful and professional.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_certificate_intent_detection_proof_of_coverage() -> None:
    """Evaluation: Should detect 'proof of coverage' as certificate intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="I need proof of liability coverage for a contract"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the proof of coverage request and offers to help.

                The response should be helpful and professional.
                """,
            )
        )


# =============================================================================
# CERTIFICATE FLOW TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_certificate_provides_email_address() -> None:
    """Evaluation: Should provide email address for certificate requests."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="I need a certificate of insurance, how do I get one?"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Provides helpful information about getting a certificate.

                The response should either:
                - Provide an email address for certificate requests
                - Offer self-service options
                - Explain the process for obtaining a certificate

                The response should be helpful and professional.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_certificate_offers_self_service_app() -> None:
    """Evaluation: Should mention self-service app option for certificates."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="Is there a way to print my own certificate?"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Provides information about self-service options.

                The response should either:
                - Mention an app or online portal
                - Provide email/contact for assistance
                - Explain available options

                The response should be helpful and professional.
                """,
            )
        )


# =============================================================================
# MORTGAGEE/LIENHOLDER INTENT DETECTION TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_mortgagee_intent_detection_mortgagee() -> None:
    """Evaluation: Should detect 'mortgagee' as mortgagee intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="I need to update my mortgagee")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the mortgagee request and offers to help.

                The response should be helpful and professional.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_mortgagee_intent_detection_lienholder() -> None:
    """Evaluation: Should detect 'lienholder' as mortgagee intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="I need to add a lienholder to my auto policy")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the lienholder request and offers to help.

                The response should be helpful and professional.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_mortgagee_intent_detection_mortgage_company() -> None:
    """Evaluation: Should detect 'mortgage company' as mortgagee intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="My mortgage company needs to be added to my policy"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the mortgage company request and offers to help.

                The response should be helpful and professional.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_mortgagee_intent_detection_loss_payee() -> None:
    """Evaluation: Should detect 'loss payee' as mortgagee intent."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="I need to add the bank as loss payee on my auto loan"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the loss payee request and offers to help.

                The response should be helpful and professional.
                """,
            )
        )


# =============================================================================
# MORTGAGEE FLOW TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_mortgagee_provides_email_address() -> None:
    """Evaluation: Should provide email for mortgagee changes."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="How do I send you my mortgagee information?"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Provides information about how to submit mortgagee info.

                The response should either:
                - Provide an email address
                - Explain the process
                - Offer to help directly

                The response should be helpful and professional.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_mortgagee_refinancing_scenario() -> None:
    """Evaluation: Should handle refinancing mortgagee change scenario."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="I'm refinancing my house and need to change the mortgagee"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the refinancing and mortgagee change request.

                The response should be helpful and professional.
                """,
            )
        )


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_unclear_certificate_vs_mortgagee_request() -> None:
    """Evaluation: Should clarify when certificate vs mortgagee is unclear."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="My bank needs some paperwork from you"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Asks for clarification about what paperwork is needed.

                The response should ask what type of document the bank needs.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_certificate_urgent_request() -> None:
    """Evaluation: Should handle urgent certificate requests."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="I need a certificate urgently, my job starts tomorrow"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges the urgency and offers expedited help.

                The response should:
                - Acknowledge the time-sensitive nature
                - Provide fastest options available
                - Be helpful and understanding

                The response should NOT dismiss the urgency.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_combined_certificate_and_mortgagee_request() -> None:
    """Evaluation: Should handle combined certificate and mortgagee requests."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="I need a certificate and also need to update my mortgagee"
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Acknowledges both requests and offers to help with both.

                The response should:
                - Acknowledge both the certificate and mortgagee needs
                - Either address both OR prioritize one
                - Be helpful and professional
                """,
            )
        )
