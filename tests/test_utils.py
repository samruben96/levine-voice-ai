"""Unit tests for utility functions.

This module contains fast unit tests for the utility functions in src/utils.py.
These tests do NOT require LLM inference and run quickly, making them ideal
for CI pipelines and rapid development feedback.

Test Categories:
- mask_phone: PII masking for phone numbers
- mask_name: PII masking for names
- validate_phone: Phone number validation and normalization
- validate_environment: Environment variable validation
- CallerInfo: Data validation methods on the CallerInfo dataclass

All tests in this module are marked with @pytest.mark.unit.

Usage:
    # Run only utility tests
    pytest tests/test_utils.py -v

    # Run only unit tests (fast, no LLM)
    pytest -m unit -v
"""

from __future__ import annotations

import os
import sys
from unittest.mock import patch

import pytest

# Import from the src directory
sys.path.insert(0, "src")

from agent import (
    CallerInfo,
    InsuranceType,
    mask_name,
    mask_phone,
    validate_environment,
    validate_phone,
)

# =============================================================================
# MASK PHONE TESTS
# =============================================================================


@pytest.mark.unit
class TestMaskPhone:
    """Tests for the mask_phone utility function.

    mask_phone is used for logging phone numbers without exposing full PII.
    It should show only the last 4 digits.
    """

    def test_masks_standard_phone_number(self):
        """Test masking a standard 10-digit US phone number."""
        result = mask_phone("555-123-4567")
        assert result == "***-***-4567"

    def test_masks_phone_with_parentheses(self):
        """Test masking a phone number formatted with parentheses."""
        result = mask_phone("(555) 123-4567")
        # Still shows last 4 digits regardless of formatting
        assert result.endswith("4567")
        assert "***" in result

    def test_masks_phone_with_country_code(self):
        """Test masking an international phone number."""
        result = mask_phone("+1-555-123-4567")
        assert result.endswith("4567")
        assert "***" in result

    def test_masks_phone_digits_only(self):
        """Test masking a phone number with only digits."""
        result = mask_phone("5551234567")
        assert result == "***-***-4567"

    def test_short_phone_returns_masked(self):
        """Test that short strings (< 4 chars) return generic mask."""
        result = mask_phone("123")
        assert result == "***"

    def test_empty_phone_returns_masked(self):
        """Test that empty string returns generic mask."""
        result = mask_phone("")
        assert result == "***"

    def test_exactly_four_digits(self):
        """Test phone with exactly 4 digits shows all 4."""
        result = mask_phone("1234")
        assert result == "***-***-1234"

    def test_five_digits(self):
        """Test phone with 5 digits shows last 4."""
        result = mask_phone("12345")
        assert result == "***-***-2345"

    def test_preserves_last_four_special_chars(self):
        """Test that last 4 chars are preserved even with special chars."""
        result = mask_phone("555-123-456!")
        # Last 4 chars are "456!"
        assert result.endswith("456!")

    def test_long_international_number(self):
        """Test masking a long international number."""
        result = mask_phone("+44 20 7946 0958")
        assert result.endswith("0958")
        assert "***" in result


# =============================================================================
# MASK NAME TESTS
# =============================================================================


@pytest.mark.unit
class TestMaskName:
    """Tests for the mask_name utility function.

    mask_name is used for logging names without exposing full PII.
    It should show only the first character followed by asterisks.
    """

    def test_masks_simple_name(self):
        """Test masking a simple first name."""
        result = mask_name("John")
        assert result == "J***"

    def test_masks_full_name(self):
        """Test masking a full name with space."""
        result = mask_name("John Smith")
        assert result == "J*********"
        assert len(result) == len("John Smith")

    def test_masks_single_character(self):
        """Test masking a single character name."""
        result = mask_name("J")
        assert result == "J"

    def test_empty_name_returns_masked(self):
        """Test that empty string returns generic mask."""
        result = mask_name("")
        assert result == "***"

    def test_preserves_first_character(self):
        """Test that first character is always preserved."""
        assert mask_name("Alice")[0] == "A"
        assert mask_name("Bob")[0] == "B"
        assert mask_name("Charlie")[0] == "C"

    def test_length_preserved(self):
        """Test that masked string has same length as original."""
        original = "Jennifer Williams"
        result = mask_name(original)
        assert len(result) == len(original)

    def test_name_with_special_chars(self):
        """Test masking name with special characters."""
        result = mask_name("O'Brien")
        assert result == "O******"
        assert len(result) == 7

    def test_name_with_hyphen(self):
        """Test masking hyphenated name."""
        result = mask_name("Smith-Jones")
        assert result == "S**********"
        assert len(result) == 11

    def test_unicode_name(self):
        """Test masking name with unicode characters."""
        result = mask_name("Jose")
        assert result[0] == "J"
        assert "*" in result


