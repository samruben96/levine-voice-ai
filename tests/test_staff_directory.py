"""Tests for staff directory configuration and routing logic.

These tests verify the alpha-split routing, exception prefix handling,
and staff lookup functions work correctly for call transfer decisions.
"""

from datetime import datetime
from unittest.mock import patch

from staff_directory import (
    STAFF_DIRECTORY,
    find_agent_by_alpha,
    get_agent_by_extension,
    get_agent_by_name,
    get_agents_by_department,
    get_alpha_route_key,
    get_available_agent_by_alpha,
    get_ring_group,
    is_agent_available,
    is_transferable,
)


class TestStaffDirectoryConfig:
    """Tests for the STAFF_DIRECTORY configuration structure."""

    def test_staff_directory_has_required_keys(self) -> None:
        """Verify the configuration has all required top-level keys."""
        assert "staff" in STAFF_DIRECTORY
        assert "restrictedTransfers" in STAFF_DIRECTORY
        assert "alphaExceptionPrefixes" in STAFF_DIRECTORY

    def test_staff_list_not_empty(self) -> None:
        """Verify there are staff members in the directory."""
        assert len(STAFF_DIRECTORY["staff"]) > 0

    def test_all_staff_have_required_fields(self) -> None:
        """Verify each staff member has the minimum required fields."""
        for staff in STAFF_DIRECTORY["staff"]:
            assert "department" in staff
            assert "name" in staff
            assert "assigned" in staff
            assert "ext" in staff

    def test_restricted_transfers_list(self) -> None:
        """Verify the restricted transfers list contains expected names."""
        restricted = STAFF_DIRECTORY["restrictedTransfers"]
        assert "Jason L." in restricted
        assert "Fred" in restricted

    def test_alpha_exception_prefixes(self) -> None:
        """Verify the alpha exception prefixes are configured."""
        prefixes = STAFF_DIRECTORY["alphaExceptionPrefixes"]
        assert "The" in prefixes
        assert "Law office of" in prefixes
        assert "Law offices of" in prefixes

    def test_ring_groups_configured(self) -> None:
        """Verify ring groups are configured in the directory."""
        assert "ringGroups" in STAFF_DIRECTORY
        ring_groups = STAFF_DIRECTORY["ringGroups"]
        assert "VA" in ring_groups

    def test_va_ring_group_structure(self) -> None:
        """Verify the VA ring group has correct structure."""
        va_group = STAFF_DIRECTORY["ringGroups"]["VA"]
        assert "name" in va_group
        assert "extensions" in va_group
        assert "description" in va_group
        assert va_group["name"] == "Virtual Assistant Team"
        assert "7016" in va_group["extensions"]  # Ann
        assert "7008" in va_group["extensions"]  # Sheree


