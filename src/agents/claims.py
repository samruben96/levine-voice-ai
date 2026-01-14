"""Claims Agent for the Harry Levine Insurance Voice Agent.

This module contains the ClaimsAgent class which handles insurance claims
requests from callers, with different flows for business hours vs after-hours.
"""

import logging

from livekit.agents import Agent, RunContext, function_tool

from business_hours import is_office_open
from constants import HOLD_MESSAGE, get_carrier_claims_number
from instruction_templates import (
    EMPATHY_CLAIMS,
    SECURITY_INSTRUCTIONS,
    compose_instructions,
)
from models import CallerInfo, CallIntent
from utils import mask_name, mask_phone

logger = logging.getLogger("agent")


class ClaimsAgent(Agent):
    """Specialized agent for handling insurance claims requests.

    This agent is handed off to when the caller needs to:
    - File a new claim
    - Report an accident, theft, damage, or other loss
    - Get help with the claims process

    The agent handles claims differently based on whether the office is open:

    Business Hours Flow (Mon-Fri, 9 AM - 5 PM Eastern):
    1. Show empathy about the situation
    2. Transfer to claims ring group

    After-Hours Flow:
    1. Show empathy and explain team is not available
    2. Inform caller they can find carrier claims number on policy documents
    3. If caller knows carrier: Look up and provide claims number
    4. If caller doesn't know carrier: Advise to check insurance card/documents
    5. Offer callback option

    The agent prioritizes empathy as callers filing claims are often stressed
    or have experienced something traumatic (accident, theft, fire, etc.).
    """

    def __init__(self, is_business_hours: bool | None = None) -> None:
        """Initialize ClaimsAgent.

        Args:
            is_business_hours: Override for business hours check (for testing).
                             If None, uses actual time check.
        """
        # Determine if office is open (allows override for testing)
        self._is_business_hours = (
            is_business_hours if is_business_hours is not None else is_office_open()
        )

        if self._is_business_hours:
            instructions = compose_instructions(
                "You are Aizellee, helping a caller who needs to file a claim.",
                "GOAL: Show empathy and transfer them to the claims team.",
                EMPATHY_CLAIMS,
                """FLOW:
1. ACKNOWLEDGE with sincere empathy:
   - "I'm so sorry to hear that. Let me get you over to our claims team right away."
   - If they mention injury/accident: "I'm so sorry. First, are you okay?"

2. TRANSFER to claims team:
   - Use transfer_to_claims to connect them with our claims department""",
                """RULES:
- Empathy first, business second
- Don't ask unnecessary questions - just get them to claims team
- If they want to explain, listen briefly and acknowledge""",
                """EXAMPLES:
- "Car accident" -> "I'm so sorry to hear about the accident. Are you okay? Let me connect you with our claims team."
- "House was broken into" -> "Oh no, I'm so sorry. That must be very upsetting. Let me get you over to someone who can help." """,
                SECURITY_INSTRUCTIONS,
            )
        else:
            instructions = compose_instructions(
                "You are Aizellee, helping a caller who needs to file a claim after hours.",
                "GOAL: Show empathy and help them find their insurance carrier's claims number.",
                EMPATHY_CLAIMS.replace(
                    "Don't rush them",
                    "Be understanding that they're calling after hours\n- Don't rush them",
                ),
                """FLOW:
1. ACKNOWLEDGE with sincere empathy AND set expectations:
   - "I'm so sorry to hear that. Our team isn't in the office right now, but I can help you."
   - "Most claims should be filed directly with your insurance carrier, and you can find their 24/7 claims number on your policy documents or insurance card."

2. OFFER to help find carrier claims number:
   - Ask: "Do you know which insurance carrier you're with?"
   - If YES: Use record_carrier_name to look up and provide the claims number
   - If NO: Advise them to check their insurance card or policy documents

3. OFFER callback option:
   - If they want to speak with our team: "Our team will be back Monday through Friday, 9 AM to 5 PM. Would you like me to note your information for a callback?"
   - If YES: Use request_callback to collect their info""",
                """CARRIER LOOKUP:
- Common carriers we have numbers for: Progressive, Travelers, Hartford, Liberty Mutual
- If carrier not found: "I don't have that carrier's claims number in my system, but it should be on your insurance card or policy documents." """,
                """RULES:
- Empathy first, always
- Be helpful even though we can't transfer them
- Provide carrier claims number if we have it
- Offer callback as an option, not a requirement""",
                """EXAMPLES:
- "Car accident" -> "I'm so sorry about the accident. Are you okay? Our team isn't in right now, but your insurance carrier has a 24/7 claims line. Do you know which carrier you're with?"
- "House flooded" -> "Oh no, I'm so sorry to hear that. Our office is closed right now, but I can help you find your carrier's claims number. Do you know who your home insurance is through?" """,
                SECURITY_INSTRUCTIONS,
            )

        super().__init__(instructions=instructions)

    async def on_enter(self) -> None:
        """Called when this agent becomes active - start the claims flow."""
        if self._is_business_hours:
            self.session.generate_reply(
                instructions="Show empathy for their situation and offer to transfer them to the claims team. If they mentioned an accident or injury, ask if they're okay."
            )
        else:
            self.session.generate_reply(
                instructions="Show empathy for their situation, explain the office is closed, and offer to help them find their carrier's claims number. Ask if they know which insurance carrier they're with."
            )

    @function_tool
    async def record_carrier_name(
        self,
        context: RunContext[CallerInfo],
        carrier_name: str,
    ) -> str:
        """Look up and provide the claims phone number for an insurance carrier.

        Call this tool when the caller provides their insurance carrier name.
        This will look up the carrier's 24/7 claims number.

        Args:
            carrier_name: The name of the insurance carrier (e.g., "Progressive", "Travelers")
        """
        context.userdata.call_intent = CallIntent.CLAIMS
        context.userdata.additional_notes = f"Carrier: {carrier_name}"

        claims_number = get_carrier_claims_number(carrier_name)

        if claims_number:
            logger.info(
                f"Claims lookup - Found carrier {carrier_name}: {claims_number}"
            )
            return (
                f"I found it. The claims number for {carrier_name} is {claims_number}. "
                f"They have a 24/7 claims line, so you can call them right now to file your claim. "
                f"Is there anything else I can help you with?"
            )
        else:
            logger.info(f"Claims lookup - Carrier not found: {carrier_name}")
            return (
                f"I'm sorry, I don't have the claims number for {carrier_name} in my system. "
                f"You should be able to find their 24/7 claims number on your insurance card "
                f"or policy documents. Is there anything else I can help you with?"
            )

    @function_tool
    async def transfer_to_claims(
        self,
        context: RunContext[CallerInfo],
    ) -> str:
        """Transfer the caller to the claims department.

        Call this during business hours to connect the caller with the claims team.
        """
        context.userdata.call_intent = CallIntent.CLAIMS

        # Log the transfer attempt
        caller_name = context.userdata.name
        caller_phone = context.userdata.phone_number
        logger.info(
            f"[MOCK TRANSFER] Transferring claims call: "
            f"name={mask_name(caller_name) if caller_name else 'unknown'}, "
            f"phone={mask_phone(caller_phone) if caller_phone else 'unknown'}"
        )

        # TODO (Needs Client Input): What extension(s) handle claims during business hours?
        # For now, this is a placeholder that logs the transfer attempt.
        # In production, this would initiate actual SIP transfer.

        return f"I'm connecting you with our claims team now. {HOLD_MESSAGE}"

    @function_tool
    async def request_callback(
        self,
        context: RunContext[CallerInfo],
        caller_name: str,
        phone_number: str,
        brief_description: str = "",
    ) -> str:
        """Request a callback from the claims team during business hours.

        Call this when the caller wants to be called back instead of contacting
        their carrier directly.

        Args:
            caller_name: The caller's name for the callback
            phone_number: Phone number to call back
            brief_description: Brief description of the claim (optional)
        """
        context.userdata.name = caller_name
        context.userdata.phone_number = phone_number
        context.userdata.call_intent = CallIntent.CLAIMS
        if brief_description:
            context.userdata.additional_notes = (
                f"Claims callback requested: {brief_description}"
            )
        else:
            context.userdata.additional_notes = "Claims callback requested"

        logger.info(
            f"Claims callback requested: "
            f"name={mask_name(caller_name)}, "
            f"phone={mask_phone(phone_number)}, "
            f"description={brief_description or 'not provided'}"
        )

        return (
            f"I've noted your information, {caller_name}. "
            f"Our team will call you back at {phone_number} during business hours, "
            f"Monday through Friday, 9 AM to 5 PM. "
            f"Is there anything else I can help you with in the meantime?"
        )