# =============================================================================
# VALIDATE PHONE TESTS
# =============================================================================


@pytest.mark.unit
class TestValidatePhone:
    """Tests for the validate_phone utility function.

    validate_phone validates phone numbers and returns normalized digits.
    It accepts phones with 10-15 digits (supporting US and international).
    """

    def test_valid_us_phone_with_dashes(self):
        """Test valid US phone with dashes is normalized."""
        is_valid, digits = validate_phone("555-123-4567")
        assert is_valid is True
        assert digits == "5551234567"

    def test_valid_us_phone_with_parentheses(self):
        """Test valid US phone with parentheses is normalized."""
        is_valid, digits = validate_phone("(555) 123-4567")
        assert is_valid is True
        assert digits == "5551234567"

    def test_valid_phone_with_country_code(self):
        """Test valid phone with +1 country code."""
        is_valid, digits = validate_phone("+1 (555) 123-4567")
        assert is_valid is True
        assert digits == "15551234567"

    def test_valid_phone_digits_only(self):
        """Test valid phone with only digits."""
        is_valid, digits = validate_phone("5551234567")
        assert is_valid is True
        assert digits == "5551234567"

    def test_valid_international_phone(self):
        """Test valid international phone number."""
        is_valid, digits = validate_phone("+44 20 7946 0958")
        assert is_valid is True
        assert digits == "442079460958"

    def test_invalid_too_short(self):
        """Test phone with fewer than 10 digits is invalid."""
        is_valid, original = validate_phone("555-1234")
        assert is_valid is False
        assert original == "555-1234"  # Returns original on failure

    def test_invalid_too_few_digits(self):
        """Test phone with 9 digits is invalid."""
        is_valid, original = validate_phone("555123456")
        assert is_valid is False
        assert original == "555123456"

    def test_invalid_empty(self):
        """Test empty string is invalid."""
        is_valid, result = validate_phone("")
        assert is_valid is False
        assert result == ""

    def test_invalid_too_long(self):
        """Test phone with more than 15 digits is invalid."""
        is_valid, original = validate_phone("1234567890123456")  # 16 digits
        assert is_valid is False
        assert original == "1234567890123456"

    def test_valid_exactly_10_digits(self):
        """Test boundary: exactly 10 digits is valid."""
        is_valid, digits = validate_phone("1234567890")
        assert is_valid is True
        assert digits == "1234567890"

    def test_valid_exactly_15_digits(self):
        """Test boundary: exactly 15 digits is valid."""
        is_valid, digits = validate_phone("123456789012345")
        assert is_valid is True
        assert digits == "123456789012345"

    def test_strips_all_non_digits(self):
        """Test that all non-digit characters are stripped."""
        is_valid, digits = validate_phone("1.2.3.4.5.6.7.8.9.0")
        assert is_valid is True
        assert digits == "1234567890"

    def test_phone_with_extension_marker(self):
        """Test phone with 'x' extension marker."""
        # The 'x' is stripped as non-digit
        is_valid, digits = validate_phone("555-123-4567 x123")
        assert is_valid is True
        assert digits == "5551234567123"

    def test_phone_with_letters(self):
        """Test phone with letters (vanity number)."""
        # Letters are stripped
        is_valid, _digits = validate_phone("1-800-FLOWERS")
        assert is_valid is False  # Only 4 digits: 1800


# =============================================================================
# VALIDATE ENVIRONMENT TESTS
# =============================================================================


