"""Integration tests for no-repetition behavior.

These tests validate that the agent does not repeat questions or acknowledgments,
ensuring callers have a smooth experience without redundant prompts.

The single-agent architecture (Assistant with direct transfer tools) was specifically
designed to prevent the double-asking bug that occurred with multi-agent handoffs.

This module also tests the single-speech handoff behavior where:
- Assistant delivers empathy/acknowledgment BEFORE handoff
- Sub-agents skip duplicate empathy/acknowledgment by checking _handoff_speech_delivered flag
- AfterHoursAgent resets the flag to deliver its own greeting
"""

import sys

import pytest
from livekit.agents import AgentSession

sys.path.insert(0, "src")
from agent import Assistant, CallerInfo

from .conftest import _llm, skip_function_events

# =============================================================================
# CONTACT INFO REPETITION TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_contact_info_not_reasked_after_providing() -> None:
    """Evaluation: After providing name/phone, agent should NOT ask for it again."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Request a quote
        await session.run(user_input="I need a quote for insurance")

        # Provide contact info
        await session.run(user_input="John Smith, 555-123-4567")

        # Continue with more details - should NOT re-ask for contact info
        result = await session.run(user_input="It's for personal auto insurance")

        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                MUST: Proceed with the quote process (e.g., ask to spell last name,
                ask about coverage type, or indicate transfer).

                MUST NOT: Ask for name and phone number again.
                MUST NOT: Say "Can I get your name?" or "What's your phone number?"
                MUST NOT: Repeat the contact info collection step.

                The caller already provided "John Smith, 555-123-4567" - the agent
                should remember this and move forward with the next step in the flow.

                FAIL if the response asks for name, phone number, or contact info.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_contact_info_not_reasked_on_policy_change() -> None:
    """Evaluation: After providing contact info for policy change, agent should NOT re-ask."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Request a policy change
        await session.run(user_input="I need to make a change to my policy")

        # Provide contact info
        await session.run(user_input="Maria Garcia, 407-555-8899")

        # Answer the insurance type question
        result = await session.run(user_input="It's my personal homeowners policy")

        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                MUST: Progress the policy change request (ask to spell last name,
                or indicate transfer to an agent who can help).

                MUST NOT: Re-ask for name or phone number.
                MUST NOT: Say things like "Before I transfer you, can I get your name?"

                The caller already provided "Maria Garcia, 407-555-8899" and the agent
                must remember this information throughout the conversation.

                FAIL if the agent asks for contact information again.
                """,
            )
        )


# =============================================================================
# LAST NAME SPELLING REPETITION TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_last_name_spelling_asked_only_once() -> None:
    """Evaluation: Spelling of last name should be requested only once for routing."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Complete a personal insurance quote flow
        await session.run(user_input="I need a quote for home insurance")
        await session.run(user_input="Personal insurance")

        # Spell the last name
        await session.run(user_input="S M I T H")

        # Make any follow-up comment
        result = await session.run(user_input="I'm looking for the best coverage")

        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                MUST: Either transfer/connect to an agent OR continue helping
                with the quote details.

                MUST NOT: Ask the caller to spell their last name again.
                MUST NOT: Say "Can you spell that for me?" or "What was the spelling?"
                MUST NOT: Re-request the spelling that was already provided.

                The caller already spelled "S M I T H" - the agent has this info
                and should proceed with routing or transfer.

                FAIL if the agent asks for the last name spelling again.
                """,
            )
        )


# =============================================================================
# INTENT ACKNOWLEDGMENT REPETITION TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_intent_acknowledged_once_not_multiple_times() -> None:
    """Evaluation: Intent should be acknowledged ONCE, not with multiple paraphrases."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="I need to make a payment on my policy")

        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                MUST: Exactly ONE acknowledgment of the payment intent.
                MUST: Move quickly to ask for contact info OR offer to help.

                MUST NOT: Multiple variations of "I can help you with a payment".
                MUST NOT: Repeated paraphrasing like "So you want to make a payment.
                I understand you need to pay. Let me help you pay your bill."
                MUST NOT: More than one sentence acknowledging the payment intent.

                Good example: "I can help with that. May I have your name and phone number?"
                Bad example: "I'd be happy to help with your payment. So you need to make
                a payment on your policy. I can certainly assist you with paying your bill."

                FAIL if response contains 2+ semantically similar acknowledgments of
                the payment intent before asking for info or taking action.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_quote_intent_single_acknowledgment() -> None:
    """Evaluation: Quote request should have single acknowledgment, not multiple."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="I want to get a quote for car insurance")

        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                MUST: Respond to the quote request helpfully.
                SHOULD: Acknowledge and ask for info (name, phone, or insurance type).

                MUST NOT: Have multiple REDUNDANT acknowledgments like:
                "I can help with a quote. I'd be happy to get you a quote.
                Let me help you with that quote."

                A single acknowledgment followed by a question is fine.
                E.g., "I can help with that. May I have your name?"

                FAIL only if there are clearly REDUNDANT/DUPLICATE phrases
                all saying the same thing about helping with a quote.
                """,
            )
        )