class TestGetAlphaRouteKey:
    """Tests for the get_alpha_route_key function."""

    def test_simple_business_name(self) -> None:
        """Test routing for a simple business name."""
        assert get_alpha_route_key("Acme Corporation") == "A"
        assert get_alpha_route_key("Zephyr Industries") == "Z"
        assert get_alpha_route_key("Mountain View LLC") == "M"

    def test_the_prefix_exception(self) -> None:
        """Test 'The' prefix is skipped for routing."""
        assert get_alpha_route_key("The Great Company") == "G"
        assert get_alpha_route_key("The Acme Corp") == "A"
        assert get_alpha_route_key("The Zoo Keeper") == "Z"

    def test_the_prefix_case_insensitive(self) -> None:
        """Test 'The' prefix works case-insensitively."""
        assert get_alpha_route_key("the Great Company") == "G"
        assert get_alpha_route_key("THE ACME CORP") == "A"
        assert get_alpha_route_key("ThE ZoO KeEpEr") == "Z"

    def test_law_office_of_prefix_exception(self) -> None:
        """Test 'Law office of' prefix is skipped for routing."""
        assert get_alpha_route_key("Law office of Smith & Associates") == "S"
        assert get_alpha_route_key("Law office of Harry Levine") == "H"
        assert get_alpha_route_key("Law office of Brown Legal") == "B"

    def test_law_offices_of_prefix_exception(self) -> None:
        """Test 'Law offices of' prefix is skipped for routing."""
        assert get_alpha_route_key("Law offices of Smith & Associates") == "S"
        assert get_alpha_route_key("Law Offices of Harry Levine") == "H"
        assert get_alpha_route_key("LAW OFFICES OF WILSON") == "W"

    def test_law_prefix_case_insensitive(self) -> None:
        """Test law prefixes work case-insensitively."""
        assert get_alpha_route_key("law office of Smith") == "S"
        assert get_alpha_route_key("LAW OFFICE OF JONES") == "J"
        assert get_alpha_route_key("law offices of Brown") == "B"

    def test_empty_business_name(self) -> None:
        """Test handling of empty or whitespace-only names."""
        assert get_alpha_route_key("") == "A"
        assert get_alpha_route_key("   ") == "A"

    def test_single_word_after_prefix(self) -> None:
        """Test when only one word follows the prefix."""
        assert get_alpha_route_key("The Company") == "C"
        assert get_alpha_route_key("Law office of Smith") == "S"

    def test_no_word_after_prefix(self) -> None:
        """Test graceful handling when nothing follows a prefix."""
        # Should fall back to first letter
        assert get_alpha_route_key("The") == "T"
        assert get_alpha_route_key("Law office of") == "L"

    def test_numbers_and_special_characters(self) -> None:
        """Test business names starting with numbers or special chars."""
        assert get_alpha_route_key("123 Industries") == "1"
        assert get_alpha_route_key("@Home Services") == "@"

    def test_lowercase_business_name(self) -> None:
        """Test that routing key is always uppercase."""
        assert get_alpha_route_key("acme corporation") == "A"
        assert get_alpha_route_key("zephyr industries") == "Z"


class TestFindAgentByAlpha:
    """Tests for the find_agent_by_alpha function."""

    # Personal Lines - New Business (Sales Agents)
    def test_pl_new_business_a_to_l(self) -> None:
        """Test PL new business routes to Queens for A-L."""
        for letter in "ABCDEFGHIJKL":
            agent = find_agent_by_alpha(letter, "PL", is_new_business=True)
            assert agent is not None, f"No agent found for letter {letter}"
            assert agent["name"] == "Queens"
            assert agent["department"] == "PL-Sales Agent"

    def test_pl_new_business_m_to_z(self) -> None:
        """Test PL new business routes to Brad for M-Z."""
        for letter in "MNOPQRSTUVWXYZ":
            agent = find_agent_by_alpha(letter, "PL", is_new_business=True)
            assert agent is not None, f"No agent found for letter {letter}"
            assert agent["name"] == "Brad"
            assert agent["department"] == "PL-Sales Agent"

    # Personal Lines - Existing Clients (Account Executives)
    def test_pl_existing_a_to_g(self) -> None:
        """Test PL existing clients route to Yarislyn for A-G."""
        for letter in "ABCDEFG":
            agent = find_agent_by_alpha(letter, "PL", is_new_business=False)
            assert agent is not None, f"No agent found for letter {letter}"
            assert agent["name"] == "Yarislyn"
            assert agent["department"] == "PL-Account Executive"

    def test_pl_existing_h_to_m(self) -> None:
        """Test PL existing clients route to Al for H-M."""
        for letter in "HIJKLM":
            agent = find_agent_by_alpha(letter, "PL", is_new_business=False)
            assert agent is not None, f"No agent found for letter {letter}"
            assert agent["name"] == "Al"
            assert agent["department"] == "PL-Account Executive"

    def test_pl_existing_n_to_z(self) -> None:
        """Test PL existing clients route to Luis for N-Z."""
        for letter in "NOPQRSTUVWXYZ":
            agent = find_agent_by_alpha(letter, "PL", is_new_business=False)
            assert agent is not None, f"No agent found for letter {letter}"
            assert agent["name"] == "Luis"
            assert agent["department"] == "PL-Account Executive"

    # Commercial Lines (Account Executives handle both)
    def test_cl_a_to_f(self) -> None:
        """Test CL routes to Adriana for A-F."""
        for letter in "ABCDEF":
            # Test new business
            agent = find_agent_by_alpha(letter, "CL", is_new_business=True)
            assert agent is not None, f"No agent found for letter {letter}"
            assert agent["name"] == "Adriana"
            assert agent["department"] == "CL-Account Executive"

            # Test existing - should be same for CL
            agent = find_agent_by_alpha(letter, "CL", is_new_business=False)
            assert agent is not None
            assert agent["name"] == "Adriana"

    def test_cl_g_to_o(self) -> None:
        """Test CL routes to Rayvon for G-O."""
        for letter in "GHIJKLMNO":
            agent = find_agent_by_alpha(letter, "CL", is_new_business=True)
            assert agent is not None, f"No agent found for letter {letter}"
            assert agent["name"] == "Rayvon"
            assert agent["department"] == "CL-Account Executive"

    def test_cl_p_to_z(self) -> None:
        """Test CL routes to Dionna for P-Z."""
        for letter in "PQRSTUVWXYZ":
            agent = find_agent_by_alpha(letter, "CL", is_new_business=True)
            assert agent is not None, f"No agent found for letter {letter}"
            assert agent["name"] == "Dionna"
            assert agent["department"] == "CL-Account Executive"

    def test_lowercase_letter_input(self) -> None:
        """Test that lowercase letters work correctly."""
        agent = find_agent_by_alpha("a", "CL", is_new_business=True)
        assert agent is not None
        assert agent["name"] == "Adriana"

        agent = find_agent_by_alpha("z", "PL", is_new_business=True)
        assert agent is not None
        assert agent["name"] == "Brad"

    def test_lowercase_department_input(self) -> None:
        """Test that lowercase department codes work."""
        agent = find_agent_by_alpha("A", "cl", is_new_business=True)
        assert agent is not None
        assert agent["name"] == "Adriana"

        agent = find_agent_by_alpha("A", "pl", is_new_business=True)
        assert agent is not None
        assert agent["name"] == "Queens"

    def test_invalid_department(self) -> None:
        """Test that invalid department returns None."""
        assert find_agent_by_alpha("A", "XX", is_new_business=True) is None
        assert find_agent_by_alpha("A", "", is_new_business=True) is None


