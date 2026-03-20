"""Unit tests for phone number validation and masking functions.

These tests verify the validate_phone, mask_phone, and mask_name functions
work correctly without requiring any external API calls.
"""

import sys

import pytest

sys.path.insert(0, "src")
from agent import mask_name, mask_phone, validate_phone


@pytest.mark.unit
class TestPhoneValidation:
    """Tests for phone number validation."""

    def test_validate_phone_valid_10_digits(self):
        """Test validation with 10 digit phone."""
        is_valid, normalized = validate_phone("555-123-4567")
        assert is_valid is True
        assert normalized == "5551234567"

    def test_validate_phone_valid_with_country_code(self):
        """Test validation with country code."""
        is_valid, normalized = validate_phone("+1 (555) 123-4567")
        assert is_valid is True
        assert normalized == "15551234567"

    def test_validate_phone_valid_with_parentheses(self):
        """Test validation with parentheses format."""
        is_valid, normalized = validate_phone("(555) 123-4567")
        assert is_valid is True
        assert normalized == "5551234567"

    def test_validate_phone_valid_no_formatting(self):
        """Test validation with no formatting."""
        is_valid, normalized = validate_phone("5551234567")
        assert is_valid is True
        assert normalized == "5551234567"

    def test_validate_phone_valid_with_dots(self):
        """Test validation with dot separators."""
        is_valid, normalized = validate_phone("555.123.4567")
        assert is_valid is True
        assert normalized == "5551234567"

    def test_validate_phone_valid_with_spaces(self):
        """Test validation with space separators."""
        is_valid, normalized = validate_phone("555 123 4567")
        assert is_valid is True
        assert normalized == "5551234567"

    def test_validate_phone_too_short(self):
        """Test validation with too few digits."""
        is_valid, _normalized = validate_phone("555-1234")
        assert is_valid is False

    def test_validate_phone_empty(self):
        """Test validation with empty string."""
        is_valid, _normalized = validate_phone("")
        assert is_valid is False

    def test_validate_phone_too_few_digits(self):
        """Test validation with only 5 digits."""
        is_valid, _normalized = validate_phone("12345")
        assert is_valid is False

    def test_validate_phone_with_letters(self):
        """Test validation with letters mixed in."""
        is_valid, _normalized = validate_phone("555-ABC-4567")
        assert is_valid is False

    def test_validate_phone_11_digits_with_1(self):
        """Test validation with 11 digits starting with 1."""
        is_valid, normalized = validate_phone("1-555-123-4567")
        assert is_valid is True
        assert normalized == "15551234567"

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
        is_valid, digits = validate_phone("555-123-4567 x123")
        assert is_valid is True
        assert digits == "5551234567123"

    def test_validate_phone_with_only_special_chars(self):
        """Test validate_phone with string of only special chars."""
        is_valid, result = validate_phone("---().")
        assert is_valid is False
        assert result == "---()."


@pytest.mark.unit
class TestMaskPhone:
    """Tests for phone number masking."""

    def test_mask_phone_normal(self):
        """Test phone masking with normal phone number."""
        assert mask_phone("555-123-4567") == "***-***-4567"

    def test_mask_phone_short(self):
        """Test phone masking with short input."""
        assert mask_phone("123") == "***"

    def test_mask_phone_empty(self):
        """Test phone masking with empty input."""
        assert mask_phone("") == "***"

    def test_mask_phone_none(self):
        """Test phone masking with None input."""
        assert mask_phone(None) == "***"

    def test_mask_phone_only_4_digits(self):
        """Test phone masking with exactly 4 digits."""
        # mask_phone pads even short numbers
        result = mask_phone("1234")
        assert "1234" in result  # Last 4 are preserved

    def test_mask_phone_10_digits_no_formatting(self):
        """Test phone masking with 10 digits no formatting."""
        result = mask_phone("5551234567")
        # Should preserve last 4 and mask rest
        assert result.endswith("4567")
        assert "***" in result

    def test_mask_phone_long_number(self):
        """Test phone masking with long international number."""
        result = mask_phone("+1-555-123-4567")
        # Should mask most of it but show last few
        assert "***" in result

    def test_masks_phone_with_parentheses(self):
        """Test masking a phone number formatted with parentheses."""
        result = mask_phone("(555) 123-4567")
        assert result.endswith("4567")
        assert "***" in result

    def test_masks_phone_with_country_code(self):
        """Test masking an international phone number."""
        result = mask_phone("+1-555-123-4567")
        assert result.endswith("4567")
        assert "***" in result

    def test_preserves_last_four_special_chars(self):
        """Test that last 4 chars are preserved even with special chars."""
        result = mask_phone("555-123-456!")
        assert result.endswith("456!")

    def test_mask_phone_with_none_like_string(self):
        """Test mask_phone doesn't crash on unusual input."""
        result = mask_phone("None")
        assert isinstance(result, str)

    def test_mask_phone_very_long_number(self):
        """Test mask_phone with unusually long input."""
        long_phone = "1" * 100
        result = mask_phone(long_phone)
        assert result == "***-***-1111"
        assert len(result) == 12


@pytest.mark.unit
class TestMaskName:
    """Tests for name masking."""

    def test_mask_name_normal(self):
        """Test name masking with normal name."""
        assert mask_name("John Smith") == "J*********"

    def test_mask_name_short(self):
        """Test name masking with single character."""
        assert mask_name("J") == "J"

    def test_mask_name_empty(self):
        """Test name masking with empty input."""
        assert mask_name("") == "***"

    def test_mask_name_none(self):
        """Test name masking with None input."""
        assert mask_name(None) == "***"

    def test_mask_name_two_characters(self):
        """Test name masking with two characters."""
        result = mask_name("Jo")
        assert result.startswith("J")
        assert "*" in result

    def test_mask_name_long_name(self):
        """Test name masking with long name."""
        result = mask_name("Alexander Hamilton")
        assert result.startswith("A")
        assert "*" in result
        # Should be same length as original
        assert len(result) == len("Alexander Hamilton")

    def test_mask_name_special_characters(self):
        """Test name masking with special characters."""
        result = mask_name("O'Brien-Smith")
        assert result.startswith("O")
        assert "*" in result

    def test_mask_name_with_unicode(self):
        """Test masking name with unicode characters."""
        result = mask_name("Jose")
        assert result[0] == "J"
        assert "*" in result

    def test_mask_name_with_hyphen(self):
        """Test masking hyphenated name."""
        result = mask_name("Smith-Jones")
        assert result == "S**********"
        assert len(result) == 11

    def test_mask_name_with_whitespace_only(self):
        """Test mask_name with whitespace-only string."""
        result = mask_name("   ")
        assert result[0] == " "
        assert len(result) == 3

    def test_mask_name_very_long_name(self):
        """Test mask_name with unusually long input."""
        long_name = "A" + "x" * 99
        result = mask_name(long_name)
        assert result[0] == "A"
        assert len(result) == 100
        assert result.count("*") == 99
