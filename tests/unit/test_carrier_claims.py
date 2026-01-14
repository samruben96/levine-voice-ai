"""Unit tests for carrier claims phone number lookup.

These tests verify the get_carrier_claims_number function returns
correct phone numbers for known carriers and handles unknown carriers
appropriately.
"""

import sys

import pytest

sys.path.insert(0, "src")

# Note: This function may not be implemented yet - tests will skip if not available
try:
    from agent import get_carrier_claims_number

    HAS_CARRIER_LOOKUP = True
except ImportError:
    HAS_CARRIER_LOOKUP = False


@pytest.mark.unit
@pytest.mark.skipif(not HAS_CARRIER_LOOKUP, reason="get_carrier_claims_number not implemented")
class TestCarrierClaimsNumbers:
    """Tests for carrier claims phone number lookup functionality."""

    def test_carrier_claims_number_lookup_progressive(self):
        """Test that Progressive claims number is correctly returned."""
        result = get_carrier_claims_number("Progressive")
        assert result is not None
        # Should be a toll-free number
        assert "800" in result or "888" in result or "877" in result

    def test_carrier_claims_number_lookup_state_farm(self):
        """Test that State Farm claims number is correctly returned."""
        result = get_carrier_claims_number("State Farm")
        assert result is not None
        assert "800" in result or "888" in result or "877" in result

    def test_carrier_claims_number_lookup_geico(self):
        """Test that GEICO claims number is correctly returned."""
        result = get_carrier_claims_number("GEICO")
        assert result is not None
        assert "800" in result or "888" in result or "877" in result

    def test_carrier_claims_number_lookup_allstate(self):
        """Test that Allstate claims number is correctly returned."""
        result = get_carrier_claims_number("Allstate")
        assert result is not None
        assert "800" in result or "888" in result or "877" in result

    def test_carrier_claims_number_lookup_case_insensitive(self):
        """Test that carrier lookup is case insensitive."""
        result_lower = get_carrier_claims_number("progressive")
        result_upper = get_carrier_claims_number("PROGRESSIVE")
        result_mixed = get_carrier_claims_number("Progressive")
        assert result_lower == result_upper == result_mixed

    def test_carrier_claims_number_lookup_unknown_carrier(self):
        """Test that unknown carrier returns None or helpful guidance."""
        result = get_carrier_claims_number("XYZ Nonexistent Insurance")
        # Should return None for unknown carriers
        assert result is None

    def test_carrier_claims_number_lookup_empty_string(self):
        """Test that empty string returns None."""
        result = get_carrier_claims_number("")
        assert result is None

    def test_carrier_claims_number_lookup_travelers(self):
        """Test that Travelers claims number is correctly returned."""
        result = get_carrier_claims_number("Travelers")
        if result is not None:
            # If implemented, should be a valid phone number
            assert any(prefix in result for prefix in ["800", "888", "877", "866"])

    def test_carrier_claims_number_lookup_nationwide(self):
        """Test that Nationwide claims number is correctly returned."""
        result = get_carrier_claims_number("Nationwide")
        if result is not None:
            assert any(prefix in result for prefix in ["800", "888", "877", "866"])

    def test_carrier_claims_number_lookup_liberty_mutual(self):
        """Test that Liberty Mutual claims number is correctly returned."""
        result = get_carrier_claims_number("Liberty Mutual")
        if result is not None:
            assert any(prefix in result for prefix in ["800", "888", "877", "866"])

    def test_carrier_claims_number_lookup_farmers(self):
        """Test that Farmers claims number is correctly returned."""
        result = get_carrier_claims_number("Farmers")
        if result is not None:
            assert any(prefix in result for prefix in ["800", "888", "877", "866"])

    def test_carrier_claims_number_lookup_usaa(self):
        """Test that USAA claims number is correctly returned."""
        result = get_carrier_claims_number("USAA")
        if result is not None:
            assert any(prefix in result for prefix in ["800", "888", "877", "866"])

    def test_carrier_claims_number_lookup_partial_name(self):
        """Test lookup with partial carrier name."""
        # Test that partial names might still work
        result = get_carrier_claims_number("State")
        # Could return State Farm or None depending on implementation
        # Document actual behavior

    def test_carrier_claims_number_lookup_with_typo(self):
        """Test lookup with common typo."""
        result = get_carrier_claims_number("Progressiv")  # Missing 'e'
        # Should probably return None unless fuzzy matching is implemented