class TestIsTransferable:
    """Tests for the is_transferable function."""

    def test_jason_not_transferable(self) -> None:
        """Test that Jason L. cannot receive direct AI transfers."""
        assert is_transferable("Jason L.") is False

    def test_fred_not_transferable(self) -> None:
        """Test that Fred cannot receive direct AI transfers."""
        assert is_transferable("Fred") is False

    def test_regular_agents_transferable(self) -> None:
        """Test that regular agents can receive transfers."""
        assert is_transferable("Adriana") is True
        assert is_transferable("Rayvon") is True
        assert is_transferable("Dionna") is True
        assert is_transferable("Queens") is True
        assert is_transferable("Brad") is True

    def test_julie_explicitly_transferable(self) -> None:
        """Test Julie L. who has explicit transferable=True."""
        assert is_transferable("Julie L.") is True

    def test_unknown_agent_defaults_to_transferable(self) -> None:
        """Test that unknown agents default to transferable."""
        assert is_transferable("Unknown Person") is True

    def test_management_transferability(self) -> None:
        """Test management team transfer status."""
        assert is_transferable("Julie L.") is True  # Explicitly True
        assert is_transferable("Jason L.") is False  # Explicitly False
        assert is_transferable("Kelly U.") is True  # No explicit setting, defaults True


class TestGetAgentByName:
    """Tests for the get_agent_by_name function."""

    def test_exact_match(self) -> None:
        """Test exact name matching."""
        agent = get_agent_by_name("Adriana")
        assert agent is not None
        assert agent["name"] == "Adriana"
        assert agent["ext"] == "7002"

    def test_partial_match_first_name(self) -> None:
        """Test partial matching with first name."""
        agent = get_agent_by_name("Rachel")
        assert agent is not None
        assert agent["name"] == "Rachel T."
        assert agent["department"] == "CL-Department Manager"

    def test_partial_match_last_initial(self) -> None:
        """Test matching with last initial included."""
        agent = get_agent_by_name("Jason L")
        assert agent is not None
        assert agent["name"] == "Jason L."

    def test_case_insensitive(self) -> None:
        """Test case-insensitive matching."""
        agent = get_agent_by_name("ADRIANA")
        assert agent is not None
        assert agent["name"] == "Adriana"

        agent = get_agent_by_name("queens")
        assert agent is not None
        assert agent["name"] == "Queens"

    def test_no_match(self) -> None:
        """Test when no agent matches."""
        assert get_agent_by_name("Nonexistent") is None
        assert get_agent_by_name("XYZ") is None

    def test_empty_name(self) -> None:
        """Test empty name input."""
        assert get_agent_by_name("") is None
        assert get_agent_by_name(None) is None  # type: ignore[arg-type]

    def test_whitespace_handling(self) -> None:
        """Test that whitespace is handled correctly."""
        agent = get_agent_by_name("  Adriana  ")
        assert agent is not None
        assert agent["name"] == "Adriana"


