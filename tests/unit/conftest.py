"""Unit test fixtures for Harry Levine Insurance Voice Agent.

This module provides mock fixtures and helpers for unit testing
without requiring external API calls or LLM inference.
"""

import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

# Import from the src directory
sys.path.insert(0, "src")
from agent import CallerInfo, InsuranceType


# =============================================================================
# MOCK LLM FIXTURES
# =============================================================================


@pytest.fixture
def mock_llm():
    """Mock LLM that returns predictable responses."""
    llm_mock = MagicMock()
    llm_mock.__aenter__ = AsyncMock(return_value=llm_mock)
    llm_mock.__aexit__ = AsyncMock()
    return llm_mock


@pytest.fixture
def mock_llm_response():
    """Factory for creating mock LLM responses."""

    def _create_response(content: str):
        response = MagicMock()
        response.content = content
        return response

    return _create_response


# =============================================================================
# MOCK AGENT SESSION FIXTURES
# =============================================================================


@pytest.fixture
def mock_agent_session_full():
    """Full mock AgentSession with tracking capabilities."""
    session = MagicMock()
    session.say = AsyncMock()
    session.run = AsyncMock()
    session.start = AsyncMock()
    session.generate_reply = MagicMock()

    # Track function calls
    session.function_calls = []

    def track_call(name, args):
        session.function_calls.append((name, args))

    session.track_call = track_call
    return session


# =============================================================================
# CALLER INFO FIXTURES FOR UNIT TESTS
# =============================================================================


@pytest.fixture
def empty_caller_info():
    """Empty CallerInfo for testing initialization."""
    return CallerInfo()


@pytest.fixture
def complete_caller_info_personal():
    """Fully populated CallerInfo for personal insurance."""
    return CallerInfo(
        name="John Smith",
        phone_number="5551234567",
        insurance_type=InsuranceType.PERSONAL,
        last_name_spelled="SMITH",
        assigned_agent="Luis",
    )


@pytest.fixture
def complete_caller_info_business():
    """Fully populated CallerInfo for business insurance."""
    return CallerInfo(
        name="Jane Doe",
        phone_number="5559876543",
        insurance_type=InsuranceType.BUSINESS,
        business_name="Acme Corporation",
        assigned_agent="Adriana",
    )


@pytest.fixture
def partial_caller_info_name_only():
    """CallerInfo with only name set."""
    return CallerInfo(name="John Smith")


@pytest.fixture
def partial_caller_info_phone_only():
    """CallerInfo with only phone set."""
    return CallerInfo(phone_number="5551234567")