@pytest.mark.unit
class TestValidateEnvironment:
    """Tests for the validate_environment utility function.

    validate_environment checks that required LiveKit environment variables
    are set and raises RuntimeError if any are missing.
    """

    def test_passes_with_all_vars_set(self, env_with_livekit):
        """Test that validation passes when all vars are set."""
        # env_with_livekit fixture sets all required vars
        # Should not raise
        validate_environment()

    def test_fails_with_missing_url(self, env_with_livekit):
        """Test that validation fails when URL is missing."""
        with patch.dict(os.environ, {"LIVEKIT_URL": ""}, clear=False):
            # Clear the URL
            del os.environ["LIVEKIT_URL"]
            with pytest.raises(RuntimeError) as exc_info:
                validate_environment()
            assert "LIVEKIT_URL" in str(exc_info.value)

    def test_fails_with_missing_api_key(self, env_with_livekit):
        """Test that validation fails when API key is missing."""
        del os.environ["LIVEKIT_API_KEY"]
        with pytest.raises(RuntimeError) as exc_info:
            validate_environment()
        assert "LIVEKIT_API_KEY" in str(exc_info.value)

    def test_fails_with_missing_api_secret(self, env_with_livekit):
        """Test that validation fails when API secret is missing."""
        del os.environ["LIVEKIT_API_SECRET"]
        with pytest.raises(RuntimeError) as exc_info:
            validate_environment()
        assert "LIVEKIT_API_SECRET" in str(exc_info.value)

    def test_fails_with_all_missing(self, env_missing_livekit):
        """Test that validation fails listing all missing vars."""
        with pytest.raises(RuntimeError) as exc_info:
            validate_environment()
        error_message = str(exc_info.value)
        assert "LIVEKIT_URL" in error_message
        assert "LIVEKIT_API_KEY" in error_message
        assert "LIVEKIT_API_SECRET" in error_message

    def test_error_message_contains_missing_list(self, env_missing_livekit):
        """Test that error message lists all missing variables."""
        with pytest.raises(RuntimeError) as exc_info:
            validate_environment()
        # Should contain a list-like representation
        assert "[" in str(exc_info.value) or "missing" in str(exc_info.value).lower()


# =============================================================================
# CALLER INFO VALIDATION TESTS
# =============================================================================


@pytest.mark.unit
class TestCallerInfoValidation:
    """Tests for CallerInfo validation methods.

    These tests verify the is_ready_for_routing() and has_insurance_identifier()
    methods work correctly across different data states.
    """

    def test_is_ready_for_routing_with_both_fields(self):
        """Test routing readiness with name and phone set."""
        caller = CallerInfo(name="John Smith", phone_number="555-123-4567")
        assert caller.is_ready_for_routing() is True

    def test_is_ready_for_routing_missing_name(self):
        """Test routing readiness with missing name."""
        caller = CallerInfo(phone_number="555-123-4567")
        assert caller.is_ready_for_routing() is False

    def test_is_ready_for_routing_missing_phone(self):
        """Test routing readiness with missing phone."""
        caller = CallerInfo(name="John Smith")
        assert caller.is_ready_for_routing() is False

    def test_is_ready_for_routing_empty(self):
        """Test routing readiness with empty CallerInfo."""
        caller = CallerInfo()
        assert caller.is_ready_for_routing() is False

    def test_is_ready_for_routing_empty_strings(self):
        """Test routing readiness with empty string values."""
        caller = CallerInfo(name="", phone_number="")
        assert caller.is_ready_for_routing() is False

    def test_has_insurance_identifier_with_business_name(self):
        """Test identifier presence with business name."""
        caller = CallerInfo(business_name="Acme Corp")
        assert caller.has_insurance_identifier() is True

    def test_has_insurance_identifier_with_last_name(self):
        """Test identifier presence with spelled last name."""
        caller = CallerInfo(last_name_spelled="Smith")
        assert caller.has_insurance_identifier() is True

    def test_has_insurance_identifier_with_both(self):
        """Test identifier presence with both set."""
        caller = CallerInfo(business_name="Acme Corp", last_name_spelled="Smith")
        assert caller.has_insurance_identifier() is True

    def test_has_insurance_identifier_empty(self):
        """Test identifier presence with no identifiers."""
        caller = CallerInfo()
        assert caller.has_insurance_identifier() is False

    def test_has_insurance_identifier_empty_strings(self):
        """Test identifier presence with empty string values."""
        caller = CallerInfo(business_name="", last_name_spelled="")
        assert caller.has_insurance_identifier() is False

    def test_caller_info_defaults(self):
        """Test CallerInfo default values."""
        caller = CallerInfo()
        assert caller.name is None
        assert caller.phone_number is None
        assert caller.insurance_type is None
        assert caller.business_name is None
        assert caller.last_name_spelled is None
        assert caller.call_intent is None
        assert caller.specific_agent_name is None
        assert caller.additional_notes == ""
        assert caller.assigned_agent is None

    def test_caller_info_business_type(self):
        """Test CallerInfo with business insurance type."""
        caller = CallerInfo(
            name="Jane Doe",
            phone_number="555-987-6543",
            insurance_type=InsuranceType.BUSINESS,
            business_name="Acme Corporation",
        )
        assert caller.insurance_type == InsuranceType.BUSINESS
        assert caller.business_name == "Acme Corporation"
        assert caller.has_insurance_identifier() is True
        assert caller.is_ready_for_routing() is True

    def test_caller_info_personal_type(self):
        """Test CallerInfo with personal insurance type."""
        caller = CallerInfo(
            name="Bob Wilson",
            phone_number="555-456-7890",
            insurance_type=InsuranceType.PERSONAL,
            last_name_spelled="Wilson",
        )
        assert caller.insurance_type == InsuranceType.PERSONAL
        assert caller.last_name_spelled == "Wilson"
        assert caller.has_insurance_identifier() is True
        assert caller.is_ready_for_routing() is True