class TestGetAgentByExtension:
    """Tests for the get_agent_by_extension function."""

    def test_valid_extension(self) -> None:
        """Test lookup by valid extension."""
        agent = get_agent_by_extension("7002")
        assert agent is not None
        assert agent["name"] == "Adriana"

        agent = get_agent_by_extension("7000")
        assert agent is not None
        assert agent["name"] == "Jason L."

    def test_all_extensions_unique(self) -> None:
        """Verify all extensions in directory return unique agents."""
        extensions = [staff["ext"] for staff in STAFF_DIRECTORY["staff"]]
        for ext in extensions:
            agent = get_agent_by_extension(ext)
            assert agent is not None
            assert agent["ext"] == ext

    def test_invalid_extension(self) -> None:
        """Test lookup with non-existent extension."""
        assert get_agent_by_extension("9999") is None
        assert get_agent_by_extension("0000") is None

    def test_empty_extension(self) -> None:
        """Test empty extension input."""
        assert get_agent_by_extension("") is None
        assert get_agent_by_extension(None) is None  # type: ignore[arg-type]

    def test_whitespace_handling(self) -> None:
        """Test that whitespace is stripped from extension."""
        agent = get_agent_by_extension("  7002  ")
        assert agent is not None
        assert agent["name"] == "Adriana"


class TestGetRingGroup:
    """Tests for the get_ring_group function."""

    def test_get_va_ring_group(self) -> None:
        """Test getting the VA ring group."""
        group = get_ring_group("VA")
        assert group is not None
        assert group["name"] == "Virtual Assistant Team"
        assert group["extensions"] == ["7016", "7008"]
        assert group["description"] == "Payment and ID/Dec requests"

    def test_ring_group_not_found(self) -> None:
        """Test getting a non-existent ring group."""
        assert get_ring_group("NONEXISTENT") is None

    def test_ring_group_empty_name(self) -> None:
        """Test getting ring group with empty name."""
        assert get_ring_group("") is None

    def test_ring_group_none_name(self) -> None:
        """Test getting ring group with None name."""
        assert get_ring_group(None) is None  # type: ignore[arg-type]


class TestGetAgentsByDepartment:
    """Tests for the get_agents_by_department function."""

    def test_cl_account_executives(self) -> None:
        """Test getting all CL Account Executives."""
        agents = get_agents_by_department("CL-Account Executive")
        assert len(agents) == 3
        names = {agent["name"] for agent in agents}
        assert names == {"Adriana", "Rayvon", "Dionna"}

    def test_pl_sales_agents(self) -> None:
        """Test getting all PL Sales Agents."""
        agents = get_agents_by_department("PL-Sales Agent")
        assert len(agents) == 2
        names = {agent["name"] for agent in agents}
        assert names == {"Queens", "Brad"}

    def test_management(self) -> None:
        """Test getting all Management staff."""
        agents = get_agents_by_department("Management")
        assert len(agents) == 3
        names = {agent["name"] for agent in agents}
        assert names == {"Julie L.", "Jason L.", "Kelly U."}

    def test_partial_department_match(self) -> None:
        """Test partial department name matching."""
        agents = get_agents_by_department("PL-")
        # Should match PL-Account Executive, PL-Sales Agent, PL-Service, PL-Special Projects
        assert len(agents) >= 6

    def test_case_insensitive(self) -> None:
        """Test case-insensitive department matching."""
        agents = get_agents_by_department("management")
        assert len(agents) == 3

    def test_empty_department(self) -> None:
        """Test empty department input."""
        agents = get_agents_by_department("")
        assert agents == []


