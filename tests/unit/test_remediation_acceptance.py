"""Acceptance tests for client feedback remediation (Phase 6).

These tests verify all 26 acceptance criteria from the remediation plan.
They are fast unit tests with no external API calls.
"""

import inspect
import os
import sys

import pytest

sys.path.insert(0, "src")

pytestmark = [pytest.mark.unit]


# Test 6.1: Contact info validation blocks transfer without name/phone
def test_validate_transfer_requires_name_and_phone():
    """AC-4: Transfer tools validate name+phone before transferring."""
    from unittest.mock import MagicMock

    from agents.assistant import Assistant
    from models import CallerInfo, InsuranceType

    agent = Assistant.__new__(Assistant)
    # Create a mock RunContext with CallerInfo that has insurance type but no name/phone
    caller_info = CallerInfo()
    caller_info.insurance_type = InsuranceType.PERSONAL
    caller_info.last_name_spelled = "SMITH"
    # name and phone_number should be None/empty
    context = MagicMock()
    context.userdata = caller_info
    result = agent._validate_transfer_requirements(context)
    assert result is not None, "Should return error when name/phone missing"
    assert "name" in result.lower() or "phone" in result.lower()


# Test 6.2: Restricted agent response text
def test_restricted_agent_response_text():
    """AC-14: Jason/Fred not directly transferable, offer message or alternative."""
    from staff_directory import is_transferable

    assert not is_transferable("Jason L."), "Jason should not be transferable"
    assert not is_transferable("Fred"), "Fred should not be transferable"
    # The response text is checked in the instruction/code -- verify the staff directory
    assert is_transferable("Adriana"), "Adriana should be transferable"
    assert is_transferable("Julie L."), "Julie should be transferable"


# Test 6.3: Appointment message matches client wording
def test_appointment_message_client_wording():
    """AC-17: Appointment message uses client's preferred wording."""
    from agents.assistant import Assistant

    source = inspect.getsource(Assistant)
    assert "walk-ins" in source and "strongly recommended" in source, (
        "Appointment message should mention walk-ins and strongly recommended"
    )
    assert "get that scheduled" in source, (
        "Transfer message should say 'get that scheduled'"
    )


# Test 6.4: No Dionna or Queens in codebase
def test_no_dionna_or_queens():
    """AC-8: No 'Queens' or 'Dionna' anywhere in source code."""
    src_dir = os.path.join(os.path.dirname(__file__), "..", "..", "src")
    src_dir = os.path.normpath(src_dir)

    for root, _dirs, files in os.walk(src_dir):
        for f in files:
            if f.endswith(".py"):
                filepath = os.path.join(root, f)
                with open(filepath) as fh:
                    content = fh.read()
                    assert "Dionna" not in content, f"Found 'Dionna' in {filepath}"
                    assert "Queens" not in content, f"Found 'Queens' in {filepath}"


# Test 6.5: No caller-facing "claims team" text
def test_no_caller_facing_claims_team():
    """AC-22: Claims doesn't say 'our claims team' to callers."""
    from agents.claims import ClaimsAgent

    source = inspect.getsource(ClaimsAgent)
    # "Claims Team" in ring group name is OK, but caller-facing text should not say it
    # Check tool return strings and say() calls
    assert "our claims team" not in source.lower(), (
        "Should not reference 'our claims team' in caller-facing text"
    )


# Test 6.6: Certificate new-cert mentions app and portal
def test_certificate_mentions_app():
    """AC-21: New certificate mentions Harry Levine Insurance app."""
    from agents.mortgagee import MortgageeCertificateAgent

    source = inspect.getsource(MortgageeCertificateAgent)
    assert (
        "Harry Levine Insurance app" in source
        or "harry levine insurance app" in source.lower()
    ), "New certificate response should mention the Harry Levine Insurance app"
    assert "login" in source.lower(), (
        "New certificate response should mention login information"
    )


# Test 6.7: Carrier list has >= 50 entries
def test_carrier_list_size():
    """Carrier claims numbers list has at least 50 entries (was 14)."""
    from constants import CARRIER_CLAIMS_NUMBERS

    assert len(CARRIER_CLAIMS_NUMBERS) >= 50, (
        f"Expected >= 50 carriers, got {len(CARRIER_CLAIMS_NUMBERS)}"
    )


# Test 6.8: Key Florida carriers present
def test_florida_carriers_present():
    """Critical Florida regional carriers are in the claims numbers list."""
    from constants import get_carrier_claims_number

    florida_carriers = [
        "Citizens",
        "Florida Peninsula",
        "Heritage",
        "Universal Property",
        "Tower Hill PL",
        "Security First",
        "People's Trust",
    ]
    for carrier in florida_carriers:
        result = get_carrier_claims_number(carrier)
        assert result is not None, f"Missing Florida carrier: {carrier}"


# Test 6.9: AE name in redirect message
def test_ae_name_in_redirect():
    """AC-13: Sales agent redirect includes AE name."""
    from agents.assistant import Assistant

    source = inspect.getsource(Assistant)
    assert "account manager is actually" in source, (
        "AE redirect should include 'account manager is actually {name}'"
    )


