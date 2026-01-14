"""Make Change Agent for the Harry Levine Insurance Voice Agent.

This module contains the MakeChangeAgent class which handles policy
change and modification requests from callers.
"""

import logging
from typing import TYPE_CHECKING

from livekit.agents import RunContext, function_tool

from base_agent import BaseRoutingAgent
from instruction_templates import (
    ON_ENTER_CHECK_CONTEXT_EXTENDED,
    RULES_WITH_SMART_DETECTION,
    SECURITY_INSTRUCTIONS,
    TYPE_DETECTION_EXTENDED,
    compose_instructions,
    format_collection_flow,
)
from models import CallerInfo, CallIntent, InsuranceType
from staff_directory import find_agent_by_alpha, get_agent_by_name, get_alpha_route_key
from utils import mask_name

if TYPE_CHECKING:
    from livekit.agents import AgentSession

logger = logging.getLogger("agent")


class MakeChangeAgent(BaseRoutingAgent):
    """Specialized agent for handling policy change and modification requests.

    This agent is handed off to when the caller indicates they want to:
    - Make changes to their existing policy
    - Add or remove a vehicle, driver, or coverage
    - Update their address or contact information
    - Modify policy limits or deductibles
    - Swap vehicles (e.g., work trucks)
    - Request endorsements

    It follows the specific flow:
    1. Determine insurance type from context or by asking
    2. Collect appropriate identifier (business name or last name)
    3. Route to Account Executive via alpha-split

    Routing Logic:
    - Personal Lines: PL Account Executives by last name (A-G: Yarislyn, H-M: Al, N-Z: Luis)
    - Commercial Lines: CL Account Executives by business name (A-F: Adriana, G-O: Rayvon, P-Z: Dionna)

    Inherits transfer/fallback behavior from BaseRoutingAgent.
    """

    # Customize logging and messaging for policy changes
    transfer_log_prefix: str = "policy change"
    fallback_log_context: str = "for policy change"
    datasheet_log_prefix: str = "policy change callback"
    datasheet_message: str = (
        "I apologize, but your Account Executive is currently busy helping other customers. "
        "I have all your information and they will call you back "
        "as soon as possible. Is there anything else I can note for them about the changes you need?"
    )

    def __init__(self) -> None:
        super().__init__(
            instructions=compose_instructions(
                "You are Aizellee, helping a caller who wants to make changes to their policy.",
                "GOAL: Collect info to route them to their Account Executive who handles policy changes.",
                f"""FLOW:
1. {TYPE_DETECTION_EXTENDED}
   - If caller says things like "swap a work truck" or "add a company vehicle", SKIP asking business/personal - it's clearly business insurance

2. {format_collection_flow("record_business_change_info", "record_personal_change_info")}

3. CONFIRM AND TRANSFER:
   "Thanks, to confirm - you need to make changes to [business name/your personal policy]. Let me connect you with your Account Executive."
   Use transfer_to_account_executive.""",
                RULES_WITH_SMART_DETECTION,
                """EDGE CASES:
- Caller won't spell name: "No problem, can you tell me just the first letter of your last name?"
- Multiple policies: "Which policy would you like to update today?"
- Multiple changes: "No problem, I can connect you to discuss all your changes. First, [continue flow]"
- Unclear response: Ask for clarification, don't assume""",
                """COMMON CHANGE REQUESTS (for context):
- Add/remove vehicle, driver, or property
- Change address or contact info
- Modify coverage limits or deductibles
- Swap vehicles (especially work trucks)
- Add/remove coverage types
- Endorsements""",
                SECURITY_INSTRUCTIONS,
            ),
        )

    async def on_enter(self) -> None:
        """Called when this agent becomes active - start the policy change flow.

        Checks if the Assistant already collected insurance type and identifier
        (business_name or last_name_spelled). If complete info is available,
        skips re-asking and proceeds directly to routing/transfer.
        """
        session: AgentSession[CallerInfo] = self.session
        userdata = session.userdata

        # Check what info is already available from the Assistant
        has_insurance_type = userdata.insurance_type is not None
        has_business_identifier = (
            userdata.insurance_type == InsuranceType.BUSINESS
            and userdata.business_name is not None
            and userdata.business_name.strip() != ""
        )
        has_personal_identifier = (
            userdata.insurance_type == InsuranceType.PERSONAL
            and userdata.last_name_spelled is not None
            and userdata.last_name_spelled.strip() != ""
        )

        if has_business_identifier:
            # Business info complete - set up routing and proceed to transfer
            logger.info(
                f"Policy change: Business info already collected - {userdata.business_name}"
            )
            # Perform the routing logic (same as record_business_change_info)
            route_key = get_alpha_route_key(userdata.business_name)
            agent = find_agent_by_alpha(route_key, "CL", is_new_business=False)
            if agent:
                userdata.assigned_agent = agent["name"]
            userdata.call_intent = CallIntent.MAKE_CHANGE

            # Generate response acknowledging and proceeding to transfer
            session.generate_reply(
                instructions=(
                    f"The caller wants to make changes to their BUSINESS policy for '{userdata.business_name}'. "
                    "You already have their info. Confirm the business name briefly, "
                    "then use transfer_to_account_executive to connect them."
                )
            )
        elif has_personal_identifier:
            # Personal info complete - set up routing and proceed to transfer
            logger.info(
                f"Policy change: Personal info already collected - last name: {mask_name(userdata.last_name_spelled)}"
            )
            # Perform the routing logic (same as record_personal_change_info)
            first_letter = (
                userdata.last_name_spelled[0].upper()
                if userdata.last_name_spelled
                else "A"
            )
            agent = find_agent_by_alpha(first_letter, "PL", is_new_business=False)
            if agent:
                userdata.assigned_agent = agent["name"]
            userdata.call_intent = CallIntent.MAKE_CHANGE

            # Generate response acknowledging and proceeding to transfer
            session.generate_reply(
                instructions=(
                    f"The caller wants to make changes to their PERSONAL policy. Their last name is '{userdata.last_name_spelled}'. "
                    "You already have their info. Confirm their name briefly, "
                    "then use transfer_to_account_executive to connect them."
                )
            )
        elif has_insurance_type and userdata.insurance_type == InsuranceType.BUSINESS:
            # Know it's business but missing business name
            logger.info("Policy change: Know it's business, need business name")
            session.generate_reply(
                instructions=(
                    "The caller wants to make changes to their BUSINESS policy. "
                    "Ask 'What is the name of the business?' Use record_business_change_info "
                    "after they provide it."
                )
            )
        elif has_insurance_type and userdata.insurance_type == InsuranceType.PERSONAL:
            # Know it's personal but missing last name
            logger.info("Policy change: Know it's personal, need last name")
            session.generate_reply(
                instructions=(
                    "The caller wants to make changes to their PERSONAL policy. "
                    "Ask 'Can you spell your last name for me?' Use record_personal_change_info "
                    "after they spell it."
                )
            )
        else:
            # No pre-collected info - use standard flow
            session.generate_reply(instructions=ON_ENTER_CHECK_CONTEXT_EXTENDED)

    @function_tool
    async def record_business_change_info(
        self,
        context: RunContext[CallerInfo],
        business_name: str,
    ) -> str:
        """Record business insurance policy change information.

        Call this tool after the caller provides their business name.

        Args:
            business_name: The name of the business requesting policy changes
        """
        context.userdata.insurance_type = InsuranceType.BUSINESS
        context.userdata.business_name = business_name
        context.userdata.call_intent = CallIntent.MAKE_CHANGE

        # Use staff directory routing for Commercial Lines
        # EXISTING clients go to Account Executives (is_new_business=False)
        route_key = get_alpha_route_key(business_name)
        agent = find_agent_by_alpha(route_key, "CL", is_new_business=False)

        if agent:
            context.userdata.assigned_agent = agent["name"]
            logger.info(
                f"Policy change request - Business: {business_name} "
                f"(route key: {route_key}) -> {agent['name']} ext {agent['ext']}"
            )
            return f"Got it, I have this noted for {business_name}. Let me connect you with {agent['name']}, your Account Executive."
        else:
            logger.info(
                f"Policy change request - Business: {business_name} (no agent found)"
            )
            return f"Got it, I have this noted for {business_name}. Let me connect you with your Account Executive."

    @function_tool
    async def record_personal_change_info(
        self,
        context: RunContext[CallerInfo],
        last_name_spelled: str,
    ) -> str:
        """Record personal insurance policy change information with spelled last name.

        Call this tool after the caller spells their last name.

        Args:
            last_name_spelled: The caller's last name as they spelled it out letter by letter
        """
        context.userdata.insurance_type = InsuranceType.PERSONAL
        context.userdata.last_name_spelled = last_name_spelled
        context.userdata.call_intent = CallIntent.MAKE_CHANGE

        # Use staff directory routing for Personal Lines
        # EXISTING clients go to Account Executives (is_new_business=False)
        first_letter = (
            last_name_spelled[0].upper()
            if last_name_spelled and len(last_name_spelled) > 0
            else "A"
        )
        agent = find_agent_by_alpha(first_letter, "PL", is_new_business=False)

        if agent:
            context.userdata.assigned_agent = agent["name"]
            logger.info(
                f"Policy change request - Personal, last name: {mask_name(last_name_spelled)} "
                f"(letter: {first_letter}) -> {agent['name']} ext {agent['ext']}"
            )
            return f"Thank you, I have that as {last_name_spelled}. Let me connect you with {agent['name']}, your Account Executive."
        else:
            logger.info(
                f"Policy change request - Personal, last name: {mask_name(last_name_spelled)} (no agent found)"
            )
            return f"Thank you, I have that as {last_name_spelled}. Let me connect you with your Account Executive."

    @function_tool
    async def transfer_to_account_executive(
        self,
        context: RunContext[CallerInfo],
    ) -> str:
        """Transfer the caller to their Account Executive for policy changes.

        Call this after recording the caller's information to initiate the transfer.
        For business insurance, uses CL alpha-split routing to Account Executives.
        For personal insurance, uses PL alpha-split routing to Account Executives.
        """
        userdata = context.userdata

        if userdata.insurance_type == InsuranceType.BUSINESS:
            # Business insurance - route via CL alpha-split to Account Executive
            agent_name = userdata.assigned_agent
            if agent_name:
                agent = get_agent_by_name(agent_name)
                if agent:
                    logger.info(
                        f"Transferring policy change to {agent['name']} ext {agent['ext']}"
                    )
                    return await self._initiate_transfer(context, agent)
            # Fallback if no agent assigned
            logger.info(
                "Transferring policy change - no agent assigned, using fallback"
            )
            return await self._handle_fallback(context, None)

        elif userdata.insurance_type == InsuranceType.PERSONAL:
            # Personal insurance - route via PL alpha-split to Account Executive
            agent_name = userdata.assigned_agent
            if agent_name:
                agent = get_agent_by_name(agent_name)
                if agent:
                    logger.info(
                        f"Transferring policy change to {agent['name']} ext {agent['ext']}"
                    )
                    return await self._initiate_transfer(context, agent)
                else:
                    # Agent unavailable - use fallback
                    return await self._handle_fallback(context, agent_name)
            else:
                # No agent assigned - use fallback
                return await self._handle_fallback(context, None)

        return "I'll connect you with your Account Executive who can help with your policy changes."
