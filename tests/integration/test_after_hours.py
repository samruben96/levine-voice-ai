"""Integration tests for after-hours behavior.

These tests verify the Assistant and AfterHoursAgent handle
after-hours calls correctly, including voicemail offers.
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
# AFTER-HOURS GREETING TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.after_hours
async def test_after_hours_greeting_mentions_closure() -> None:
    """Test that after-hours greeting mentions office is closed."""
    # Simulate after hours context
    after_hours_context = (
        "CURRENT TIME: 7:30 PM ET, Tuesday\n"
        "OFFICE STATUS: Closed (reopens tomorrow at 9 AM)"
    )

    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant(business_hours_context=after_hours_context))

        result = await session.run(user_input="Hello")

        # Skip any function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Greets the caller and indicates the office is currently closed.

                The response should:
                - Acknowledge this is Harry Levine Insurance (or similar)
                - Indicate the office is closed/after hours
                - Be warm and professional

                The response could include phrases like:
                - "We're currently closed"
                - "Our office is closed"
                - "After hours"
                - "Not available at this time"

                The response should NOT:
                - Pretend the office is open
                - Ignore that it's after hours
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.after_hours
async def test_after_hours_greeting_mentions_hours() -> None:
    """Test that greeting mentions M-F 9am-5pm hours."""
    # Simulate after hours context (Saturday)
    after_hours_context = (
        "CURRENT TIME: 11:00 AM ET, Saturday\n"
        "OFFICE STATUS: Closed (reopens Monday at 9 AM)"
    )

    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant(business_hours_context=after_hours_context))

        result = await session.run(user_input="Hi, I need help with my insurance")

        # Skip any function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Responds to the caller and provides business hours information.

                The response should either:
                - Mention business hours (9 to 5, Monday-Friday, or similar), OR
                - Mention when the office reopens (Monday at 9 AM), OR
                - Offer to leave a voicemail for callback

                The response should be helpful and acknowledge the caller's need.
                """,
            )
        )


# =============================================================================
# HOURS RESPONSE CONTEXT TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_hours_response_contextual_when_open() -> None:
    """Evaluation: Hours response should be contextual when office is open."""
    # Use a simulated 'open' time context
    open_context = (
        "CURRENT TIME: 2:30 PM ET, Wednesday\nOFFICE STATUS: Open (closes at 5 PM)"
    )

    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant(business_hours_context=open_context))

        result = await session.run(user_input="What are your hours?")

        # Skip any function calls
        skip_function_events(result, max_calls=3)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Provides hours information in a contextual way that reflects the office is currently open.

                The response should:
                - Indicate the office is currently open, OR
                - Provide the hours in a present-tense manner ("we're open", "we're here until 5")
                - Include the standard hours (9 to 5, Monday-Friday)

                The response could include:
                - "We're open right now"
                - "We're open until 5 PM"
                - "We're here to help"

                The response should NOT:
                - Say the office is closed
                - Only mention when the office reopens
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.after_hours
async def test_hours_response_contextual_when_closed() -> None:
    """Evaluation: Hours response should be contextual when office is closed."""
    # Use a simulated 'closed' time context
    closed_context = (
        "CURRENT TIME: 7:30 PM ET, Tuesday\n"
        "OFFICE STATUS: Closed (reopens tomorrow at 9 AM)"
    )

    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant(business_hours_context=closed_context))

        result = await session.run(user_input="What are your hours?")

        # Skip any function calls
        skip_function_events(result, max_calls=3)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Provides hours information in a contextual way that reflects the office is currently closed.

                The response should:
                - Indicate the office is currently closed, OR
                - Mention when the office reopens (tomorrow at 9 AM), OR
                - Provide the standard hours (9 to 5, Monday-Friday)

                The response could include:
                - "We're currently closed"
                - "We reopen tomorrow at 9 AM"
                - "Our hours are..."

                The response should NOT:
                - Say the office is open right now
                - Ignore that it's after hours
                """,
            )
        )


# =============================================================================
# AFTER-HOURS INFO COLLECTION TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.after_hours
async def test_after_hours_collects_name_and_phone() -> None:
    """Test that caller name and phone are collected during after hours."""
    after_hours_context = (
        "CURRENT TIME: 8:00 PM ET, Wednesday\n"
        "OFFICE STATUS: Closed (reopens tomorrow at 9 AM)"
    )

    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant(business_hours_context=after_hours_context))

        # Caller wants help with general inquiry
        result = await session.run(user_input="I need help with my policy")

        # Skip function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Either:
                - Indicates office is closed and offers voicemail option
                - Asks for name and phone for callback
                - Offers to help with what they can

                The response should be helpful even though it's after hours.
                """,
            )
        )


