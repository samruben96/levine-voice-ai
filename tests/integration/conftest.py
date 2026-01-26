"""Integration test fixtures for Harry Levine Insurance Voice Agent.

This module provides fixtures specific to integration tests that use
real LLM inference. These tests are slower but verify actual agent behavior.
"""

import sys
from typing import Any

import pytest
from livekit.agents import AgentSession, inference
from livekit.agents import llm as llm_module

# Import from the src directory
sys.path.insert(0, "src")
from agent import Assistant, CallerInfo

# =============================================================================
# EVENT SKIPPING HELPERS
# =============================================================================


def skip_function_events(
    result: Any,
    max_calls: int = 10,
    skip_handoff: bool = True,
) -> None:
    """Skip function call and handoff events in test results.

    This helper is essential for voice agent testing where function calls
    may occur before the assistant's response. Call this before checking
    for message events.

    Args:
        result: The test result object from session.run().
        max_calls: Maximum number of function call pairs to skip. Each function
            call consists of a function_call event followed by function_call_output.
        skip_handoff: Whether to also skip agent_handoff events after function calls.
    """
    for _ in range(max_calls):
        result.expect.skip_next_event_if(type="function_call")
        result.expect.skip_next_event_if(type="function_call_output")
    if skip_handoff:
        result.expect.skip_next_event_if(type="agent_handoff")


# =============================================================================
# LLM FIXTURES
# =============================================================================


def create_integration_llm(model: str = "openai/gpt-4.1-mini") -> llm_module.LLM:
    """Create an LLM instance for integration tests."""
    return inference.LLM(model=model)


def _llm(model: str = "openai/gpt-4.1-mini") -> llm_module.LLM:
    """Create an LLM instance for integration tests.

    This is the standard helper used across integration tests for creating
    LLM instances that can be used as async context managers.

    Args:
        model: The model identifier to use. Defaults to gpt-4.1-mini.

    Returns:
        An LLM instance that can be used with `async with _llm() as llm`.
    """
    return inference.LLM(model=model)


# =============================================================================
# BUSINESS HOURS CONTEXT STRINGS
# =============================================================================

CONTEXT_OPEN = (
    "CURRENT TIME: 2:30 PM ET, Wednesday\nOFFICE STATUS: Open (closes at 5 PM)"
)

CONTEXT_CLOSED_EVENING = (
    "CURRENT TIME: 7:30 PM ET, Tuesday\n"
    "OFFICE STATUS: Closed (reopens tomorrow at 9 AM)"
)

CONTEXT_CLOSED_WEEKEND = (
    "CURRENT TIME: 11:00 AM ET, Saturday\n"
    "OFFICE STATUS: Closed (reopens Monday at 9 AM)"
)

CONTEXT_CLOSED_EARLY_MORNING = (
    "CURRENT TIME: 7:00 AM ET, Thursday\nOFFICE STATUS: Closed (opens at 9 AM)"
)


# =============================================================================
# SESSION FIXTURES WITH SPECIFIC CONTEXTS
# =============================================================================


@pytest.fixture
async def session_during_business_hours():
    """Session with Assistant configured for during business hours.

    Yields:
        Tuple of (session, llm) for testing business hours behavior.
    """
    llm = create_integration_llm()
    async with (
        llm as llm_ctx,
        AgentSession[CallerInfo](llm=llm_ctx, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant(business_hours_context=CONTEXT_OPEN))
        yield session, llm_ctx


@pytest.fixture
async def session_after_hours_evening():
    """Session with Assistant configured for evening after hours.

    Yields:
        Tuple of (session, llm) for testing after-hours behavior.
    """
    llm = create_integration_llm()
    async with (
        llm as llm_ctx,
        AgentSession[CallerInfo](llm=llm_ctx, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant(business_hours_context=CONTEXT_CLOSED_EVENING))
        yield session, llm_ctx


@pytest.fixture
async def session_after_hours_weekend():
    """Session with Assistant configured for weekend.

    Yields:
        Tuple of (session, llm) for testing weekend behavior.
    """
    llm = create_integration_llm()
    async with (
        llm as llm_ctx,
        AgentSession[CallerInfo](llm=llm_ctx, userdata=CallerInfo()) as session,
    ):
        await session.start(Assistant(business_hours_context=CONTEXT_CLOSED_WEEKEND))
        yield session, llm_ctx


@pytest.fixture
async def session_early_morning():
    """Session with Assistant configured for early morning (before open).

    Yields:
        Tuple of (session, llm) for testing early morning behavior.
    """
    llm = create_integration_llm()
    async with (
        llm as llm_ctx,
        AgentSession[CallerInfo](llm=llm_ctx, userdata=CallerInfo()) as session,
    ):
        await session.start(
            Assistant(business_hours_context=CONTEXT_CLOSED_EARLY_MORNING)
        )
        yield session, llm_ctx
