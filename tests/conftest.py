"""Shared test fixtures for Harry Levine Insurance Voice Agent tests."""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import from the src directory
sys.path.insert(0, "src")
from agent import CallerInfo


def skip_function_events(result, max_calls: int = 10, skip_handoff: bool = True):
    """Skip function call events in test results.

    Args:
        result: The test result object.
        max_calls: Maximum number of function calls to skip.
        skip_handoff: Whether to also skip agent_handoff events.
    """
    for _ in range(max_calls):
        result.expect.skip_next_event_if(type="function_call")
        result.expect.skip_next_event_if(type="function_call_output")
    if skip_handoff:
        result.expect.skip_next_event_if(type="agent_handoff")


@pytest.fixture
def caller_info():
    """Create a fresh CallerInfo instance for testing."""
    return CallerInfo()


@pytest.fixture
def caller_info_with_contact():
    """Create a CallerInfo with contact info populated."""
    return CallerInfo(
        name="John Smith",
        phone_number="555-123-4567",
    )


@pytest.fixture
def caller_info_business():
    """Create a CallerInfo for business insurance."""
    from agent import InsuranceType

    return CallerInfo(
        name="Jane Doe",
        phone_number="555-987-6543",
        insurance_type=InsuranceType.BUSINESS,
        business_name="Acme Corporation",
    )


@pytest.fixture
def caller_info_personal():
    """Create a CallerInfo for personal insurance."""
    from agent import InsuranceType

    return CallerInfo(
        name="Bob Wilson",
        phone_number="555-456-7890",
        insurance_type=InsuranceType.PERSONAL,
        last_name_spelled="Wilson",
    )


@pytest.fixture
def mock_context():
    """Create a mock RunContext for testing function tools."""
    context = MagicMock()
    context.userdata = CallerInfo()
    return context


@pytest.fixture
def mock_agent_session():
    """Create a mock AgentSession for testing."""
    session = MagicMock()
    session.say = AsyncMock()
    session.generate_reply = MagicMock()
    return session


@pytest.fixture
def env_with_livekit():
    """Fixture that sets up LiveKit environment variables."""
    env = {
        "LIVEKIT_URL": "wss://test.livekit.cloud",
        "LIVEKIT_API_KEY": "test-api-key",
        "LIVEKIT_API_SECRET": "test-api-secret",
    }
    with patch.dict(os.environ, env):
        yield env