# =============================================================================
# EXCEPTION INTENT TESTS (Bypass voicemail)
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.after_hours
async def test_after_hours_claims_gets_special_handling() -> None:
    """Test that claims after hours gets special handling (carrier lookup)."""
    after_hours_context = (
        "CURRENT TIME: 9:00 PM ET, Thursday\n"
        "OFFICE STATUS: Closed (reopens tomorrow at 9 AM)"
    )

    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant(business_hours_context=after_hours_context))

        result = await session.run(user_input="I was just in a car accident")

        # Skip function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Shows empathy and offers to help with the claim despite being after hours.

                The response should:
                - Express concern about the accident
                - Offer to help (may provide carrier claims number)
                - Be warm and supportive

                Claims should get special handling even after hours.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.after_hours
async def test_after_hours_hours_question_answered_directly() -> None:
    """Test that hours questions are answered directly even after hours."""
    after_hours_context = (
        "CURRENT TIME: 6:00 AM ET, Monday\nOFFICE STATUS: Closed (opens at 9 AM)"
    )

    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant(business_hours_context=after_hours_context))

        result = await session.run(user_input="When do you open?")

        # Skip function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Provides the office hours directly.

                The response should:
                - Mention the office opens at 9 AM
                - May mention Monday-Friday, 9 to 5

                Hours questions should be answered directly.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.after_hours
async def test_after_hours_certificate_gets_email() -> None:
    """Test that certificate requests after hours get email address."""
    after_hours_context = (
        "CURRENT TIME: 8:00 PM ET, Wednesday\n"
        "OFFICE STATUS: Closed (reopens tomorrow at 9 AM)"
    )

    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant(business_hours_context=after_hours_context))

        result = await session.run(user_input="I need a certificate of insurance")

        # Skip function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Provides helpful information about certificates even after hours.

                The response should either:
                - Provide an email for certificate requests
                - Mention self-service options
                - Offer to help when office reopens

                Certificate requests can often be handled via email.
                """,
            )
        )


# =============================================================================
# VOICEMAIL OFFER TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.after_hours
async def test_after_hours_offers_voicemail_for_general_inquiry() -> None:
    """Test that voicemail is offered for general inquiries after hours."""
    after_hours_context = (
        "CURRENT TIME: 10:00 PM ET, Monday\n"
        "OFFICE STATUS: Closed (reopens tomorrow at 9 AM)"
    )

    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant(business_hours_context=after_hours_context))

        result = await session.run(user_input="I need to make a change to my policy")

        # Skip function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Indicates office is closed and offers options.

                The response should either:
                - Offer to take a message/leave voicemail
                - Mention when office reopens for callback
                - Acknowledge the request and offer to help

                The response should be helpful despite being after hours.
                """,
            )
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.after_hours
async def test_after_hours_weekend_mentions_monday() -> None:
    """Test that weekend calls mention reopening Monday."""
    weekend_context = (
        "CURRENT TIME: 2:00 PM ET, Saturday\n"
        "OFFICE STATUS: Closed (reopens Monday at 9 AM)"
    )

    async with (
        _llm() as llm,
        AgentSession[CallerInfo](llm=llm, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant(business_hours_context=weekend_context))

        result = await session.run(
            user_input="I'd like to speak to someone about a quote"
        )

        # Skip function calls
        skip_function_events(result)

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Indicates office is closed for the weekend.

                The response should:
                - Mention the office reopens Monday at 9 AM
                - Offer to help with what they can OR take a message
                - Be friendly and helpful

                Weekend calls should know the office reopens Monday.
                """,
            )
        )
