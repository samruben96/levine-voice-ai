"""Unit tests for the log_route_decision() utility function.

These tests verify the structured route decision logging works correctly,
including enum handling, PII masking, and edge cases.
"""

import logging
import sys

import pytest

sys.path.insert(0, "src")
from models import CallIntent, InsuranceType
from utils import log_route_decision


# =============================================================================
# ENUM INPUT TESTS
# =============================================================================


@pytest.mark.unit
class TestLogRouteDecisionEnumInputs:
    """Tests for log_route_decision with enum inputs."""

    def test_log_route_decision_with_call_intent_enum(self, caplog):
        """Test that CallIntent enum values are properly converted to strings."""
        with caplog.at_level(logging.INFO, logger="agent"):
            log_route_decision(
                intent=CallIntent.NEW_QUOTE,
                agent="Rachel Moreno",
                insurance_type=InsuranceType.PERSONAL,
                identifier="Smith",
                destination="transfer",
                is_personal=True,
            )

        assert len(caplog.records) == 1
        log_message = caplog.records[0].message
        assert "intent=new_quote" in log_message
        assert "ROUTE_DECISION:" in log_message

    def test_log_route_decision_with_insurance_type_enum(self, caplog):
        """Test that InsuranceType enum values are properly converted to strings."""
        with caplog.at_level(logging.INFO, logger="agent"):
            log_route_decision(
                intent=CallIntent.MAKE_PAYMENT,
                agent="Luis Ramirez",
                insurance_type=InsuranceType.BUSINESS,
                identifier="Acme Corporation",
                destination="ring_group:VA",
                is_personal=False,
            )

        assert len(caplog.records) == 1
        log_message = caplog.records[0].message
        assert "insurance_type=business" in log_message

    def test_log_route_decision_with_all_enums(self, caplog):
        """Test complete log message with all enum types."""
        with caplog.at_level(logging.INFO, logger="agent"):
            log_route_decision(
                intent=CallIntent.CLAIMS,
                agent="Sheree",
                insurance_type=InsuranceType.PERSONAL,
                identifier="Johnson",
                destination="handoff:ClaimsAgent",
                is_personal=True,
            )

        log_message = caplog.records[0].message
        assert "intent=claims" in log_message
        assert "insurance_type=personal" in log_message
        assert "agent=Sheree" in log_message
        assert "destination=handoff:ClaimsAgent" in log_message


# =============================================================================
# STRING INPUT TESTS
# =============================================================================


@pytest.mark.unit
class TestLogRouteDecisionStringInputs:
    """Tests for log_route_decision with string inputs."""

    def test_log_route_decision_with_string_intent(self, caplog):
        """Test that string intent values are passed through correctly."""
        with caplog.at_level(logging.INFO, logger="agent"):
            log_route_decision(
                intent="custom_intent",
                agent="Adriana",
                insurance_type=InsuranceType.BUSINESS,
                identifier="Widget Co",
                destination="transfer",
                is_personal=False,
            )

        assert len(caplog.records) == 1
        log_message = caplog.records[0].message
        assert "intent=custom_intent" in log_message

    def test_log_route_decision_with_string_intent_preserves_case(self, caplog):
        """Test that string intent case is preserved."""
        with caplog.at_level(logging.INFO, logger="agent"):
            log_route_decision(
                intent="UPPERCASE_INTENT",
                agent="Test Agent",
                insurance_type=None,
                identifier="Test",
                destination="test",
            )

        log_message = caplog.records[0].message
        assert "intent=UPPERCASE_INTENT" in log_message


# =============================================================================
# NONE HANDLING TESTS
# =============================================================================


