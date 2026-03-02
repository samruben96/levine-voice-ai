"""Unit tests for mask_email utility function."""

import sys

import pytest

sys.path.insert(0, "src")
from utils import mask_email


@pytest.mark.unit
class TestMaskEmail:
    """Tests for mask_email PII masking function."""

    def test_mask_email_normal(self):
        """Test masking a normal email address."""
        assert mask_email("john.smith@example.com") == "j***@example.com"

    def test_mask_email_none(self):
        """Test masking None returns masked placeholder."""
        assert mask_email(None) == "***"

    def test_mask_email_empty(self):
        """Test masking empty string returns masked placeholder."""
        assert mask_email("") == "***"

    def test_mask_email_no_at_sign(self):
        """Test masking string without @ returns masked placeholder."""
        assert mask_email("notanemail") == "***"

    def test_mask_email_empty_local_part(self):
        """Test masking email with empty local part."""
        assert mask_email("@example.com") == "***@example.com"

    def test_mask_email_single_char_local(self):
        """Test masking email with single character local part."""
        assert mask_email("a@example.com") == "a***@example.com"