class TestIntegrationScenarios:
    """Integration tests for realistic routing scenarios."""

    def test_new_personal_lines_quote_flow(self) -> None:
        """Test the complete flow for a new personal lines quote."""
        # Caller with last name "Smith"
        letter = "S"

        # New business -> goes to Sales Agent
        agent = find_agent_by_alpha(letter, "PL", is_new_business=True)
        assert agent is not None
        assert agent["name"] == "Brad"  # M-Z range
        assert is_transferable(agent["name"]) is True

    def test_existing_personal_lines_client_flow(self) -> None:
        """Test the flow for an existing personal lines client."""
        # Existing client with last name "Anderson"
        letter = "A"

        # Existing client -> goes to Account Executive
        agent = find_agent_by_alpha(letter, "PL", is_new_business=False)
        assert agent is not None
        assert agent["name"] == "Yarislyn"  # A-G range
        assert is_transferable(agent["name"]) is True

    def test_commercial_lines_with_the_prefix(self) -> None:
        """Test CL routing with 'The' prefix exception."""
        # Business name: "The Great Plumbing Co"
        letter = get_alpha_route_key("The Great Plumbing Co")
        assert letter == "G"

        agent = find_agent_by_alpha(letter, "CL", is_new_business=True)
        assert agent is not None
        assert agent["name"] == "Rayvon"  # G-O range

    def test_law_office_routing(self) -> None:
        """Test routing for law office with prefix exception."""
        # Business name: "Law Offices of Harry Levine"
        letter = get_alpha_route_key("Law Offices of Harry Levine")
        assert letter == "H"

        agent = find_agent_by_alpha(letter, "CL", is_new_business=True)
        assert agent is not None
        assert agent["name"] == "Rayvon"  # G-O range (H is in this range)

    def test_transfer_to_specific_agent_by_name(self) -> None:
        """Test looking up a specific agent by name for transfer."""
        # Caller asks for "Rachel"
        agent = get_agent_by_name("Rachel")
        assert agent is not None
        assert agent["name"] == "Rachel T."
        assert agent["ext"] == "7005"
        assert is_transferable(agent["name"]) is True

    def test_transfer_to_restricted_agent(self) -> None:
        """Test that restricted agents are flagged correctly."""
        # Caller asks for "Jason"
        agent = get_agent_by_name("Jason")
        assert agent is not None
        assert agent["name"] == "Jason L."
        assert is_transferable(agent["name"]) is False  # Cannot transfer directly

    def test_extension_lookup_for_transfer(self) -> None:
        """Test looking up agent by extension for transfer."""
        # Caller provides extension 7018
        agent = get_agent_by_extension("7018")
        assert agent is not None
        assert agent["name"] == "Rayvon"
        assert is_transferable(agent["name"]) is True


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


