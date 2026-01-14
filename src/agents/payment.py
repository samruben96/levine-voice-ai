"""Payment/ID-Dec Agent for the Harry Levine Insurance Voice Agent.

This module contains the PaymentIDDecAgent class which handles payment
and document (ID cards, declarations pages) requests from callers.
"""

import logging
from typing import TYPE_CHECKING

from livekit.agents import Agent, RunContext, function_tool

from instruction_templates import (
    EDGE_CASES_PAYMENT,
    ON_ENTER_CHECK_CONTEXT,
    SECURITY_INSTRUCTIONS,
    TYPE_DETECTION_INSTRUCTIONS,
    compose_instructions,
    format_collection_flow,
)
from models import CallerInfo, CallIntent, InsuranceType
from staff_directory import find_agent_by_alpha, get_alpha_route_key, get_ring_group
from utils import mask_name

if TYPE_CHECKING:
    from livekit.agents import AgentSession

logger = logging.getLogger("agent")


class PaymentIDDecAgent(Agent):
    """Specialized agent for handling payment and document requests.

    This agent is handed off to when the caller indicates they want to:
    - Make a payment on their policy
    - Request ID cards or proof of insurance
    - Request declarations page / dec page

    It follows the specific flow:
    1. Confirm insurance type (business vs personal)
    2. Collect appropriate information based on type
    3. Route to VA ring group first, then fallback to Account Executives
    """

    def __init__(self) -> None:
        super().__init__(
            instructions=compose_instructions(
                "You are Aizellee, helping a caller with a payment or document request.",
                "GOAL: Collect info to route them to the right team member.",
                f"""FLOW:
1. {TYPE_DETECTION_INSTRUCTIONS}

2. {format_collection_flow("record_business_payment_info", "record_personal_payment_info")}

3. CONFIRM AND TRANSFER:
   "Thanks [name], to confirm - you need [payment/ID card/dec page] for [business name/personal insurance]. Let me connect you."
   Use transfer_payment_request.""",
                """RULES:
- One question at a time
- Pay attention to context clues from earlier conversation
- If unclear, ask for clarification""",
                EDGE_CASES_PAYMENT,
                SECURITY_INSTRUCTIONS,
            ),
        )

    async def on_enter(self) -> None:
        """Called when this agent becomes active - start the payment/doc flow.

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
                f"Payment/ID-Dec: Business info already collected - {userdata.business_name}"
            )
            # Perform the routing logic (same as record_business_payment_info)
            route_key = get_alpha_route_key(userdata.business_name)
            agent = find_agent_by_alpha(route_key, "CL", is_new_business=False)
            if agent:
                userdata.assigned_agent = agent["name"]
            userdata.call_intent = CallIntent.MAKE_PAYMENT

            # Generate response acknowledging and proceeding to transfer
            session.generate_reply(
                instructions=(
                    f"The caller needs payment or document help for their business '{userdata.business_name}'. "
                    "You already have their info. Confirm what they need (payment/ID card/dec page), "
                    "then use transfer_payment_request to connect them."
                )
            )
        elif has_personal_identifier:
            # Personal info complete - set up routing and proceed to transfer
            logger.info(
                f"Payment/ID-Dec: Personal info already collected - last name: {mask_name(userdata.last_name_spelled)}"
            )
            # Perform the routing logic (same as record_personal_payment_info)
            first_letter = (
                userdata.last_name_spelled[0].upper()
                if userdata.last_name_spelled
                else "A"
            )
            agent = find_agent_by_alpha(first_letter, "PL", is_new_business=False)
            if agent:
                userdata.assigned_agent = agent["name"]
            userdata.call_intent = CallIntent.MAKE_PAYMENT

            # Generate response acknowledging and proceeding to transfer
            session.generate_reply(
                instructions=(
                    f"The caller needs payment or document help for their personal policy. Their last name is '{userdata.last_name_spelled}'. "
                    "You already have their info. Confirm what they need (payment/ID card/dec page), "
                    "then use transfer_payment_request to connect them."
                )
            )
        elif has_insurance_type and userdata.insurance_type == InsuranceType.BUSINESS:
            # Know it's business but missing business name
            logger.info("Payment/ID-Dec: Know it's business, need business name")
            session.generate_reply(
                instructions=(
                    "The caller needs payment or document help for their BUSINESS policy. "
                    "Ask 'What is the name of the business?' Use record_business_payment_info "
                    "after they provide it."
                )
            )
        elif has_insurance_type and userdata.insurance_type == InsuranceType.PERSONAL:
            # Know it's personal but missing last name
            logger.info("Payment/ID-Dec: Know it's personal, need last name")
            session.generate_reply(
                instructions=(
                    "The caller needs payment or document help for their PERSONAL policy. "
                    "Ask 'Can you spell your last name for me?' Use record_personal_payment_info "
                    "after they spell it."
                )
            )
        else:
            # No pre-collected info - use standard flow
            session.generate_reply(instructions=ON_ENTER_CHECK_CONTEXT)

    @function_tool
    async def record_business_payment_info(
        self,
        context: RunContext[CallerInfo],
        business_name: str,
    ) -> str:
        """Record business insurance payment/document request information.

        Call this tool after the caller provides their business name.

        Args:
            business_name: The name of the business making the request
        """
        context.userdata.insurance_type = InsuranceType.BUSINESS
        context.userdata.business_name = business_name
        context.userdata.call_intent = CallIntent.MAKE_PAYMENT

        # Use staff directory routing for Commercial Lines
        route_key = get_alpha_route_key(business_name)
        agent = find_agent_by_alpha(route_key, "CL", is_new_business=False)

        if agent:
            context.userdata.assigned_agent = agent["name"]
            logger.info(
                f"Payment/ID-Dec request - Business: {business_name} "
                f"(route key: {route_key}) -> {agent['name']} ext {agent['ext']}"
            )
            return f"Got it, I have this noted for {business_name}. Let me connect you with someone who can help."
        else:
            logger.info(
                f"Payment/ID-Dec request - Business: {business_name} (no agent found)"
            )
            return f"Got it, I have this noted for {business_name}. Let me connect you with our customer service team."

    @function_tool
    async def record_personal_payment_info(
        self,
        context: RunContext[CallerInfo],
        last_name_spelled: str,
    ) -> str:
        """Record personal insurance payment/document request information.

        Call this tool after the caller spells their last name.

        Args:
            last_name_spelled: The caller's last name as they spelled it out letter by letter
        """
        context.userdata.insurance_type = InsuranceType.PERSONAL
        context.userdata.last_name_spelled = last_name_spelled
        context.userdata.call_intent = CallIntent.MAKE_PAYMENT

        # Use staff directory routing for Personal Lines (existing client -> Account Executives)
        first_letter = (
            last_name_spelled[0].upper()
            if last_name_spelled and len(last_name_spelled) > 0
            else "A"
        )
        agent = find_agent_by_alpha(first_letter, "PL", is_new_business=False)

        if agent:
            context.userdata.assigned_agent = agent["name"]
            logger.info(
                f"Payment/ID-Dec request - Personal, last name: {mask_name(last_name_spelled)} "
                f"(letter: {first_letter}) -> {agent['name']} ext {agent['ext']}"
            )
            return f"Thank you, I have that as {last_name_spelled}. Let me connect you with someone who can help."
        else:
            logger.info(
                f"Payment/ID-Dec request - Personal, last name: {mask_name(last_name_spelled)} (no agent found)"
            )
            return f"Thank you, I have that as {last_name_spelled}. Let me connect you with our customer service team."

    @function_tool
    async def transfer_payment_request(
        self,
        context: RunContext[CallerInfo],
    ) -> str:
        """Transfer the caller for payment or document request.

        Call this after recording the caller's information to initiate the transfer.
        Priority: VA ring group first, then fallback to Account Executives.
        """
        return await self._transfer_payment_request(context)

    async def _transfer_payment_request(self, context: RunContext[CallerInfo]) -> str:
        """Transfer payment/ID-Dec request with VA ring group priority.

        Priority:
        1. Try VA ring group first
        2. Fall back to Account Executives using alpha-split
        """
        userdata = context.userdata

        # Try VA ring group first
        va_group = get_ring_group("VA")
        if va_group:
            logger.info(
                f"[MOCK TRANSFER] Attempting VA ring group: {va_group['extensions']}"
            )
            # In production, would try ring group and check for answer
            # For now, simulate successful VA transfer
            return "I'm connecting you with our customer service team now."

        # Fallback to Account Executives using alpha-split
        if userdata.insurance_type == InsuranceType.PERSONAL:
            first_letter = (
                userdata.last_name_spelled[0].upper()
                if userdata.last_name_spelled and len(userdata.last_name_spelled) > 0
                else "A"
            )
            agent = find_agent_by_alpha(
                first_letter, "PL", is_new_business=False
            )  # Existing client
        elif userdata.insurance_type == InsuranceType.BUSINESS:
            route_key = get_alpha_route_key(userdata.business_name or "")
            agent = find_agent_by_alpha(route_key, "CL", is_new_business=False)
        else:
            agent = None

        if agent:
            logger.info(
                f"[MOCK TRANSFER] Fallback to Account Executive: "
                f"{agent['name']} ext {agent['ext']}"
            )
            return (
                f"I'm connecting you with {agent['name']} who can help you with that."
            )

        return "I'm connecting you with someone who can help you with that."