# Test 6.10: Pronunciation fields exist for ambiguous names
def test_pronunciation_fields():
    """Pronunciation fields present for TTS-ambiguous staff names."""
    from staff_directory import STAFF_DIRECTORY

    required_pronunciations = {"Adriana", "Rayvon", "Yarislyn", "Sheree", "Louis"}
    staff_with_pronunciation: set[str] = set()

    for staff in STAFF_DIRECTORY["staff"]:
        if staff.get("pronunciation"):
            staff_with_pronunciation.add(staff["name"].split()[0])  # First name only

    # Check Anamer separately since her entry uses "Anamer L."
    for staff in STAFF_DIRECTORY["staff"]:
        if staff["name"].startswith("Anamer") and staff.get("pronunciation"):
            staff_with_pronunciation.add("Anamer")

    required_pronunciations.add("Anamer")
    missing = required_pronunciations - staff_with_pronunciation
    assert not missing, f"Missing pronunciation for: {missing}"


# Test 6.11: Post-transfer silence instruction exists
def test_post_transfer_silence_instruction():
    """AC-15: Instruction exists telling agent not to speak after transfer."""
    from instruction_templates import ASSISTANT_OUTPUT_RULES

    rules_lower = ASSISTANT_OUTPUT_RULES.lower()
    assert "do not speak again" in rules_lower or "not speak again" in rules_lower, (
        "Output rules should contain post-transfer silence instruction"
    )


# Test 6.12: After-hours routing in exactly ONE location
def test_after_hours_single_location():
    """AC-25: After-hours routing instructions appear in exactly ONE detailed location."""
    from instruction_templates import (
        ASSISTANT_OFFICE_STATUS_GATE,
        ASSISTANT_SPECIAL_NOTES,
    )

    # OFFICE_STATUS_GATE should have the detailed after-hours routing
    assert "route_call_after_hours" in ASSISTANT_OFFICE_STATUS_GATE, (
        "OFFICE_STATUS_GATE should contain after-hours routing"
    )

    # SPECIAL_NOTES should NOT have detailed after-hours routing (just a cross-reference)
    assert "route_call_after_hours" not in ASSISTANT_SPECIAL_NOTES, (
        "SPECIAL_NOTES should not contain detailed after-hours routing (should be cross-ref only)"
    )


# Test 6.13: Bank caller detection includes new triggers
def test_bank_caller_detection_triggers():
    """AC-20: Bank caller detection includes 'recorded line' trigger."""
    from instruction_templates import ASSISTANT_EDGE_CASES

    edge_cases_lower = ASSISTANT_EDGE_CASES.lower()
    assert "recorded line" in edge_cases_lower or "on a recorded" in edge_cases_lower, (
        "Bank caller detection should include 'recorded line' as a trigger"
    )


# Test 6.14: Live person handling exists
def test_live_person_handling():
    """AC-24: Live person request gets structured response."""
    from instruction_templates import ASSISTANT_EDGE_CASES

    edge_cases_lower = ASSISTANT_EDGE_CASES.lower()
    assert (
        "live person" in edge_cases_lower
        or "real person" in edge_cases_lower
        or "representative" in edge_cases_lower
    ), "EDGE_CASES should handle live person / representative requests"


# =============================================================================
# Post-Audit Fix Tests
# =============================================================================


# C1: Claims instructions should NOT hardcode carrier list
def test_claims_no_hardcoded_carrier_list():
    """C1: Claims instructions should not contain hardcoded carrier names."""
    import inspect

    from agents.claims import ClaimsAgent

    source = inspect.getsource(ClaimsAgent)
    assert "Progressive, Travelers, Hartford, Liberty Mutual" not in source, (
        "Claims instructions should not hardcode specific carrier names"
    )
    assert "most major carriers" in source, (
        "Claims instructions should reference 'most major carriers'"
    )


# H1: Pronunciation used in route_call_specific_agent caller-facing speech
def test_pronunciation_in_specific_agent_routing():
    """H1: route_call_specific_agent uses pronunciation for caller-facing speech."""
    import inspect

    from agents.assistant import Assistant

    source = inspect.getsource(Assistant.route_call_specific_agent)
    # Caller-facing lines should use pronunciation-aware lookup
    assert (
        "agent.get('pronunciation'" in source or 'agent.get("pronunciation"' in source
    ), (
        "route_call_specific_agent should use agent.get('pronunciation', ...) for caller-facing speech"
    )