@pytest.mark.unit
class TestLogRouteDecisionNoneHandling:
    """Tests for log_route_decision with None values."""

    def test_log_route_decision_with_all_none_values(self, caplog):
        """Test that None values are handled gracefully."""
        with caplog.at_level(logging.INFO, logger="agent"):
            log_route_decision(
                intent=None,
                agent=None,
                insurance_type=None,
                identifier=None,
                destination="unknown",
            )

        assert len(caplog.records) == 1
        log_message = caplog.records[0].message
        assert "intent=None" in log_message
        assert "agent=None" in log_message
        assert "insurance_type=None" in log_message
        assert "identifier=None" in log_message
        assert "destination=unknown" in log_message

    def test_log_route_decision_with_none_identifier(self, caplog):
        """Test that None identifier is logged as 'None' string."""
        with caplog.at_level(logging.INFO, logger="agent"):
            log_route_decision(
                intent=CallIntent.SOMETHING_ELSE,
                agent="Front Desk",
                insurance_type=InsuranceType.PERSONAL,
                identifier=None,
                destination="voicemail",
                is_personal=True,
            )

        log_message = caplog.records[0].message
        assert "identifier=None" in log_message

    def test_log_route_decision_with_none_agent(self, caplog):
        """Test that None agent is logged as 'None' string."""
        with caplog.at_level(logging.INFO, logger="agent"):
            log_route_decision(
                intent=CallIntent.MAKE_PAYMENT,
                agent=None,
                insurance_type=InsuranceType.PERSONAL,
                identifier="Test",
                destination="ring_group:VA",
                is_personal=True,
            )

        log_message = caplog.records[0].message
        assert "agent=None" in log_message


# =============================================================================
# PII MASKING TESTS
# =============================================================================


@pytest.mark.unit
class TestLogRouteDecisionPIIMasking:
    """Tests for PII masking in log_route_decision."""

    def test_log_route_decision_masks_personal_identifier(self, caplog):
        """Test that personal identifiers (last names) are masked."""
        with caplog.at_level(logging.INFO, logger="agent"):
            log_route_decision(
                intent=CallIntent.NEW_QUOTE,
                agent="Rachel Moreno",
                insurance_type=InsuranceType.PERSONAL,
                identifier="Johnson",
                destination="transfer",
                is_personal=True,
            )

        log_message = caplog.records[0].message
        # "Johnson" should be masked to "J******"
        assert "identifier=J******" in log_message
        assert "Johnson" not in log_message

    def test_log_route_decision_does_not_mask_business_identifier(self, caplog):
        """Test that business names are NOT masked."""
        with caplog.at_level(logging.INFO, logger="agent"):
            log_route_decision(
                intent=CallIntent.NEW_QUOTE,
                agent="Adriana Blanco",
                insurance_type=InsuranceType.BUSINESS,
                identifier="Acme Corporation",
                destination="transfer",
                is_personal=False,
            )

        log_message = caplog.records[0].message
        # Business name should appear unmasked
        assert "identifier=Acme Corporation" in log_message

    def test_log_route_decision_masks_short_name(self, caplog):
        """Test that short names (e.g., 'Li') are properly masked."""
        with caplog.at_level(logging.INFO, logger="agent"):
            log_route_decision(
                intent=CallIntent.MAKE_CHANGE,
                agent="Luis Ramirez",
                insurance_type=InsuranceType.PERSONAL,
                identifier="Li",
                destination="transfer",
                is_personal=True,
            )

        log_message = caplog.records[0].message
        # "Li" should be masked to "L*"
        assert "identifier=L*" in log_message
        assert "identifier=Li" not in log_message

    def test_log_route_decision_masks_long_name(self, caplog):
        """Test that long names are properly masked."""
        with caplog.at_level(logging.INFO, logger="agent"):
            log_route_decision(
                intent=CallIntent.POLICY_REVIEW_RENEWAL,
                agent="Sheree",
                insurance_type=InsuranceType.PERSONAL,
                identifier="Williamson-Rodriguez",
                destination="transfer",
                is_personal=True,
            )

        log_message = caplog.records[0].message
        # "Williamson-Rodriguez" (20 chars) should be masked to "W*******************"
        assert "identifier=W*******************" in log_message
        assert "Williamson-Rodriguez" not in log_message

    def test_log_route_decision_default_is_personal_false(self, caplog):
        """Test that is_personal defaults to False (no masking)."""
        with caplog.at_level(logging.INFO, logger="agent"):
            log_route_decision(
                intent=CallIntent.COVERAGE_RATE_QUESTIONS,
                agent="Test Agent",
                insurance_type=InsuranceType.PERSONAL,
                identifier="TestName",
                destination="transfer",
                # is_personal not specified, defaults to False
            )

        log_message = caplog.records[0].message
        # Without is_personal=True, identifier should NOT be masked
        assert "identifier=TestName" in log_message


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


