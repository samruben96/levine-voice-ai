"""Unit tests for CallerInfo dataclass validation.

These tests verify the CallerInfo state validation methods work correctly
without requiring any external API calls.
"""

import sys

import pytest

sys.path.insert(0, "src")
from agent import CallerInfo, InsuranceType


@pytest.mark.unit
class TestCallerInfoValidation:
    """Tests for CallerInfo state validation."""

    def test_is_ready_for_routing_complete(self):
        """Test routing readiness with complete info."""
        caller = CallerInfo(name="John", phone_number="555-1234")
        assert caller.is_ready_for_routing() is True

    def test_is_ready_for_routing_missing_name(self):
        """Test routing readiness without name."""
        caller = CallerInfo(phone_number="555-1234")
        assert caller.is_ready_for_routing() is False

    def test_is_ready_for_routing_missing_phone(self):
        """Test routing readiness without phone."""
        caller = CallerInfo(name="John")
        assert caller.is_ready_for_routing() is False

    def test_is_ready_for_routing_empty(self):
        """Test routing readiness with empty CallerInfo."""
        caller = CallerInfo()
        assert caller.is_ready_for_routing() is False

    def test_has_insurance_identifier_business(self):
        """Test identifier check with business name."""
        caller = CallerInfo(business_name="Acme Corp")
        assert caller.has_insurance_identifier() is True

    def test_has_insurance_identifier_personal(self):
        """Test identifier check with last name."""
        caller = CallerInfo(last_name_spelled="Smith")
        assert caller.has_insurance_identifier() is True

    def test_has_insurance_identifier_none(self):
        """Test identifier check without any identifier."""
        caller = CallerInfo()
        assert caller.has_insurance_identifier() is False

    def test_has_insurance_identifier_both(self):
        """Test identifier check with both business name and last name."""
        caller = CallerInfo(
            business_name="Acme Corp",
            last_name_spelled="Smith",
        )
        assert caller.has_insurance_identifier() is True


@pytest.mark.unit
class TestCallerInfoInsuranceType:
    """Tests for CallerInfo insurance type handling."""

    def test_insurance_type_default_none(self):
        """Test that insurance type defaults to None."""
        caller = CallerInfo()
        assert caller.insurance_type is None

    def test_insurance_type_set_business(self):
        """Test setting business insurance type."""
        caller = CallerInfo()
        caller.insurance_type = InsuranceType.BUSINESS
        assert caller.insurance_type == InsuranceType.BUSINESS

    def test_insurance_type_set_personal(self):
        """Test setting personal insurance type."""
        caller = CallerInfo()
        caller.insurance_type = InsuranceType.PERSONAL
        assert caller.insurance_type == InsuranceType.PERSONAL

    def test_insurance_type_via_constructor(self):
        """Test setting insurance type via constructor."""
        caller_business = CallerInfo(insurance_type=InsuranceType.BUSINESS)
        caller_personal = CallerInfo(insurance_type=InsuranceType.PERSONAL)
        assert caller_business.insurance_type == InsuranceType.BUSINESS
        assert caller_personal.insurance_type == InsuranceType.PERSONAL


@pytest.mark.unit
class TestCallerInfoAssignedAgent:
    """Tests for CallerInfo assigned agent handling."""

    def test_assigned_agent_default_none(self):
        """Test that assigned agent defaults to None."""
        caller = CallerInfo()
        assert caller.assigned_agent is None

    def test_assigned_agent_set(self):
        """Test setting assigned agent."""
        caller = CallerInfo()
        caller.assigned_agent = "Adriana"
        assert caller.assigned_agent == "Adriana"

    def test_assigned_agent_via_constructor(self):
        """Test setting assigned agent via constructor."""
        caller = CallerInfo(assigned_agent="Luis")
        assert caller.assigned_agent == "Luis"


@pytest.mark.unit
class TestCallerInfoAdditionalNotes:
    """Tests for CallerInfo additional notes handling."""

    def test_additional_notes_default_empty(self):
        """Test that additional notes defaults to empty string."""
        caller = CallerInfo()
        assert caller.additional_notes == ""

    def test_additional_notes_set(self):
        """Test setting additional notes."""
        caller = CallerInfo()
        caller.additional_notes = "Customer wants to discuss pricing"
        assert caller.additional_notes == "Customer wants to discuss pricing"

    def test_additional_notes_via_constructor(self):
        """Test setting additional notes via constructor."""
        caller = CallerInfo(additional_notes="Urgent callback requested")
        assert caller.additional_notes == "Urgent callback requested"
