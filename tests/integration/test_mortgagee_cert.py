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
                - Acknowledge the request and indicate they will help
                - Provide email address for certificate requests
                - Ask for more details about the certificate needed
                - Offer self-service options

                The response should be helpful and professional. Saying something
                like "I'll help you with that" or "One moment" is acceptable
                as the email info will be provided after the handoff.
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

        result = await session.run(
            user_input="I need to add a lienholder to my auto policy"
        )

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
    """Evaluation: Should clarify when certificate vs mortgagee is unclear.

    Note: "My bank needs" indicates a CUSTOMER needing documents for their bank,
    not a bank representative calling. The agent may clarify this distinction
    or ask about what paperwork is needed.
    """
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="My bank needs some paperwork from you")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Asks for clarification to understand the caller's needs.

                The response should do ONE of these:
                - Ask what type of document the bank needs
                - Ask whether caller is a bank representative or a customer
                - Ask for more details about what paperwork is required

                Any clarifying question is acceptable since "bank" was mentioned
                and the exact need is unclear. The agent may be trying to
                distinguish between a bank rep calling vs a customer who needs
                documents for their bank.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_certificate_urgent_request() -> None:
    """Evaluation: Should handle urgent certificate requests with disambiguation.

    The enhanced flow first asks if it's a new or existing certificate,
    then provides the appropriate response.
    """
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # First request - agent should ask new vs existing
        result = await session.run(
            user_input="I need a certificate urgently, my job starts tomorrow"
        )

        # Skip function calls, assistant's handoff message, and handoff event
        # to get to MortgageeCertificateAgent's disambiguation question
        skip_function_events(result, skip_handoff=False)
        result.expect.skip_next_event_if(type="message")  # Skip assistant's ack
        result.expect.skip_next_event_if(type="agent_handoff")

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Asks whether this is for a NEW certificate or an EXISTING certificate.

                The response should ask something like:
                - "Are you calling about an existing certificate, or a new one you need issued?"
                - Or similar disambiguation question about new vs existing
                """,
            )
        )

        # Caller says it's a new certificate they need
        result = await session.run(user_input="I need a new one issued")

        # Skip function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Provides information for getting a NEW certificate issued quickly.

                The response should include:
                - Email address (Certificate@hlinsure.com) for written requests
                - Self-service app option for 24/7 certificate issuance
                - May ask about login credentials for the app

                This provides the fastest options: email or self-service app.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_certificate_existing_issue_transfer() -> None:
    """Evaluation: Should transfer to Account Executive for existing certificate issues.

    When a caller has an issue with an EXISTING certificate (not requesting a new one),
    the agent should collect their info and transfer to the appropriate Account Executive.
    """
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # First request - agent should ask new vs existing
        result = await session.run(user_input="I have a question about a certificate")

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Asks whether this is for a NEW certificate or an EXISTING certificate.

                The response should ask something like:
                - "Are you calling about an existing certificate, or a new one you need issued?"
                - Or similar disambiguation question about new vs existing
                """,
            )
        )

        # Caller says it's about an existing certificate
        result = await session.run(user_input="It's an existing certificate")

        # Skip function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Offers to connect with Account Executive and asks for insurance type.

                The response should:
                - Mention connecting with Account Executive OR someone who can help
                - Ask if this is for business or personal insurance

                This is the start of collecting info for the transfer.
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