@pytest.mark.unit
class TestLogRouteDecisionEdgeCases:
    """Tests for edge cases in log_route_decision."""

    def test_log_route_decision_with_empty_string_identifier(self, caplog):
        """Test that empty string identifier is handled (falsy, becomes 'None')."""
        with caplog.at_level(logging.INFO, logger="agent"):
            log_route_decision(
                intent=CallIntent.HOURS_LOCATION,
                agent=None,
                insurance_type=None,
                identifier="",
                destination="direct_answer",
                is_personal=False,
            )

        log_message = caplog.records[0].message
        # Empty string is falsy, so should be logged as "None"
        assert "identifier=None" in log_message

    def test_log_route_decision_with_single_char_identifier(self, caplog):
        """Test that single character identifiers are handled correctly."""
        with caplog.at_level(logging.INFO, logger="agent"):
            log_route_decision(
                intent=CallIntent.CANCELLATION,
                agent="Ann",
                insurance_type=InsuranceType.PERSONAL,
                identifier="X",
                destination="transfer",
                is_personal=True,
            )

        log_message = caplog.records[0].message
        # Single char "X" masked should be just "X" (first char + 0 asterisks)
        assert "identifier=X" in log_message

    def test_log_route_decision_with_whitespace_identifier(self, caplog):
        """Test that whitespace-only identifier is not masked as business."""
        with caplog.at_level(logging.INFO, logger="agent"):
            log_route_decision(
                intent=CallIntent.SOMETHING_ELSE,
                agent="Test",
                insurance_type=InsuranceType.BUSINESS,
                identifier="   ",
                destination="transfer",
                is_personal=False,
            )

        log_message = caplog.records[0].message
        # Whitespace is truthy, so it should be passed through
        assert "identifier=   " in log_message

    def test_log_route_decision_with_special_characters_in_identifier(self, caplog):
        """Test identifiers with special characters."""
        with caplog.at_level(logging.INFO, logger="agent"):
            log_route_decision(
                intent=CallIntent.CERTIFICATES,
                agent="Adriana",
                insurance_type=InsuranceType.BUSINESS,
                identifier="O'Brien & Sons, LLC",
                destination="handoff:MortgageeCertificateAgent",
                is_personal=False,
            )

        log_message = caplog.records[0].message
        assert "identifier=O'Brien & Sons, LLC" in log_message

    def test_log_route_decision_log_level_is_info(self, caplog):
        """Test that route decisions are logged at INFO level."""
        with caplog.at_level(logging.DEBUG, logger="agent"):
            log_route_decision(
                intent=CallIntent.BANK_CALLER,
                agent=None,
                insurance_type=None,
                identifier=None,
                destination="direct_handling",
            )

        assert len(caplog.records) == 1
        assert caplog.records[0].levelno == logging.INFO

    def test_log_route_decision_format_structure(self, caplog):
        """Test the overall structure of the log message."""
        with caplog.at_level(logging.INFO, logger="agent"):
            log_route_decision(
                intent=CallIntent.SPECIFIC_AGENT,
                agent="Fred",
                insurance_type=InsuranceType.PERSONAL,
                identifier="Test",
                destination="restricted_transfer",
                is_personal=True,
            )

        log_message = caplog.records[0].message
        # Verify the overall format with pipe separators
        assert log_message.startswith("ROUTE_DECISION:")
        assert " | " in log_message
        # Count separators (should be 4 separators for 5 fields)
        assert log_message.count(" | ") == 4
