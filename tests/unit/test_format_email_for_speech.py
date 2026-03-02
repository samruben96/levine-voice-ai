"""Unit tests for format_email_for_speech utility function."""

import sys

import pytest

sys.path.insert(0, "src")
from utils import format_email_for_speech


@pytest.mark.unit
class TestFormatEmailForSpeech:
    """Tests for format_email_for_speech TTS formatting function."""

    def test_format_standard_email(self):
        """Test formatting a standard email for speech."""
        result = format_email_for_speech("info@example.com")
        assert "at" in result
        assert "dot com" in result
        assert "spell" in result.lower()

    def test_format_hlinsure_special_case(self):
        """Test the hlinsure.com special case produces H-L Insure."""
        result = format_email_for_speech("Certificate@hlinsure.com")
        assert "H-L Insure" in result

    def test_format_empty_string(self):
        """Test empty string returns empty string."""
        result = format_email_for_speech("")
        assert result == ""

    def test_format_no_at_sign(self):
        """Test string without @ returns as-is."""
        result = format_email_for_speech("notanemail")
        assert result == "notanemail"

    def test_format_contains_spelled_version(self):
        """Test that result includes both readable and spelled versions."""
        result = format_email_for_speech("info@hlinsure.com")
        # Should contain spelled out letters
        assert "I-N-F-O" in result

    def test_format_certificate_email(self):
        """Test formatting the certificate email address."""
        result = format_email_for_speech("Certificate@hlinsure.com")
        assert "C-E-R-T-I-F-I-C-A-T-E" in result