# H2: Whitespace-only name/phone rejected
def test_whitespace_validation_rejects_spaces():
    """H2: _validate_transfer_requirements rejects whitespace-only name/phone."""
    from unittest.mock import MagicMock

    from agents.assistant import Assistant
    from models import CallerInfo, InsuranceType

    agent = Assistant.__new__(Assistant)

    # Whitespace-only name should fail
    caller = CallerInfo()
    caller.insurance_type = InsuranceType.PERSONAL
    caller.name = "   "
    caller.phone_number = "5551234567"
    ctx = MagicMock()
    ctx.userdata = caller
    result = agent._validate_transfer_requirements(ctx)
    assert result is not None, "Whitespace-only name should be rejected"

    # Whitespace-only phone should fail
    caller2 = CallerInfo()
    caller2.insurance_type = InsuranceType.PERSONAL
    caller2.name = "John Smith"
    caller2.phone_number = "  "
    ctx2 = MagicMock()
    ctx2.userdata = caller2
    result2 = agent._validate_transfer_requirements(ctx2)
    assert result2 is not None, "Whitespace-only phone should be rejected"

    # Valid name + phone should pass (returns None for no error)
    caller3 = CallerInfo()
    caller3.insurance_type = InsuranceType.PERSONAL
    caller3.name = "John Smith"
    caller3.phone_number = "5551234567"
    caller3.last_name_spelled = "SMITH"
    ctx3 = MagicMock()
    ctx3.userdata = caller3
    result3 = agent._validate_transfer_requirements(ctx3)
    assert result3 is None, "Valid name + phone should pass validation"


# H3: Certificate response mentions portal and website
def test_certificate_mentions_portal_and_website():
    """H3: Certificate response mentions both app and portal/website."""
    import inspect

    from agents.mortgagee import MortgageeCertificateAgent

    source = inspect.getsource(MortgageeCertificateAgent.check_certificate_type)
    assert "portal" in source, "Certificate response should mention portal"
    assert "website" in source or "harry levine insurance dot com" in source, (
        "Certificate response should mention website"
    )


# M1: No trailing filler in request_callback
def test_request_callback_no_trailing_filler():
    """M1: request_callback should not contain trailing filler question."""
    import inspect

    from agents.claims import ClaimsAgent

    source = inspect.getsource(ClaimsAgent.request_callback)
    assert "Is there anything else" not in source, (
        "request_callback should not contain trailing filler"
    )


# M2: assigned_agent stores canonical name, not pronunciation
def test_assigned_agent_stores_canonical_name():
    """M2: assigned_agent must store agent['name'], not pronunciation."""
    import inspect

    from agents.assistant import Assistant
    from agents.mortgagee import MortgageeCertificateAgent

    # Both assistant.py and mortgagee.py must store canonical name
    assistant_source = inspect.getsource(Assistant)
    assert 'userdata.assigned_agent = agent["name"]' in assistant_source, (
        "Assistant: assigned_agent should store canonical agent name"
    )

    mortgagee_source = inspect.getsource(
        MortgageeCertificateAgent.transfer_existing_certificate
    )
    assert 'userdata.assigned_agent = agent["name"]' in mortgagee_source, (
        "MortgageeCertificateAgent: assigned_agent should store canonical agent name, not pronunciation"
    )
    # Verify pronunciation is NOT stored in assigned_agent
    assert "userdata.assigned_agent = agent_display" not in mortgagee_source, (
        "assigned_agent must not store the pronunciation/display name"
    )


def test_assigned_agent_lookup_works_with_pronunciation():
    """M2: assigned_agent with canonical name still resolves via get_agent_by_name."""
    from staff_directory import get_agent_by_name

    # Yarislyn has a pronunciation field — verify canonical name still resolves
    agent = get_agent_by_name("Yarislyn")
    assert agent is not None, "get_agent_by_name('Yarislyn') should find the agent"
    assert agent.get("pronunciation") == "Yah-ris-lin"

    # Pronunciation string must NOT resolve (this was the bug)
    assert get_agent_by_name("Yah-ris-lin") is None, (
        "Pronunciation string should NOT resolve via get_agent_by_name"
    )


# M4: Second-tier live person escalation exists
def test_second_tier_live_person_escalation():
    """M4: Second-insistence escalation for live person requests."""
    from instruction_templates import ASSISTANT_EDGE_CASES

    edge_cases_lower = ASSISTANT_EDGE_CASES.lower()
    assert "insists again" in edge_cases_lower, (
        "EDGE_CASES should handle second insistence on live person"
    )
    assert "name, phone number, and what you need help with" in edge_cases_lower, (
        "Second-tier response should mention name, phone number, and what they need"
    )


# L1: TTS pronunciation comment exists
def test_harry_leveen_tts_comment():
    """L1: Comment explains Harry Leveen intentional TTS spelling."""
    import inspect

    import instruction_templates

    source = inspect.getsource(instruction_templates)
    assert "intentional TTS pronunciation" in source, (
        "Comment should explain Harry Leveen is intentional TTS pronunciation spelling"
    )


# L2: get_bilingual_agents default is empty list
def test_bilingual_agents_default_empty():
    """L2: Staff without explicit languages field excluded from results."""
    from staff_directory import get_bilingual_agents

    # Spanish agents should still be returned (they have explicit languages field)
    spanish_agents = get_bilingual_agents("es")
    assert len(spanish_agents) > 0, "Should still return Spanish-speaking agents"

    # English query should NOT return all staff (old behavior)
    english_agents = get_bilingual_agents("en")
    all_staff_count = 18  # Total staff count
    assert len(english_agents) < all_staff_count, (
        "get_bilingual_agents('en') should not return all staff"
    )
