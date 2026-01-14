"""Cancellation Agent for the Harry Levine Insurance Voice Agent.

This module contains the CancellationAgent class which handles policy
cancellation requests from callers.
"""

import logging
from typing import TYPE_CHECKING

from livekit.agents import RunContext, function_tool

from base_agent import BaseRoutingAgent
from instruction_templates import (
    EDGE_CASES_CANCELLATION,
    EMPATHY_CANCELLATION,
    ON_ENTER_CHECK_CONTEXT_CANCELLATION,
    RULES_CANCELLATION,
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


class CancellationAgent(BaseRoutingAgent):
    """Specialized agent for handling policy cancellation requests.

    This agent is handed off to when the caller indicates they want to:
    - Cancel their existing policy
    - End their coverage
    - Not renew their policy
    - Switch to another carrier

    It follows the specific flow:
    1. Show empathy about the cancellation (without being pushy about retention)
    2. Determine insurance type from context or by asking
    3. Collect appropriate identifier (business name or last name)
    4. Route to Account Executive via alpha-split

    Routing Logic (EXISTING clients to Account Executives):
    - Personal Lines: PL Account Executives by last name (A-G: Yarislyn, H-M: Al, N-Z: Luis)
    - Commercial Lines: CL Account Executives by business name (A-F: Adriana, G-O: Rayvon, P-Z: Dionna)

    Note: This agent respects the caller's decision and does not attempt aggressive
    retention tactics. The Account Executive will handle any retention conversation.

    Inherits transfer/fallback behavior from BaseRoutingAgent.
    """

    # Customize logging and messaging for cancellations
    transfer_log_prefix: str = "cancellation"
    fallback_log_context: str = "for cancellation"
    datasheet_log_prefix: str = "cancellation callback"
    include_notes_in_log: bool = True  # Log reason for cancellation
    datasheet_message: str = (
        "I apologize, but your Account Executive is currently busy helping other customers. "
        "I have all your information and they will call you back "
        "as soon as possible. Before I let you go, may I ask the reason for the cancellation "
        "so I can note it for them? And is there a preferred time for them to call you back?"
    )

    def __init__(self) -> None:
        # Use cancellation-specific type detection with adjusted clues
        cancellation_type_detection = TYPE_DETECTION_EXTENDED.replace(
            "work truck", "work policy"
        ).replace("company vehicle", "business policy")

        super().__init__(
            instructions=compose_instructions(
                "You are Aizellee, helping a caller who wants to cancel their policy.",
                "GOAL: Collect info to route them to their Account Executive who handles cancellations.",
                EMPATHY_CANCELLATION,
                f"""FLOW:
1. ACKNOWLEDGE with empathy (brief, not over-the-top):
   - "I understand you'd like to cancel your policy."
   - "I'm sorry to hear that. Let me help you with the cancellation."

2. {cancellation_type_detection}

3. {format_collection_flow("record_business_cancellation_info", "record_personal_cancellation_info")}

4. CONFIRM AND TRANSFER:
   "Thanks, to confirm - you'd like to cancel [business name/your personal policy]. Let me connect you with your Account Executive who can help with that."
   Use transfer_to_account_executive.""",
                RULES_CANCELLATION,
                EDGE_CASES_CANCELLATION,
                """REASONS CALLERS CANCEL (for context):
- Found cheaper insurance elsewhere
- Selling the insured property (car, home, business)
- Moving out of state
- Financial reasons
- Dissatisfaction with service or claims
- No longer need the coverage""",
                SECURITY_INSTRUCTIONS,
            ),
        )

    async def on_enter(self) -> None:
        """Called when this agent becomes active - start the cancellation flow.

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
                f"Cancellation: Business info already collected - {userdata.business_name}"
            )
            # Perform the routing logic (same as record_business_cancellation_info)
            route_key = get_alpha_route_key(userdata.business_name)
            agent = find_agent_by_alpha(route_key, "CL", is_new_business=False)
            if agent:
                userdata.assigned_agent = agent["name"]
            userdata.call_intent = CallIntent.CANCELLATION

            # Generate response acknowledging and proceeding to transfer
            session.generate_reply(
                instructions=(
                    f"The caller wants to cancel their BUSINESS policy for '{userdata.business_name}'. "
                    "You already have their info. Show brief empathy (e.g., 'I understand you'd like to cancel'), "
                    f"confirm the business name, then use transfer_to_account_executive to connect them."
                )
            )
        elif has_personal_identifier:
            # Personal info complete - set up routing and proceed to transfer
            logger.info(
                f"Cancellation: Personal info already collected - last name: {mask_name(userdata.last_name_spelled)}"
            )
            # Perform the routing logic (same as record_personal_cancellation_info)
            first_letter = (
                userdata.last_name_spelled[0].upper()
                if userdata.last_name_spelled
                else "A"
            )
            agent = find_agent_by_alpha(first_letter, "PL", is_new_business=False)
            if agent:
                userdata.assigned_agent = agent["name"]
            userdata.call_intent = CallIntent.CANCELLATION

            # Generate response acknowledging and proceeding to transfer
            session.generate_reply(
                instructions=(
                    f"The caller wants to cancel their PERSONAL policy. Their last name is '{userdata.last_name_spelled}'. "
                    "You already have their info. Show brief empathy (e.g., 'I understand you'd like to cancel'), "
                    "confirm their name, then use transfer_to_account_executive to connect them."
                )
            )
        elif has_insurance_type and userdata.insurance_type == InsuranceType.BUSINESS:
            # Know it's business but missing business name
            logger.info("Cancellation: Know it's business, need business name")
            session.generate_reply(
                instructions=(
                    "The caller wants to cancel their BUSINESS policy. Show brief empathy, "
                    "then ask 'What is the name of the business?' Use record_business_cancellation_info "
                    "after they provide it."
                )
            )
        elif has_insurance_type and userdata.insurance_type == InsuranceType.PERSONAL:
            # Know it's personal but missing last name
            logger.info("Cancellation: Know it's personal, need last name")
            session.generate_reply(
                instructions=(
                    "The caller wants to cancel their PERSONAL policy. Show brief empathy, "
                    "then ask 'Can you spell your last name for me?' Use record_personal_cancellation_info "
                    "after they spell it."
                )
            )
        else:
            # No pre-collected info - use standard flow
            session.generate_reply(instructions=ON_ENTER_CHECK_CONTEXT_CANCELLATION)

    @function_tool
    async def record_business_cancellation_info(
        self,
        context: RunContext[CallerInfo],
        business_name: str,
    ) -> str:
        """Record business insurance cancellation information.

        Call this tool after the caller provides their business name.

        Args:
            business_name: The name of the business requesting policy cancellation
        """
        context.userdata.insurance_type = InsuranceType.BUSINESS
        context.userdata.business_name = business_name
        context.userdata.call_intent = CallIntent.CANCELLATION

        # Use staff directory routing for Commercial Lines
        # EXISTING clients go to Account Executives (is_new_business=False)
        route_key = get_alpha_route_key(business_name)
        agent = find_agent_by_alpha(route_key, "CL", is_new_business=False)

        if agent:
            context.userdata.assigned_agent = agent["name"]
            logger.info(
                f"Cancellation request - Business: {business_name} "
                f"(route key: {route_key}) -> {agent['name']} ext {agent['ext']}"
            )
            return f"Got it, I have this noted for {business_name}. Let me connect you with {agent['name']}, your Account Executive."
        else:
            logger.info(
                f"Cancellation request - Business: {business_name} (no agent found)"
            )
            return f"Got it, I have this noted for {business_name}. Let me connect you with your Account Executive."

    @function_tool
    async def record_personal_cancellation_info(
        self,
        context: RunContext[CallerInfo],
        last_name_spelled: str,
    ) -> str:
        """Record personal insurance cancellation information with spelled last name.

        Call this tool after the caller spells their last name.

        Args:
            last_name_spelled: The caller's last name as they spelled it out letter by letter
        """
        context.userdata.insurance_type = InsuranceType.PERSONAL
        context.userdata.last_name_spelled = last_name_spelled
        context.userdata.call_intent = CallIntent.CANCELLATION

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
                f"Cancellation request - Personal, last name: {mask_name(last_name_spelled)} "
                f"(letter: {first_letter}) -> {agent['name']} ext {agent['ext']}"
            )
            return f"Thank you, I have that as {last_name_spelled}. Let me connect you with {agent['name']}, your Account Executive."
        else:
            logger.info(
                f"Cancellation request - Personal, last name: {mask_name(last_name_spelled)} (no agent found)"
            )
            return f"Thank you, I have that as {last_name_spelled}. Let me connect you with your Account Executive."

    @function_tool
    async def transfer_to_account_executive(
        self,
        context: RunContext[CallerInfo],
    ) -> str:
        """Transfer the caller to their Account Executive for policy cancellation.

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
                        f"Transferring cancellation to {agent['name']} ext {agent['ext']}"
                    )
                    return await self._initiate_transfer(context, agent)
            # Fallback if no agent assigned
            logger.info("Transferring cancellation - no agent assigned, using fallback")
            return await self._handle_fallback(context, None)

        elif userdata.insurance_type == InsuranceType.PERSONAL:
            # Personal insurance - route via PL alpha-split to Account Executive
            agent_name = userdata.assigned_agent
            if agent_name:
                agent = get_agent_by_name(agent_name)
                if agent:
                    logger.info(
                        f"Transferring cancellation to {agent['name']} ext {agent['ext']}"
                    )
                    return await self._initiate_transfer(context, agent)
                else:
                    # Agent unavailable - use fallback
                    return await self._handle_fallback(context, agent_name)
            else:
                # No agent assigned - use fallback
                return await self._handle_fallback(context, None)

        return "I'll connect you with your Account Executive who can help with the cancellation."
