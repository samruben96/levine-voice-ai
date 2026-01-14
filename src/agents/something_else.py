"""Something Else Agent for the Harry Levine Insurance Voice Agent.

This module contains the SomethingElseAgent class which handles requests
that don't fit other specific categories (catch-all handler).
"""

import logging
from typing import TYPE_CHECKING

from livekit.agents import RunContext, function_tool

from base_agent import BaseRoutingAgent
from instruction_templates import (
    ON_ENTER_CHECK_CONTEXT_EXTENDED,
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


class SomethingElseAgent(BaseRoutingAgent):
    """Specialized agent for handling requests that don't fit other categories.

    This agent is the catch-all/fallback for requests that don't match specific
    intents like quotes, payments, policy changes, cancellations, or coverage
    questions. It collects a brief summary of what the caller needs and routes
    them to their Account Executive via alpha-split.

    This agent performs a WARM TRANSFER, meaning it collects context about the
    caller's request to relay to the receiving agent.

    It follows the specific flow:
    1. Confirm insurance type (business vs personal)
    2. Ask for a brief summary of what they're calling about
    3. Collect appropriate identifier (business name or last name)
    4. Route to Account Executive via alpha-split with context

    Routing Logic (EXISTING clients to Account Executives):
    - Personal Lines: PL Account Executives by last name (A-G: Yarislyn, H-M: Al, N-Z: Luis)
    - Commercial Lines: CL Account Executives by business name (A-F: Adriana, G-O: Rayvon, P-Z: Dionna)

    Note: The caller's summary is stored in CallerInfo.additional_notes for context
    relay during the warm transfer.
    """

    # Class attributes for BaseRoutingAgent customization
    transfer_log_prefix = "something else"
    fallback_log_context = "for other inquiry"
    datasheet_log_prefix = "other inquiry callback"
    is_warm_transfer = True
    include_notes_in_log = True  # Include summary in data sheet log
    datasheet_message = (
        "I apologize, but your Account Executive is currently busy helping other customers. "
        "I have all your information including what you're calling about, and they will call you back "
        "as soon as possible. Is there a preferred time for them to call you back?"
    )

    def __init__(self) -> None:
        super().__init__(
            instructions=compose_instructions(
                "You are Aizellee, helping a caller whose request doesn't fit standard categories.",
                "GOAL: Collect info about what they need and route them to the right Account Executive.",
                "IMPORTANT: This is a WARM TRANSFER - collect context to relay to the receiving agent.",
                f"""FLOW:
1. {TYPE_DETECTION_INSTRUCTIONS}

2. GET SUMMARY of their request:
   - Ask: "Can you give me a quick summary of what you're calling about so I can get you to the right person?"
   - Use record_request_summary after they explain

3. {format_collection_flow("record_business_other_info", "record_personal_other_info")}

4. CONFIRM AND TRANSFER:
   "Thanks, to confirm - you're calling about [summary] for [business name/your personal policy]. Let me connect you with your Account Executive who can help."
   Use transfer_to_account_executive.""",
                """RULES:
- One question at a time
- Context words are CLUES, not business names
- Listen carefully to their summary to capture the reason for the call
- If unclear, ask for clarification""",
                """EDGE CASES:
- Caller won't spell name: "No problem, can you tell me just the first letter of your last name?"
- Multiple topics: "I'll note all of that for your Account Executive. Which is most urgent?"
- Unclear response: Ask for clarification, don't assume""",
                """WARM TRANSFER CONTEXT:
When transferring, you'll relay:
- Caller's name
- What they're calling about (the summary)
- Insurance type (business/personal)
This helps the Account Executive prepare before taking the call.""",
                SECURITY_INSTRUCTIONS,
            ),
        )

    async def on_enter(self) -> None:
        """Called when this agent becomes active - start the catch-all flow.

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
                f"Something else: Business info already collected - {userdata.business_name}"
            )
            # Perform the routing logic (same as record_business_other_info)
            route_key = get_alpha_route_key(userdata.business_name)
            agent = find_agent_by_alpha(route_key, "CL", is_new_business=False)
            if agent:
                userdata.assigned_agent = agent["name"]
            userdata.call_intent = CallIntent.SOMETHING_ELSE

            # Generate response acknowledging and proceeding to transfer
            session.generate_reply(
                instructions=(
                    f"The caller has a request about their business '{userdata.business_name}'. "
                    "You already have their business info. Ask 'Can you give me a quick summary of what you're calling about?' "
                    "Use record_request_summary after they explain, then use transfer_to_account_executive."
                )
            )
        elif has_personal_identifier:
            # Personal info complete - set up routing and proceed to transfer
            logger.info(
                f"Something else: Personal info already collected - last name: {mask_name(userdata.last_name_spelled)}"
            )
            # Perform the routing logic (same as record_personal_other_info)
            first_letter = (
                userdata.last_name_spelled[0].upper()
                if userdata.last_name_spelled
                else "A"
            )
            agent = find_agent_by_alpha(first_letter, "PL", is_new_business=False)
            if agent:
                userdata.assigned_agent = agent["name"]
            userdata.call_intent = CallIntent.SOMETHING_ELSE

            # Generate response acknowledging and proceeding to transfer
            session.generate_reply(
                instructions=(
                    f"The caller has a request about their personal policy. Their last name is '{userdata.last_name_spelled}'. "
                    "You already have their info. Ask 'Can you give me a quick summary of what you're calling about?' "
                    "Use record_request_summary after they explain, then use transfer_to_account_executive."
                )
            )
        elif has_insurance_type and userdata.insurance_type == InsuranceType.BUSINESS:
            # Know it's business but missing business name
            logger.info("Something else: Know it's business, need business name")
            session.generate_reply(
                instructions=(
                    "The caller has a request about their BUSINESS policy. "
                    "Ask 'Can you give me a quick summary of what you're calling about?' then "
                    "'What is the name of the business?' "
                    "Use record_request_summary and record_business_other_info as they provide info."
                )
            )
        elif has_insurance_type and userdata.insurance_type == InsuranceType.PERSONAL:
            # Know it's personal but missing last name
            logger.info("Something else: Know it's personal, need last name")
            session.generate_reply(
                instructions=(
                    "The caller has a request about their PERSONAL policy. "
                    "Ask 'Can you give me a quick summary of what you're calling about?' then "
                    "'Can you spell your last name for me?' "
                    "Use record_request_summary and record_personal_other_info as they provide info."
                )
            )
        else:
            # No pre-collected info - use standard flow
            session.generate_reply(instructions=ON_ENTER_CHECK_CONTEXT_EXTENDED)

    @function_tool
    async def record_request_summary(
        self,
        context: RunContext[CallerInfo],
        summary: str,
    ) -> str:
        """Record a summary of what the caller is calling about.

        Call this tool after the caller explains what they need help with.

        Args:
            summary: A brief summary of the caller's request or reason for calling
        """
        context.userdata.additional_notes = summary
        context.userdata.call_intent = CallIntent.SOMETHING_ELSE
        logger.info(f"Recorded request summary: {summary[:100]}...")
        return f"Got it, I understand you're calling about {summary}. Let me get you to the right person."

    @function_tool
    async def record_business_other_info(
        self,
        context: RunContext[CallerInfo],
        business_name: str,
    ) -> str:
        """Record business insurance information for miscellaneous request.

        Call this tool after the caller provides their business name.

        Args:
            business_name: The name of the business
        """
        context.userdata.insurance_type = InsuranceType.BUSINESS
        context.userdata.business_name = business_name
        context.userdata.call_intent = CallIntent.SOMETHING_ELSE

        # Use staff directory routing for Commercial Lines
        # EXISTING clients go to Account Executives (is_new_business=False)
        route_key = get_alpha_route_key(business_name)
        agent = find_agent_by_alpha(route_key, "CL", is_new_business=False)

        if agent:
            context.userdata.assigned_agent = agent["name"]
            logger.info(
                f"Something else request - Business: {business_name} "
                f"(route key: {route_key}) -> {agent['name']} ext {agent['ext']}"
            )
            return f"Got it, I have this noted for {business_name}. Let me connect you with {agent['name']}, your Account Executive."
        else:
            logger.info(
                f"Something else request - Business: {business_name} (no agent found)"
            )
            return f"Got it, I have this noted for {business_name}. Let me connect you with your Account Executive."

    @function_tool
    async def record_personal_other_info(
        self,
        context: RunContext[CallerInfo],
        last_name_spelled: str,
    ) -> str:
        """Record personal insurance information for miscellaneous request with spelled last name.

        Call this tool after the caller spells their last name.

        Args:
            last_name_spelled: The caller's last name as they spelled it out letter by letter
        """
        context.userdata.insurance_type = InsuranceType.PERSONAL
        context.userdata.last_name_spelled = last_name_spelled
        context.userdata.call_intent = CallIntent.SOMETHING_ELSE

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
                f"Something else request - Personal, last name: {mask_name(last_name_spelled)} "
                f"(letter: {first_letter}) -> {agent['name']} ext {agent['ext']}"
            )
            return f"Thank you, I have that as {last_name_spelled}. Let me connect you with {agent['name']}, your Account Executive."
        else:
            logger.info(
                f"Something else request - Personal, last name: {mask_name(last_name_spelled)} (no agent found)"
            )
            return f"Thank you, I have that as {last_name_spelled}. Let me connect you with your Account Executive."

    @function_tool
    async def transfer_to_account_executive(
        self,
        context: RunContext[CallerInfo],
    ) -> str:
        """Transfer the caller to their Account Executive with warm transfer context.

        Call this after recording the caller's information to initiate the transfer.
        For business insurance, uses CL alpha-split routing to Account Executives.
        For personal insurance, uses PL alpha-split routing to Account Executives.

        This is a WARM TRANSFER - the caller's summary is relayed to the Account Executive.
        """
        userdata = context.userdata

        if userdata.insurance_type == InsuranceType.BUSINESS:
            # Business insurance - route via CL alpha-split to Account Executive
            agent_name = userdata.assigned_agent
            if agent_name:
                agent = get_agent_by_name(agent_name)
                if agent:
                    logger.info(
                        f"Transferring other request to {agent['name']} ext {agent['ext']}"
                    )
                    return await self._initiate_transfer(context, agent)
            # Fallback if no agent assigned
            logger.info(
                "Transferring other request - no agent assigned, using fallback"
            )
            return await self._handle_fallback(context, None)

        elif userdata.insurance_type == InsuranceType.PERSONAL:
            # Personal insurance - route via PL alpha-split to Account Executive
            agent_name = userdata.assigned_agent
            if agent_name:
                agent = get_agent_by_name(agent_name)
                if agent:
                    logger.info(
                        f"Transferring other request to {agent['name']} ext {agent['ext']}"
                    )
                    return await self._initiate_transfer(context, agent)
                else:
                    # Agent unavailable - use fallback
                    return await self._handle_fallback(context, agent_name)
            else:
                # No agent assigned - use fallback
                return await self._handle_fallback(context, None)

        return "I'll connect you with your Account Executive who can help."

    async def _initiate_transfer(
        self, context: RunContext[CallerInfo], agent: dict
    ) -> str:
        """Initiate the warm transfer to an agent with context relay.

        This overrides the base class method to add warm transfer context
        relay before the standard transfer behavior.

        Args:
            context: The run context containing caller information.
            agent: Staff directory entry with name, ext, department, etc.

        Returns:
            Transfer message with hold instructions.
        """
        # Relay warm transfer context before initiating the transfer
        await self._relay_warm_transfer_context(context, agent)

        # Call the base class transfer implementation
        return await super()._initiate_transfer(context, agent)

    async def _relay_warm_transfer_context(
        self, context: RunContext[CallerInfo], agent: dict
    ) -> None:
        """Relay conversation context to the receiving agent for warm transfer.

        This logs the context that would be relayed to the receiving agent
        before the call is connected. In production, this would be transmitted
        via SIP headers or a separate notification channel.

        Args:
            context: The run context containing caller information.
            agent: Staff directory entry with name, ext, department, etc.
        """
        agent_name = agent.get("name", "an agent") if isinstance(agent, dict) else agent

        # Get caller info for warm transfer context
        caller_name = context.userdata.name or "a caller"
        summary = context.userdata.additional_notes or "a general inquiry"

        # Log the warm transfer context that would be relayed
        # This is the intro the agent would hear before the call connects
        warm_transfer_intro = (
            f"Hi {agent_name}, I have {caller_name} on the line. "
            f"They're calling about {summary}."
        )
        logger.info(f"[WARM TRANSFER CONTEXT] {warm_transfer_intro}")

        # TODO: Implement actual warm transfer context relay via SIP