# =============================================================================
# EMPATHY REPETITION TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_claims_empathy_not_repeated_across_turns() -> None:
    """Evaluation: 'I'm sorry to hear that' empathy should appear only ONCE."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Initial claim request - empathy expected here
        await session.run(user_input="I was in a car accident and need to file a claim")

        # Provide additional details - should NOT repeat empathy
        result = await session.run(
            user_input="It happened this morning on my way to work"
        )

        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                MUST: Acknowledge the additional detail and continue helping.
                MUST: Focus on progressing the claims process (ask for contact info,
                ask about carrier, or indicate transfer).

                MUST NOT: Repeat the empathy expression from the first turn.
                MUST NOT: Say "I'm sorry to hear that" or "that's terrible" again.
                MUST NOT: Re-express shock or sympathy that was already conveyed.

                The first response already showed empathy. This response should
                focus on gathering information or moving forward, not re-emoting.

                FAIL if the response contains another "sorry to hear" or equivalent
                empathy phrase that was already expressed.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_cancellation_empathy_single_expression() -> None:
    """Evaluation: Understanding about cancellation expressed only ONCE."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Cancellation with context - empathy expected here
        await session.run(
            user_input="I need to cancel my policy, things are tight financially"
        )

        # Provide contact info - should NOT re-express empathy
        result = await session.run(user_input="My name is John Doe, 555-444-3333")

        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                MUST: Acknowledge the contact info and continue the cancellation flow.
                MUST: Ask about business vs personal OR ask for last name spelling.

                MUST NOT: Re-express empathy about financial difficulties.
                MUST NOT: Say "I understand times are tough" or similar again.
                MUST NOT: Repeat sympathetic statements from the first turn.

                The caller already heard empathy. Now the agent should be efficient
                and help them complete their request.

                FAIL if the response repeats empathy/understanding about finances.
                """,
            )
        )


# =============================================================================
# INSURANCE TYPE DETERMINATION TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_insurance_type_determined_once() -> None:
    """Evaluation: Business/personal type should be asked only ONCE."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Quote request
        await session.run(user_input="I need a quote")
        await session.run(user_input="Sarah Johnson, 321-555-7890")

        # Indicate personal insurance
        await session.run(user_input="It's personal insurance, for my home")

        # Continue the conversation
        result = await session.run(user_input="I just bought the house last month")

        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                MUST: Progress the quote flow - ask to spell last name, discuss
                coverage details, or indicate transfer to an agent.

                MUST NOT: Ask "Is this for business or personal?" again.
                MUST NOT: Re-confirm the insurance type that was already stated.
                MUST NOT: Say "Just to confirm, this is personal insurance, right?"

                The caller already said "personal insurance, for my home" - the agent
                should remember this and not re-ask.

                FAIL if the agent asks about business vs personal again.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_business_name_not_reasked() -> None:
    """Evaluation: Business name should be collected only ONCE."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Business quote flow
        await session.run(user_input="I need commercial insurance")
        await session.run(user_input="Business insurance")

        # Provide business name
        await session.run(user_input="The business is called Smith Trucking LLC")

        # Continue conversation
        result = await session.run(user_input="We have about 10 trucks in our fleet")

        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                MUST: Either transfer to a commercial lines agent OR continue
                gathering relevant information for the quote.

                MUST NOT: Ask for the business name again.
                MUST NOT: Say "What is the name of your business?" when it was
                already provided as "Smith Trucking LLC".

                The agent should remember "Smith Trucking LLC" and proceed.

                FAIL if the agent asks for the business name again.
                """,
            )
        )