# =============================================================================
# BANK CALLER TESTS (Direct Handling by Assistant)
# =============================================================================
# These tests verify that bank representatives calling to verify coverage
# or confirm renewal information are handled DIRECTLY by the Assistant.
#
# New expected behavior (per client request):
# 1. Agent asks: "Are you requesting renewal documents for a mutual customer?"
# 2. Agent tells them: "All requests must be submitted in writing to
#    Info@HLInsure.com and no, we don't have a fax number."
#
# This is NO LONGER a handoff to MortgageeCertificateAgent.
#
# Key trigger patterns for bank callers:
# - "calling from [bank name]"
# - "on a recorded line"
# - "mutual client"
# - "verify coverage"
# - "confirm renewal"
#
# FALSE POSITIVE scenarios to avoid:
# - Customer saying "I bank with Chase" (customer, not bank rep)
# - Customer saying "my bank needs proof of insurance" (document request)


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.mortgagee
async def test_bank_caller_full_formal_intro() -> None:
    """Evaluation: Bank rep with full formal intro handled directly by Assistant.

    Scenario: A bank representative calls with the classic formal introduction
    pattern used by mortgage companies and lenders when verifying insurance.

    Expected behavior (new per client request):
    - Agent should recognize this as a bank caller
    - Agent handles directly (NO handoff to MortgageeCertificateAgent)
    - Agent provides DIRECT response with email policy (no clarifying questions)
    - Response includes: Info@HLInsure.com, requests in writing, no fax
    """
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input=(
                "Hi, this is Sarah calling from First National Bank on a recorded line. "
                "I'm looking to confirm renewal information on a mutual client."
            )
        )

        # Skip function calls (no handoff expected)
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Provides a DIRECT, COMPLETE response for bank callers without asking
                questions first, then ends the call.

                The response MUST include ALL of these:
                - The email address Info@HLInsure.com
                - That requests must be submitted in writing
                - That no fax number is available
                - A closing/goodbye (e.g., "Have a good day", "Goodbye")

                The response MUST NOT:
                - Ask a clarifying question like "Are you requesting renewal documents?"
                - Ask "Is this for business or personal insurance?"
                - Hand off to MortgageeCertificateAgent or another sub-agent
                - Ask for more information before providing the email policy
                - Continue the conversation after providing the response

                This is a strict, direct response requirement. The agent should
                immediately provide the email policy, say goodbye, and end the call.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.mortgagee
async def test_bank_caller_abbreviated_intro() -> None:
    """Evaluation: Bank rep with abbreviated intro handled directly by Assistant.

    Scenario: A bank representative calls with a shorter, more direct introduction
    that still identifies them as a bank caller doing policy verification.

    Expected behavior (new per client request):
    - Agent should recognize this as a bank caller
    - Agent handles directly (NO handoff to MortgageeCertificateAgent)
    - Agent provides DIRECT response with email policy (no clarifying questions)
    - Response includes: Info@HLInsure.com, requests in writing, no fax
    """
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="First National Bank, calling for policy verification."
        )

        # Skip function calls (no handoff expected)
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Provides a DIRECT, COMPLETE response for bank callers without asking
                questions first, then ends the call.

                The response MUST include ALL of these:
                - The email address Info@HLInsure.com
                - That requests must be submitted in writing
                - That no fax number is available
                - A closing/goodbye (e.g., "Have a good day", "Goodbye")

                The response MUST NOT:
                - Ask a clarifying question like "Are you requesting renewal documents?"
                - Ask "Is this for business or personal insurance?"
                - Hand off to MortgageeCertificateAgent or another sub-agent
                - Ask for more information before providing the email policy
                - Ask "is this about your bank's business insurance?"
                - Continue the conversation after providing the response

                This is a strict, direct response requirement. The agent should
                immediately provide the email policy, say goodbye, and end the call.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.mortgagee