class TestEdgeCases:
    """Edge case tests for staff directory functions."""

    def test_get_alpha_route_key_numeric_business_name(self) -> None:
        """Test routing for business names starting with numbers."""
        # Numbers should return the digit as the key
        result = get_alpha_route_key("123 Corp")
        assert result == "1"

    def test_get_alpha_route_key_special_characters(self) -> None:
        """Test routing for business names with special characters."""
        # Should handle special characters gracefully
        result = get_alpha_route_key("@Twitter Inc")
        assert result == "@"

    def test_get_alpha_route_key_very_long_name(self) -> None:
        """Test routing for very long business names."""
        name = "The " + "A" * 1000 + " Corporation"
        result = get_alpha_route_key(name)
        assert result == "A"  # Should skip "The" prefix

    def test_get_alpha_route_key_unicode_name(self) -> None:
        """Test routing for business names with unicode characters."""
        result = get_alpha_route_key("Cafe du Monde")
        assert result == "C"

    def test_get_alpha_route_key_only_whitespace(self) -> None:
        """Test routing for whitespace-only input."""
        result = get_alpha_route_key("   ")
        assert result == "A"  # Default fallback

    def test_get_agent_by_name_case_insensitive(self) -> None:
        """Test that agent lookup is case-insensitive."""
        agent1 = get_agent_by_name("ADRIANA")
        agent2 = get_agent_by_name("adriana")
        agent3 = get_agent_by_name("Adriana")
        assert agent1 is not None
        assert agent1 == agent2 == agent3

    def test_empty_string_handling(self) -> None:
        """Test that empty strings are handled gracefully."""
        assert get_alpha_route_key("") == "A"
        assert get_agent_by_name("") is None
        assert get_agent_by_extension("") is None
        # Empty letter should not crash
        result = find_agent_by_alpha("", "PL", is_new_business=True)
        # May return None or handle gracefully
        assert result is None or isinstance(result, dict)

    def test_multiple_the_prefixes(self) -> None:
        """Test routing with 'The The' prefix."""
        result = get_alpha_route_key("The The Company")
        assert result == "T"  # Only first "The" is stripped

    def test_law_office_with_special_chars(self) -> None:
        """Test law office prefix with special characters."""
        result = get_alpha_route_key("Law office of Smith & Associates, LLC")
        assert result == "S"

    def test_lowercase_the_prefix(self) -> None:
        """Test lowercase 'the' prefix is handled correctly."""
        result = get_alpha_route_key("the quick brown fox")
        assert result == "Q"

    def test_single_letter_business_name(self) -> None:
        """Test business name that is just a single letter."""
        result = get_alpha_route_key("Z")
        assert result == "Z"

    def test_whitespace_around_name(self) -> None:
        """Test that extra whitespace is trimmed correctly."""
        result = get_alpha_route_key("  Zebra Corp  ")
        assert result == "Z"

    def test_find_agent_by_alpha_empty_department(self) -> None:
        """Test find_agent_by_alpha with empty department."""
        result = find_agent_by_alpha("A", "", is_new_business=True)
        assert result is None

    def test_find_agent_by_alpha_none_like_values(self) -> None:
        """Test find_agent_by_alpha with unusual inputs."""
        # Empty letter should be handled
        result = find_agent_by_alpha("", "PL", is_new_business=True)
        assert result is None or isinstance(result, dict)

    def test_is_transferable_partial_name_match(self) -> None:
        """Test is_transferable with partial name that doesn't match restricted."""
        # "Jason" alone should not match "Jason L." in restricted list
        # But get_agent_by_name will find Jason L.
        # is_transferable should check exact match on restricted list
        assert is_transferable("Jason") is True  # Not in restricted list directly
        assert is_transferable("Jason L.") is False  # In restricted list

    def test_get_agents_by_department_nonexistent(self) -> None:
        """Test getting agents from a nonexistent department."""
        agents = get_agents_by_department("Nonexistent Department")
        assert agents == []

    def test_get_ring_group_case_sensitivity(self) -> None:
        """Test that ring group lookup is case-sensitive."""
        # VA should work
        group = get_ring_group("VA")
        assert group is not None
        # va should not work (case-sensitive)
        group_lower = get_ring_group("va")
        assert group_lower is None