# =============================================================================
# TRANSFER ANNOUNCEMENT TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_transfer_announcement_not_duplicated() -> None:
    """Evaluation: 'Let me connect you' should appear only ONCE before transfer."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Complete flow to get to transfer point
        await session.run(user_input="I need a quote for personal auto")
        await session.run(user_input="David Williams, 407-555-1234")

        # Spell last name to trigger transfer
        result = await session.run(user_input="W I L L I A M S")

        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                MUST: Respond to the spelled name by continuing the quote flow.
                SHOULD: Either ask for more info OR indicate transfer.

                MUST NOT: Have DUPLICATE transfer announcements like:
                "I'll transfer you now. Let me connect you. I'm putting you through."

                A single transfer announcement is fine.
                E.g., "I'm connecting you with Brad now."

                Also acceptable: asking a follow-up question if more info needed.

                FAIL only if there are clearly REDUNDANT/DUPLICATE transfer
                announcements in the same response.
                """,
            )
        )


# =============================================================================
# CROSS-AGENT CONTEXT PRESERVATION TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_claims_handoff_preserves_caller_context() -> None:
    """After providing info to Assistant, ClaimsAgent should not re-ask."""
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Provide name and phone to Assistant
        await session.run(user_input="I need to file a claim")
        await session.run(user_input="John Smith, 555-123-4567")

        # After handoff to ClaimsAgent, should not re-ask for name/phone
        result = await session.run(user_input="Yes, I'm okay, just shaken up")

        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                MUST NOT: Ask for name or phone number again.
                MUST NOT: Say "Can I get your name?" or "What's your phone number?"

                The caller already provided "John Smith, 555-123-4567" to the
                Assistant before the handoff. This context should be preserved.
                """,
            )
        )


# =============================================================================
# SINGLE-SPEECH HANDOFF TESTS
# =============================================================================
# These tests verify that handoffs between agents don't result in duplicate
# empathy or acknowledgment messages. The pattern is:
# 1. Assistant delivers empathy/acknowledgment BEFORE calling the handoff tool
# 2. Sub-agent checks _handoff_speech_delivered flag in on_enter()
# 3. If flag is True, sub-agent skips redundant empathy/acknowledgment


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_claims_handoff_single_empathy() -> None:
    """Evaluation: When user says 'I need to file a claim', only ONE empathy message is spoken.

    The Assistant should express empathy and mention connecting to claims team
    BEFORE the handoff. The ClaimsAgent should NOT repeat the empathy.

    This tests the single-speech handoff pattern where the Assistant handles
    the empathetic response and the ClaimsAgent proceeds without duplication.
    """
    # Test during business hours - ClaimsAgent transfers immediately
    business_hours_context = (
        "CURRENT TIME: 2:30 PM ET, Wednesday\nOFFICE STATUS: Open (closes at 5 PM)"
    )

    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(
            Assistant(
                business_hours_context=business_hours_context,
                is_after_hours=False,
            )
        )

        # Single claim request - should get exactly ONE empathetic response
        result = await session.run(
            user_input="I was in a car accident and need to file a claim"
        )

        # Skip function calls (route_call_claims) and potential handoff
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                MUST: Show empathy about the accident (e.g., "I'm sorry to hear that").
                MUST: Be supportive and helpful.

                ACCEPTABLE: A response like "I'm so sorry to hear that. Are you okay?
                Let me connect you with our claims team." This combines empathy,
                checking on wellbeing, and indicating transfer - all in one natural flow.

                MUST NOT: Multiple SEPARATE empathy expressions like:
                "I'm so sorry to hear that. That sounds terrible. I'm really sorry
                about your accident. How awful for you."

                MUST NOT: Repeating the same empathy sentiment multiple times.

                The key is that the empathy should be expressed ONCE, not that
                asking "are you okay" AND mentioning transfer is wrong - those
                are different types of statements (checking wellbeing vs action).

                FAIL only if there are multiple redundant empathy phrases
                (e.g., "sorry" said multiple times, or multiple expressions
                of sympathy like "that's terrible" and "how awful").
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_claims_handoff_flag_set() -> None:
    """Verify the _handoff_speech_delivered flag behavior for claims handoff.

    When Assistant calls route_call_claims:
    - ClaimsAgent is expected to NOT repeat empathy because Assistant already said it
    - The ClaimsAgent instructions explicitly say "Do NOT say empathy - already said by receptionist"

    This test verifies that after a claims handoff during business hours,
    the subsequent response from ClaimsAgent is NOT repeating empathy.
    """
    business_hours_context = (
        "CURRENT TIME: 10:30 AM ET, Tuesday\nOFFICE STATUS: Open (closes at 5 PM)"
    )

    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(
            Assistant(
                business_hours_context=business_hours_context,
                is_after_hours=False,
            )
        )

        # File a claim - triggers handoff to ClaimsAgent
        await session.run(user_input="I need to file a claim for a fender bender")

        # After handoff, continue the conversation
        # ClaimsAgent should NOT repeat "I'm sorry to hear that"
        result = await session.run(user_input="What do I need to do next?")

        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                MUST: Provide helpful information about next steps OR indicate transfer.
                MUST: Be professional and supportive.

                MUST NOT: Start with "I'm sorry to hear about your accident" again.
                MUST NOT: Re-express empathy that was already conveyed in the first turn.
                MUST NOT: Ask "Are you okay?" again if already asked.

                The previous turn already expressed empathy. This response should
                focus on practical next steps without repeating the empathy.

                FAIL if the response contains empathy phrases that duplicate
                what was already said in the initial claim acknowledgment.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_certificate_handoff_no_duplicate_ack() -> None:
    """Verify certificate requests don't get duplicate acknowledgments.

    When Assistant routes to MortgageeCertificateAgent:
    1. Assistant sets _handoff_speech_delivered = True
    2. MortgageeCertificateAgent checks the flag in on_enter()
    3. If flag is True, it skips "I can help you with that" acknowledgment

    This test verifies there's no duplicate "I can help you with that" or similar.
    """
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Request a certificate of insurance
        result = await session.run(
            user_input="I need a certificate of insurance for a contractor"
        )

        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                MUST: Respond helpfully to the certificate request.
                SHOULD: Acknowledge the request and/or provide certificate info.

                MUST NOT: Say "I can help you with that" TWICE (or similar phrases).
                MUST NOT: Have DUPLICATE acknowledgment phrases like:
                "I can help with that. Sure, I can help with that."
                "Got it. Got it, I understand."

                A single acknowledgment is fine. The key test is that there
                are NOT two separate acknowledgments in the same response.

                FAIL only if there are clearly redundant/duplicate acknowledgments.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_mortgagee_handoff_no_duplicate_ack() -> None:
    """Verify mortgagee requests don't get duplicate acknowledgments.

    When Assistant routes to MortgageeCertificateAgent for mortgagee:
    1. Assistant sets _handoff_speech_delivered = True
    2. MortgageeCertificateAgent checks the flag in on_enter()
    3. If flag is True, it skips redundant acknowledgment

    This test verifies there's no duplicate acknowledgment for mortgagee requests.
    """
    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant())

        # Request mortgagee update
        result = await session.run(
            user_input="I need to add a new mortgagee to my homeowners policy"
        )

        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                MUST: Provide helpful information about the mortgagee request.
                SHOULD: Either mention email requirement OR ask for more info
                OR acknowledge and move to next step.

                MUST NOT: Have DUPLICATE acknowledgment phrases like:
                "I can help you with that. Let me help you with that."
                "Got it. Got it."
                "Sure, I can help. I'd be happy to help."

                A SINGLE acknowledgment followed by action is fine.
                E.g., "Got it. [email info]" or "I can help with that. [next step]"

                FAIL only if there are clearly REDUNDANT acknowledgments
                (the same acknowledgment said twice in different words).
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_after_hours_resets_flag() -> None:
    """Verify AfterHoursAgent resets the flag so it can deliver its own greeting.

    When Assistant routes to AfterHoursAgent:
    1. AfterHoursAgent.on_enter() resets _handoff_speech_delivered = False
    2. This allows AfterHoursAgent to deliver its own after-hours greeting

    The AfterHoursAgent needs to inform callers that the office is closed
    and collect their information for callback, so it must deliver its greeting.
    """
    # Set after-hours context
    after_hours_context = (
        "CURRENT TIME: 7:30 PM ET, Tuesday\n"
        "OFFICE STATUS: Closed (reopens tomorrow at 9 AM)"
    )

    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(
            Assistant(
                business_hours_context=after_hours_context,
                is_after_hours=True,
            )
        )

        # Make a general request that should route to AfterHoursAgent
        # (not claims/certificates/mortgagee/hours which have special handling)
        result = await session.run(
            user_input="I need to get a quote for home insurance"
        )

        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                MUST: Mention that the office is closed or not available now.
                MUST: Indicate willingness to help or collect information for callback.
                MUST: Be warm and helpful despite being after hours.

                The AfterHoursAgent should deliver its own greeting about being
                closed and offer to help the caller leave a message or get info
                for a callback.

                The response should NOT be completely silent or fail to acknowledge
                the caller's request.

                FAIL if the response doesn't mention office hours or being closed.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_after_hours_voicemail_flow_no_duplicate_greetings() -> None:
    """Verify after-hours flow doesn't have duplicate greetings across agents.

    When caller reaches AfterHoursAgent:
    1. Assistant may have already delivered after-hours greeting
    2. AfterHoursAgent should not repeat the exact same greeting

    This ensures the caller doesn't hear "We're closed" twice.
    """
    after_hours_context = (
        "CURRENT TIME: 8:00 PM ET, Wednesday\n"
        "OFFICE STATUS: Closed (reopens tomorrow at 9 AM)"
    )

    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(
            Assistant(
                business_hours_context=after_hours_context,
                is_after_hours=True,
            )
        )

        # Initial greeting from Assistant (mentions closed)
        # Then make a request that routes to AfterHoursAgent
        await session.run(user_input="I want to make a payment on my policy")

        # Provide info - should not get another "we're closed" message
        result = await session.run(user_input="My name is Jane Doe")

        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                MUST: Continue the conversation by acknowledging input or asking a follow-up.
                SHOULD: Ask for phone number OR insurance type OR other needed info.

                MUST NOT: Say "We're closed" or "the office is closed" again.
                MUST NOT: Repeat the full after-hours greeting that was already delivered.
                MUST NOT: Say "Thanks for calling Harry Levine Insurance" again.

                The caller already knows the office is closed. The response should
                focus on collecting their information efficiently.

                A brief acknowledgment like "Got it" is fine - the key is NOT repeating
                the closed/after-hours messaging.

                FAIL if the response contains closed/after-hours messaging that was
                already conveyed in the previous turn.
                """,
            )
        )