# =============================================================================
# INSURANCE TYPE ENUM TESTS
# =============================================================================


@pytest.mark.unit
class TestInsuranceType:
    """Tests for the InsuranceType enum."""

    def test_business_value(self):
        """Test business insurance type value."""
        assert InsuranceType.BUSINESS.value == "business"

    def test_personal_value(self):
        """Test personal insurance type value."""
        assert InsuranceType.PERSONAL.value == "personal"

    def test_enum_members(self):
        """Test that only expected members exist."""
        members = list(InsuranceType)
        assert len(members) == 2
        assert InsuranceType.BUSINESS in members
        assert InsuranceType.PERSONAL in members

    def test_string_comparison(self):
        """Test that InsuranceType can be compared with strings."""
        # InsuranceType inherits from str
        assert InsuranceType.BUSINESS == "business"
        assert InsuranceType.PERSONAL == "personal"

    def test_construction_from_string(self):
        """Test constructing InsuranceType from string value."""
        business = InsuranceType("business")
        personal = InsuranceType("personal")
        assert business == InsuranceType.BUSINESS
        assert personal == InsuranceType.PERSONAL


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


@pytest.mark.unit
class TestEdgeCases:
    """Edge case tests for utility functions."""

    def test_mask_phone_with_none_like_string(self):
        """Test mask_phone doesn't crash on unusual input."""
        # None would raise TypeError, but "None" string should work
        result = mask_phone("None")
        assert isinstance(result, str)

    def test_mask_name_with_whitespace_only(self):
        """Test mask_name with whitespace-only string."""
        result = mask_name("   ")
        # First char is space, rest masked
        assert result[0] == " "
        assert len(result) == 3

    def test_validate_phone_with_only_special_chars(self):
        """Test validate_phone with string of only special chars."""
        is_valid, result = validate_phone("---().")
        assert is_valid is False
        assert result == "---()."

    def test_caller_info_with_all_fields(self):
        """Test CallerInfo with all fields populated."""
        from agent import CallIntent

        caller = CallerInfo(
            name="Test User",
            phone_number="555-000-1234",
            insurance_type=InsuranceType.BUSINESS,
            business_name="Test Corp",
            last_name_spelled="User",
            call_intent=CallIntent.NEW_QUOTE,
            specific_agent_name="Adriana",
            additional_notes="Test notes",
            assigned_agent="Adriana",
        )
        assert caller.is_ready_for_routing() is True
        assert caller.has_insurance_identifier() is True

    def test_mask_phone_very_long_number(self):
        """Test mask_phone with unusually long input."""
        long_phone = "1" * 100
        result = mask_phone(long_phone)
        assert result == "***-***-1111"
        assert len(result) == 12

    def test_mask_name_very_long_name(self):
        """Test mask_name with unusually long input."""
        long_name = "A" + "x" * 99
        result = mask_name(long_name)
        assert result[0] == "A"
        assert len(result) == 100
        assert result.count("*") == 99