async def test_bank_caller_mutual_client_reference() -> None:
    """Evaluation: Bank caller mentioning 'mutual client' handled directly by Assistant.

    Scenario: A bank representative explicitly mentions they are calling about
    a 'mutual client', which is a key indicator of a mortgagee verification call.

    Expected behavior (new per client request):
    - Agent should recognize 'mutual client' phrase as bank caller indicator
    - Agent handles directly (NO handoff to MortgageeCertificateAgent)
    - Agent provides DIRECT response with email policy (no clarifying questions)
    - Response includes: Info@HLInsure.com, requests in writing, no fax
    """
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input=(
                "Hello, I'm calling from Chase Mortgage. "
                "I need to verify coverage on a mutual client, John Smith."
            )
        )

        # Skip function calls (no handoff expected)
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Provides a DIRECT, COMPLETE response for bank callers without asking
                questions first, then ends the call.

                The response MUST include ALL of these:
                - The email address Info@HLInsure.com
                - That requests must be submitted in writing
                - That no fax number is available
                - A closing/goodbye (e.g., "Have a good day", "Goodbye")

                The response MUST NOT:
                - Ask a clarifying question like "Are you requesting renewal documents?"
                - Ask "Is this for business or personal insurance?"
                - Hand off to MortgageeCertificateAgent or another sub-agent
                - Ask for more information before providing the email policy
                - Treat John Smith as if he's the one calling
                - Continue the conversation after providing the response

                This is a strict, direct response requirement. The agent should
                immediately provide the email policy, say goodbye, and end the call.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.mortgagee
