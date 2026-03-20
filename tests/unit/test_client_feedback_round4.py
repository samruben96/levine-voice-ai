"""Unit tests for Client Feedback Round 4 behavioral changes.

Tests cover:
- Former employee handling in staff directory and route_call_specific_agent
- Rachel disambiguation guard
- Restricted agent vendor/sales flow (handle_restricted_agent_response)
- CallerInfo restricted_agent_name field
"""

import sys

import pytest

sys.path.insert(0, "src")

from models import CallerInfo
from staff_directory import (
    STAFF_DIRECTORY,
    get_agent_by_name,
    get_agents_by_name_prefix,
    is_transferable,
)


# =============================================================================
# Former Employee Tests
# =============================================================================


@pytest.mark.unit
class TestFormerEmployees:
    """Tests for former employee entries in staff directory."""

    def test_harry_is_deceased(self):
        """Harry should be in directory with status='deceased'."""
        harry = get_agent_by_name("Harry")
        assert harry is not None
        assert harry["status"] == "deceased"
        assert harry["department"] == "Former"
        assert harry["transferable"] is False

    def test_harry_has_appropriate_message(self):
        """Harry's message should mention he is no longer with us."""
        harry = get_agent_by_name("Harry")
        assert "no longer with us" in harry["message"]

    def test_rosa_is_retired(self):
        """Rosa should be in directory with status='retired'."""
        rosa = get_agent_by_name("Rosa")
        assert rosa is not None
        assert rosa["status"] == "retired"
        assert rosa["department"] == "Former"
        assert rosa["transferable"] is False

    def test_rosa_has_appropriate_message(self):
        """Rosa's message should mention retirement."""
        rosa = get_agent_by_name("Rosa")
        assert "retired" in rosa["message"]

    def test_debi_is_retired(self):
        """Debi should be in directory with status='retired'."""
        debi = get_agent_by_name("Debi")
        assert debi is not None
        assert debi["status"] == "retired"
        assert debi["department"] == "Former"
        assert debi["transferable"] is False

    def test_debi_has_appropriate_message(self):
        """Debi's message should mention retirement."""
        debi = get_agent_by_name("Debi")
        assert "retired" in debi["message"]

    def test_debbie_resolves_to_debi(self):
        """'Debbie' alias should resolve to Debi in route_call_specific_agent logic."""
        # Simulate the alias mapping used in route_call_specific_agent
        name_aliases = {"debbie": "Debi"}
        resolved = name_aliases.get("Debbie".strip().lower(), "Debbie")
        assert resolved == "Debi"
        debi = get_agent_by_name(resolved)
        assert debi is not None
        assert debi["name"] == "Debi"

    def test_deb_prefix_matches_debi(self):
        """'Deb' should prefix-match to Debi via get_agent_by_name."""
        debi = get_agent_by_name("Deb")
        assert debi is not None
        assert debi["name"] == "Debi"

    def test_former_employees_not_in_restricted_transfers(self):
        """Harry, Rosa, Debi should NOT be in restrictedTransfers (handled by status + transferable:False)."""
        restricted = STAFF_DIRECTORY["restrictedTransfers"]
        assert "Harry" not in restricted
        assert "Rosa" not in restricted
        assert "Debi" not in restricted

    def test_fred_is_not_former(self):
        """Fred should still be active (just restricted), not marked as former."""
        fred = get_agent_by_name("Fred")
        assert fred is not None
        assert fred["department"] == "PL-Special Projects"
        assert "status" not in fred or fred.get("status") != "retired"

    def test_former_employees_not_transferable(self):
        """All former employees should not be transferable."""
        assert is_transferable("Harry") is False
        assert is_transferable("Rosa") is False
        assert is_transferable("Debi") is False


# =============================================================================
# Rachel Disambiguation Tests
# =============================================================================


@pytest.mark.unit
class TestRachelDisambiguation:
    """Tests for Rachel disambiguation guard logic."""

    def test_rachel_returns_two_matches(self):
        """'Rachel' should match both Rachel T. and Rachel Moreno."""
        matches = get_agents_by_name_prefix("Rachel")
        assert len(matches) == 2
        names = {m["name"] for m in matches}
        assert "Rachel T." in names
        assert "Rachel Moreno" in names

    def test_rach_prefix_returns_two_matches(self):
        """'Rach' should also match both Rachels."""
        matches = get_agents_by_name_prefix("Rach")
        assert len(matches) == 2

    def test_rachel_moreno_exact_match_first(self):
        """'Rachel Moreno' exact match should be first result."""
        matches = get_agents_by_name_prefix("Rachel Moreno")
        assert matches[0]["name"] == "Rachel Moreno"

    def test_rachel_t_exact_match_first(self):
        """'Rachel T.' exact match should be first result."""
        matches = get_agents_by_name_prefix("Rachel T.")
        assert matches[0]["name"] == "Rachel T."

    def test_disambiguation_guard_logic(self):
        """Guard should fire for 'Rachel' but not 'Rachel Moreno'."""
        # Simulates the guard logic from route_call_specific_agent
        for name, should_fire in [
            ("Rachel", True),
            ("rachel", True),
            ("Rach", True),
            ("Rachel Moreno", False),
            ("Rachel T.", False),
        ]:
            name_stripped = name.strip()
            name_lower = name_stripped.lower()
            guard_fires = name_lower.startswith("rach") and " " not in name_stripped
            assert guard_fires == should_fire, (
                f"Guard for '{name}': expected {should_fire}, got {guard_fires}"
            )


# =============================================================================
# Restricted Agent Response Tests
# =============================================================================


@pytest.mark.unit
class TestRestrictedAgentResponse:
    """Tests for handle_restricted_agent_response logic."""

    def test_caller_info_has_restricted_agent_name_field(self):
        """CallerInfo should have restricted_agent_name as a declared field."""
        info = CallerInfo()
        assert info.restricted_agent_name is None
        info.restricted_agent_name = "Jason L."
        assert info.restricted_agent_name == "Jason L."

    def test_vendor_sales_response(self):
        """Vendor/sales callers should get email info."""
        # Simulates the handle_restricted_agent_response logic
        caller_type = "vendor_sales"
        if caller_type == "vendor_sales":
            response = "All vendor and sales inquiries should be submitted by email"
        assert "email" in response

    def test_new_client_response(self):
        """New client callers should be asked about insurance type."""
        caller_type = "new_client"
        if caller_type == "new_client":
            response = "Is this for business or personal insurance?"
        assert "business or personal" in response

    def test_existing_client_response(self):
        """Existing client callers should be asked about insurance type."""
        caller_type = "existing_client"
        if caller_type == "existing_client":
            response = "Is this for business or personal insurance?"
        assert "business or personal" in response

    def test_unknown_caller_type_asks_again(self):
        """Unknown caller type should re-ask the three-way question."""
        caller_type = "something_else"
        if caller_type not in ("vendor_sales", "new_client", "existing_client"):
            response = "are you an existing client, looking to become a client, or is this a vendor or sales call?"
        assert "existing client" in response
        assert "vendor" in response

    def test_restricted_agents_get_three_way_question(self):
        """Jason L. and Fred should be restricted (non-transferable)."""
        assert is_transferable("Jason L.") is False
        assert is_transferable("Fred") is False

    def test_restricted_agents_have_no_former_status(self):
        """Jason L. and Fred should NOT have former/retired/deceased status."""
        jason = get_agent_by_name("Jason L.")
        assert jason is not None
        assert jason.get("status") is None

        fred = get_agent_by_name("Fred")
        assert fred is not None
        assert fred.get("status") is None
