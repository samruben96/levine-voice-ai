"""New Quote Agent for the Harry Levine Insurance Voice Agent.

This module contains the NewQuoteAgent class which handles new insurance
quote requests from callers.
"""

import logging
from typing import TYPE_CHECKING

from livekit.agents import RunContext, function_tool

from base_agent import BaseRoutingAgent
from instruction_templates import (
    ON_ENTER_CHECK_CONTEXT,
    RULES_STANDARD,
    SECURITY_INSTRUCTIONS,
    TYPE_DETECTION_INSTRUCTIONS,
    compose_instructions,
    format_collection_flow,
)
from models import CallerInfo, CallIntent, InsuranceType
from staff_directory import find_agent_by_alpha, get_agent_by_name, get_alpha_route_key
from utils import mask_name

if TYPE_CHECKING:
    from livekit.agents import AgentSession

logger = logging.getLogger("agent")


class NewQuoteAgent(BaseRoutingAgent):
    """Specialized agent for handling new quote requests.

    This agent is handed off to when the caller indicates they want a new quote.
    It follows the specific flow:
    1. Confirm insurance type (business vs personal)
    2. Collect appropriate information based on type
    3. Route to the correct sales agent via alpha-split

    Inherits transfer/fallback behavior from BaseRoutingAgent.
    """

    # Customize logging and messaging for new quotes
    transfer_log_prefix: str = "new quote"
    fallback_log_context: str = "for new quote"
    datasheet_log_prefix: str = "new quote callback"
    datasheet_message: str = (
        "I apologize, but our sales agents are currently helping other customers. "
        "I have all your information and one of our agents will call you back "
        "as soon as possible to help with your quote. Is there anything else I can note for them?"
    )

    def __init__(self) -> None:
        super().__init__(
            instructions=compose_instructions(
                "You are Aizellee, helping a caller who wants a new insurance quote.",
                "GOAL: Collect info to route them to the right sales agent.",
                f"""FLOW:
1. {TYPE_DETECTION_INSTRUCTIONS}

2. {format_collection_flow("record_business_quote_info", "record_personal_quote_info")}

3. CONFIRM AND TRANSFER:
   "Thanks [name], to confirm - you need a quote for [business name/personal insurance]. Let me connect you."
   Use transfer_to_sales_agent.""",
                RULES_STANDARD,
                """EDGE CASES:
- Caller won't spell name: "No problem, can you tell me just the first letter of your last name?"
- Multiple businesses: "Which business would you like to start with today?"
- Unclear response: Ask for clarification, don't assume""",
                SECURITY_INSTRUCTIONS,
            ),
        )

    async def on_enter(self) -> None:
        """Called when this agent becomes active - start the quote flow.

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
                f"New quote: Business info already collected - {userdata.business_name}"
            )
            # Perform the routing logic (same as record_business_quote_info)
            # NEW QUOTE -> is_new_business=True -> routes to Sales Agents
            route_key = get_alpha_route_key(userdata.business_name)
            agent = find_agent_by_alpha(route_key, "CL", is_new_business=True)
            if agent:
                userdata.assigned_agent = agent["name"]
            userdata.call_intent = CallIntent.NEW_QUOTE

            # Generate response acknowledging and proceeding to transfer
            session.generate_reply(
                instructions=(
                    f"The caller wants a new insurance quote for their business '{userdata.business_name}'. "
                    "You already have their info. Confirm the business name briefly, "
                    "then use transfer_to_sales_agent to connect them."
                )
            )
        elif has_personal_identifier:
            # Personal info complete - set up routing and proceed to transfer
            logger.info(
                f"New quote: Personal info already collected - last name: {mask_name(userdata.last_name_spelled)}"
            )
            # Perform the routing logic (same as record_personal_quote_info)
            # NEW QUOTE -> is_new_business=True -> routes to Sales Agents
            first_letter = (
                userdata.last_name_spelled[0].upper()
                if userdata.last_name_spelled
                else "A"
            )
            agent = find_agent_by_alpha(first_letter, "PL", is_new_business=True)
            if agent:
                userdata.assigned_agent = agent["name"]
            userdata.call_intent = CallIntent.NEW_QUOTE

            # Generate response acknowledging and proceeding to transfer
            session.generate_reply(
                instructions=(
                    f"The caller wants a new personal insurance quote. Their last name is '{userdata.last_name_spelled}'. "
                    "You already have their info. Confirm their name briefly, "
                    "then use transfer_to_sales_agent to connect them."
                )
            )
        elif has_insurance_type and userdata.insurance_type == InsuranceType.BUSINESS:
            # Know it's business but missing business name
            logger.info("New quote: Know it's business, need business name")
            session.generate_reply(
                instructions=(
                    "The caller wants a new quote for BUSINESS insurance. "
                    "Ask 'What is the name of the business?' Use record_business_quote_info "
                    "after they provide it."
                )
            )
        elif has_insurance_type and userdata.insurance_type == InsuranceType.PERSONAL:
            # Know it's personal but missing last name
            logger.info("New quote: Know it's personal, need last name")
            session.generate_reply(
                instructions=(
                    "The caller wants a new quote for PERSONAL insurance. "
                    "Ask 'Can you spell your last name for me?' Use record_personal_quote_info "
                    "after they spell it."
                )
            )
        else:
            # No pre-collected info - use standard flow
            session.generate_reply(instructions=ON_ENTER_CHECK_CONTEXT)

    @function_tool
    async def record_business_quote_info(
        self,
        context: RunContext[CallerInfo],
        business_name: str,
    ) -> str:
        """Record business insurance quote information.

        Call this tool after the caller provides their business name.

        Args:
            business_name: The name of the business seeking insurance
        """
        context.userdata.insurance_type = InsuranceType.BUSINESS
        context.userdata.business_name = business_name
        context.userdata.call_intent = CallIntent.NEW_QUOTE

        # Use staff directory routing for Commercial Lines
        route_key = get_alpha_route_key(business_name)
        agent = find_agent_by_alpha(route_key, "CL", is_new_business=True)

        if agent:
            context.userdata.assigned_agent = agent["name"]
            logger.info(
                f"New quote - Business insurance for: {business_name} "
                f"(route key: {route_key}) -> {agent['name']} ext {agent['ext']}"
            )
            return f"Got it, I have this noted for {business_name}. Let me connect you with {agent['name']}."
        else:
            logger.info(
                f"New quote - Business insurance for: {business_name} (no agent found)"
            )
            return f"Got it, I have this noted for {business_name}. Let me connect you with one of our commercial insurance specialists."

    @function_tool
    async def record_personal_quote_info(
        self,
        context: RunContext[CallerInfo],
        last_name_spelled: str,
    ) -> str:
        """Record personal insurance quote information with spelled last name.

        Call this tool after the caller spells their last name.

        Args:
            last_name_spelled: The caller's last name as they spelled it out letter by letter
        """
        context.userdata.insurance_type = InsuranceType.PERSONAL
        context.userdata.last_name_spelled = last_name_spelled
        context.userdata.call_intent = CallIntent.NEW_QUOTE

        # Use staff directory routing for Personal Lines (new business -> Sales Agents)
        first_letter = (
            last_name_spelled[0].upper()
            if last_name_spelled and len(last_name_spelled) > 0
            else "A"
        )
        agent = find_agent_by_alpha(first_letter, "PL", is_new_business=True)

        if agent:
            context.userdata.assigned_agent = agent["name"]
            logger.info(
                f"New quote - Personal insurance, last name: {mask_name(last_name_spelled)} "
                f"(letter: {first_letter}) -> {agent['name']} ext {agent['ext']}"
            )
            return f"Thank you, I have that as {last_name_spelled}. Let me connect you with {agent['name']}."
        else:
            logger.info(
                f"New quote - Personal insurance, last name: {mask_name(last_name_spelled)} (no agent found)"
            )
            return f"Thank you, I have that as {last_name_spelled}. Let me connect you with one of our agents."

    @function_tool
    async def transfer_to_sales_agent(
        self,
        context: RunContext[CallerInfo],
    ) -> str:
        """Transfer the caller to the appropriate sales agent.

        Call this after recording the caller's information to initiate the transfer.
        For business insurance, uses CL alpha-split routing.
        For personal insurance, uses PL alpha-split routing based on last name.
        """
        userdata = context.userdata

        if userdata.insurance_type == InsuranceType.BUSINESS:
            # Business insurance - route via CL alpha-split
            agent_name = userdata.assigned_agent
            if agent_name:
                agent = get_agent_by_name(agent_name)
                if agent:
                    logger.info(
                        f"Transferring business quote to {agent['name']} ext {agent['ext']}"
                    )
                    return await self._initiate_transfer(context, agent)
            # Fallback if no agent assigned
            logger.info(
                "Transferring business quote - no agent assigned, using fallback"
            )
            return await self._handle_fallback(context, None)

        elif userdata.insurance_type == InsuranceType.PERSONAL:
            # Personal insurance - route via PL alpha-split
            agent_name = userdata.assigned_agent
            if agent_name:
                agent = get_agent_by_name(agent_name)
                if agent:
                    logger.info(
                        f"Transferring personal quote to {agent['name']} ext {agent['ext']}"
                    )
                    return await self._initiate_transfer(context, agent)
                else:
                    # Agent unavailable - use fallback
                    return await self._handle_fallback(context, agent_name)
            else:
                # No agent assigned - use fallback
                return await self._handle_fallback(context, None)

        return "I'll connect you with one of our agents who can help with your quote."