async def test_bank_caller_verify_coverage_request() -> None:
    """Evaluation: Bank caller requesting to 'verify coverage' handled directly by Assistant.

    Scenario: A lender calls specifically to verify that coverage is in place,
    which is a common mortgagee verification scenario.

    Expected behavior (new per client request):
    - Agent should recognize 'verify coverage' from a bank as bank caller
    - Agent handles directly (NO handoff to MortgageeCertificateAgent)
    - Agent provides DIRECT response with email policy (no clarifying questions)
    - Response includes: Info@HLInsure.com, requests in writing, no fax
    """
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input=(
                "Hi, this is Wells Fargo calling. "
                "We need to verify coverage is in place for one of your policyholders."
            )
        )

        # Skip function calls (no handoff expected)
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Provides a DIRECT, COMPLETE response for bank callers without asking
                questions first, then ends the call.

                The response MUST include ALL of these:
                - The email address Info@HLInsure.com
                - That requests must be submitted in writing
                - That no fax number is available
                - A closing/goodbye (e.g., "Have a good day", "Goodbye")

                The response MUST NOT:
                - Ask a clarifying question like "Are you requesting renewal documents?"
                - Ask "Is this for business or personal insurance?"
                - Hand off to MortgageeCertificateAgent or another sub-agent
                - Ask for more information before providing the email policy
                - Treat Wells Fargo as a customer needing insurance
                - Continue the conversation after providing the response

                This is a strict, direct response requirement. The agent should
                immediately provide the email policy, say goodbye, and end the call.
                """,
            )
        )


# =============================================================================
# FALSE POSITIVE TESTS - Scenarios that should NOT route to mortgagee flow
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.mortgagee
async def test_false_positive_customer_banks_with_chase() -> None:
    """Evaluation: Customer saying 'I bank with Chase' should NOT route to mortgagee flow.

    FALSE POSITIVE SCENARIO: A customer mentions their bank in conversation,
    but they are calling about their own insurance needs, not as a bank rep.

    Expected behavior:
    - Agent should recognize this as a CUSTOMER calling about their own needs
    - Should route to NEW QUOTE flow (home insurance request)
    - Should NOT route to MortgageeCertificateAgent
    - Should begin collecting customer information for a quote
    """
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="Hi, I bank with Chase and I'm looking for home insurance."
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Handles a potential customer who mentions a bank.

                The response should do ONE of these:
                - Treat this as a new quote request for home insurance and begin
                  collecting customer info OR
                - Ask a clarifying question to confirm if this is a customer looking
                  for insurance (vs a bank rep) - this is acceptable since "bank"
                  was mentioned

                The response should NOT:
                - Immediately route to mortgagee flow without clarification
                - Provide mortgagee email info without confirming caller is a bank rep
                - Assume this is a bank representative without asking

                Note: Asking "are you the policyholder or a bank representative?" is
                acceptable and even smart behavior given "bank" was mentioned.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.mortgagee
async def test_false_positive_bank_needs_proof_of_insurance() -> None:
    """Evaluation: Customer saying 'my bank needs proof of insurance' should route to certificate/document flow.

    FALSE POSITIVE SCENARIO: A customer calls because their bank has requested
    proof of insurance. This is a document request from a policyholder, NOT
    a bank rep calling to verify coverage.

    Expected behavior:
    - Agent should recognize this as a CUSTOMER needing documents
    - Should route to certificate/document flow
    - Should treat caller as the policyholder (not a bank rep)
    """
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input=(
                "My bank needs proof of insurance for my mortgage. "
                "How do I get that sent to them?"
            )
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Recognizes this as a CUSTOMER requesting proof of insurance
                documents to satisfy their bank/mortgage company.

                The response should:
                - Treat the caller as a CUSTOMER/policyholder
                - Route to certificate/document request flow OR
                - Provide information about getting proof of insurance
                - Help the customer get documentation for their bank

                The response should NOT:
                - Treat the caller as a bank representative
                - Ask about mutual clients or coverage verification on someone else
                - Provide the mortgagee email (info@hlinsure.com) as if this is a bank calling

                The caller IS the policyholder who needs to provide documentation
                to their bank, not a bank rep calling about someone else's policy.
                The key phrase is "MY bank needs" - this indicates the caller
                owns the policy and needs to provide proof to their lender.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.mortgagee
async def test_false_positive_bank_is_requesting_certificate() -> None:
    """Evaluation: Customer saying 'the bank is requesting a certificate' should route to certificate flow.

    FALSE POSITIVE SCENARIO: A customer says their bank is requesting a certificate.
    This is similar to the proof of insurance scenario - the caller is the
    policyholder, not the bank.

    Expected behavior:
    - Agent should recognize this as a CUSTOMER needing a certificate
    - Should route to certificate flow
    - Should treat caller as the policyholder
    """
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="The bank is requesting a certificate of insurance from me."
        )

        # Skip function calls and handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Recognizes this as a CUSTOMER who needs a certificate of insurance
                to provide to their bank.

                The response should:
                - Treat the caller as a CUSTOMER/policyholder
                - Route to certificate of insurance request flow OR
                - Provide information about how to get a certificate
                - Help the customer get the document they need

                The response should NOT:
                - Treat the caller as a bank representative
                - Ask about mutual clients or policy verification for another person
                - Assume this is a bank calling to verify someone else's coverage

                The caller is the policyholder who has been asked BY their bank
                to provide a certificate. The phrase "from me" indicates this
                is the customer, not the bank.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.mortgagee
async def test_bank_caller_recorded_line_indicator() -> None:
    """Evaluation: 'On a recorded line' phrase identifies bank caller, handled directly.

    Scenario: The phrase 'on a recorded line' is a strong indicator of a
    professional/institutional caller (bank, mortgage company) as they are
    required to disclose recording for compliance.

    Expected behavior (new per client request):
    - Agent should recognize this professional caller pattern
    - Agent handles directly (NO handoff to MortgageeCertificateAgent)
    - Agent provides DIRECT response with email policy (no clarifying questions)
    - Response includes: Info@HLInsure.com, requests in writing, no fax
    """
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input=(
                "Good afternoon, this call is on a recorded line. "
                "I'm with Bank of America mortgage department calling to confirm "
                "insurance coverage for a closing next week."
            )
        )

        # Skip function calls (no handoff expected)
        # Note: With session.say(), the bank response may appear as a separate event
        skip_function_events(result)

        # Find the message containing the bank caller response
        # (may need to skip on_enter greeting depending on event ordering)
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Provides a DIRECT, COMPLETE response for bank callers without asking
                questions first.

                The response MUST include ALL of these:
                - The email address Info@HLInsure.com (or Info at HLInsure dot com)
                - That requests must be submitted in writing
                - That no fax number is available
                - A closing/goodbye (e.g., "Have a good day", "Goodbye")

                The response MUST NOT:
                - Ask a clarifying question
                - Ask about insurance type
                - Continue the conversation

                This is the direct bank caller response requirement.
                """,
            )
        )
