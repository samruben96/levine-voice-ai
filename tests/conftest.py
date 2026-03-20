"""Shared test fixtures for Harry Levine Insurance Voice Agent tests.

This module provides reusable fixtures and helper functions for testing
the voice agent. It includes:

- Helper functions for skipping expected events in test results
- Environment fixtures for LiveKit configuration
- LLM factory for creating test LLM instances
"""

from __future__ import annotations

import os
import sys
from typing import Any
from unittest.mock import patch

import pytest
from livekit.agents import inference
from livekit.agents import llm as llm_module

# Import from the src directory
sys.path.insert(0, "src")


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

    Example:
        >>> result = await session.run(user_input="Hello")
        >>> skip_function_events(result)
        >>> await result.expect.next_event().is_message(role="assistant")...
    """
    for _ in range(max_calls):
        result.expect.skip_next_event_if(type="function_call")
        result.expect.skip_next_event_if(type="function_call_output")
    if skip_handoff:
        result.expect.skip_next_event_if(type="agent_handoff")


# =============================================================================
# LLM FACTORY
# =============================================================================


def create_test_llm(model: str = "openai/gpt-4.1-mini") -> llm_module.LLM:
    """Create an LLM instance for testing.

    Factory function for creating LLM instances. Centralizes LLM configuration
    for tests, making it easy to switch models or configurations.

    Args:
        model: The model identifier to use. Defaults to the same model
            used in production (gpt-4.1-mini).

    Returns:
        A configured LLM instance.
    """
    return inference.LLM(model=model)


# Alias for backwards compatibility with existing tests
def _llm() -> llm_module.LLM:
    """Create an LLM instance for testing (deprecated alias).

    .. deprecated::
        Use :func:`create_test_llm` instead for clarity.
    """
    return create_test_llm()


# =============================================================================
# ENVIRONMENT FIXTURES
# =============================================================================


@pytest.fixture
def env_with_livekit():
    """Fixture that sets up LiveKit environment variables.

    Yields:
        Dict of environment variables that were set.
    """
    env = {
        "LIVEKIT_URL": "wss://test.livekit.cloud",
        "LIVEKIT_API_KEY": "test-api-key",
        "LIVEKIT_API_SECRET": "test-api-secret",
    }
    with patch.dict(os.environ, env):
        yield env


@pytest.fixture
def env_missing_livekit():
    """Fixture that clears LiveKit environment variables.

    Useful for testing error handling when env vars are missing.

    Yields:
        Empty dict representing cleared environment.
    """
    env_keys = ["LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET"]
    original = {k: os.environ.get(k) for k in env_keys}

    for key in env_keys:
        if key in os.environ:
            del os.environ[key]

    yield {}

    # Restore original values
    for key, value in original.items():
        if value is not None:
            os.environ[key] = value


# =============================================================================
# TEST MARKERS CONFIGURATION
# =============================================================================


def pytest_configure(config):
    """Configure custom pytest markers.

    Registers markers for categorizing tests:
    - unit: Fast tests that don't require LLM
    - integration: Tests that use LLM inference
    - slow: Tests that may take longer to run
    - security: Security-related tests
    - smoke: Critical path smoke tests
    - mortgagee: Mortgagee/bank caller related tests
    """
    config.addinivalue_line("markers", "unit: Fast unit tests (no LLM required)")
    config.addinivalue_line("markers", "integration: Integration tests (uses LLM)")
    config.addinivalue_line("markers", "slow: Slow-running tests")
    config.addinivalue_line("markers", "security: Security-related tests")
    config.addinivalue_line("markers", "smoke: Critical path smoke tests")
    config.addinivalue_line("markers", "mortgagee: Mortgagee and bank caller tests")