class TestTimeBlockAvailability:
    """Tests for time block availability checking."""

    def test_no_time_block_always_available(self) -> None:
        """Agent without time block should always be available."""
        agent = {"name": "Test", "ext": "1234", "timeBlock": None}
        assert is_agent_available(agent) is True

    def test_empty_time_block_always_available(self) -> None:
        """Agent with empty time block should always be available."""
        agent = {"name": "Test", "ext": "1234"}
        assert is_agent_available(agent) is True

    @patch("staff_directory.datetime")
    def test_agent_unavailable_during_time_block(self, mock_datetime) -> None:
        """Agent should be unavailable during their time block."""
        # Mock current time to 9:30 AM
        mock_now = datetime(2024, 1, 15, 9, 30, 0)
        mock_datetime.now.return_value = mock_now

        agent = {"name": "Test", "ext": "1234", "timeBlock": "9:00-10:00"}
        assert is_agent_available(agent) is False

    @patch("staff_directory.datetime")
    def test_agent_available_outside_time_block(self, mock_datetime) -> None:
        """Agent should be available outside their time block."""
        # Mock current time to 11:00 AM
        mock_now = datetime(2024, 1, 15, 11, 0, 0)
        mock_datetime.now.return_value = mock_now

        agent = {"name": "Test", "ext": "1234", "timeBlock": "9:00-10:00"}
        assert is_agent_available(agent) is True

    @patch("staff_directory.datetime")
    def test_lunch_block_indicator(self, mock_datetime) -> None:
        """Lunch indicator 'L' should be handled correctly."""
        # Mock current time to 12:30 PM
        mock_now = datetime(2024, 1, 15, 12, 30, 0)
        mock_datetime.now.return_value = mock_now

        agent = {"name": "Test", "ext": "1234", "timeBlock": "12:00-1:00 L"}
        assert is_agent_available(agent) is False

    @patch("staff_directory.datetime")
    def test_agent_available_at_block_boundary_end(self, mock_datetime) -> None:
        """Agent should be unavailable at the exact end time."""
        # Mock current time to exactly 10:00 AM (boundary)
        mock_now = datetime(2024, 1, 15, 10, 0, 0)
        mock_datetime.now.return_value = mock_now

        agent = {"name": "Test", "ext": "1234", "timeBlock": "9:00-10:00"}
        # At the boundary, still considered in block
        assert is_agent_available(agent) is False

    @patch("staff_directory.datetime")
    def test_agent_available_just_after_block(self, mock_datetime) -> None:
        """Agent should be available just after their time block ends."""
        # Mock current time to 10:01 AM
        mock_now = datetime(2024, 1, 15, 10, 1, 0)
        mock_datetime.now.return_value = mock_now

        agent = {"name": "Test", "ext": "1234", "timeBlock": "9:00-10:00"}
        assert is_agent_available(agent) is True

    def test_malformed_time_block_returns_available(self) -> None:
        """Malformed time blocks should default to available."""
        agent = {"name": "Test", "ext": "1234", "timeBlock": "invalid"}
        assert is_agent_available(agent) is True

        agent_no_dash = {"name": "Test", "ext": "1234", "timeBlock": "9:00"}
        assert is_agent_available(agent_no_dash) is True

    @patch("staff_directory.datetime")
    def test_get_available_agent_returns_available_agent(self, mock_datetime) -> None:
        """get_available_agent_by_alpha should return agent when available."""
        # Mock current time to 11:00 AM (outside Adriana's 1:00-2:00 block)
        mock_now = datetime(2024, 1, 15, 11, 0, 0)
        mock_datetime.now.return_value = mock_now

        agent = get_available_agent_by_alpha("A", "CL", is_new_business=True)
        assert agent is not None
        assert agent["name"] == "Adriana"

    @patch("staff_directory.datetime")
    def test_get_available_agent_returns_none_when_unavailable(
        self, mock_datetime
    ) -> None:
        """get_available_agent_by_alpha should return None when agent unavailable."""
        # Mock current time to 1:30 PM (during Adriana's 1:00-2:00 block)
        mock_now = datetime(2024, 1, 15, 13, 30, 0)
        mock_datetime.now.return_value = mock_now

        agent = get_available_agent_by_alpha("A", "CL", is_new_business=True)
        assert agent is None


class TestNameMatchingFix:
    """Tests for the fixed name matching behavior."""

    def test_al_does_not_match_anamer(self) -> None:
        """'Al' should match Al, not Anamer L."""
        agent = get_agent_by_name("Al")
        assert agent is not None
        assert agent["name"] == "Al"
        assert agent["ext"] == "7015"

    def test_short_name_prefix_match(self) -> None:
        """Short names should use prefix matching."""
        # 'Ann' should match 'Ann', not 'Anamer L.'
        agent = get_agent_by_name("Ann")
        assert agent is not None
        assert agent["name"] == "Ann"

    def test_full_name_with_last_initial(self) -> None:
        """Full name with last initial should match."""
        agent = get_agent_by_name("Rachel T")
        assert agent is not None
        assert agent["name"] == "Rachel T."

    def test_first_name_only_matches_staff(self) -> None:
        """First name only should still find staff."""
        agent = get_agent_by_name("Rachel")
        assert agent is not None
        assert agent["name"] == "Rachel T."

    def test_search_with_extra_text_matches_first_name(self) -> None:
        """Search term starting with staff first name should match."""
        # "Adriana Smith" should match "Adriana"
        agent = get_agent_by_name("Adriana Smith")
        assert agent is not None
        assert agent["name"] == "Adriana"
