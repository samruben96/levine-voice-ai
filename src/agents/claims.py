"""Claims Agent for the Harry Levine Insurance Voice Agent.

This module contains the ClaimsAgent class which handles insurance claims
requests from callers, with different flows for business hours vs after-hours.
"""

import logging

from livekit.agents import Agent, RunContext, function_tool

from business_hours import is_office_open
from constants import HOLD_MESSAGE, get_carrier_claims_number
from instruction_templates import (
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

    NOTE: The Assistant expresses empathy BEFORE handing off to this agent.
    This agent should NOT repeat empathy phrases to avoid duplication.

    The agent handles claims differently based on whether the office is open:

    Business Hours Flow (Mon-Fri, 9 AM - 5 PM Eastern):
    1. Transfer to claims ring group immediately (empathy already expressed)

    After-Hours Flow:
    1. Explain team is not available (empathy already expressed)
    2. Inform caller they can find carrier claims number on policy documents
    3. If caller knows carrier: Look up and provide claims number
    4. If caller doesn't know carrier: Advise to check insurance card/documents
    5. Offer callback option
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
                "You are Aizellee, transferring a caller to the claims team.",
                """YOUR ONLY JOB:
1. Call transfer_to_claims IMMEDIATELY
2. Be silent after that - done.

The caller has already heard empathy from the receptionist. Do NOT say any empathy phrases.""",
                """RULES:
- Call the tool IMMEDIATELY - no speaking first
- Stay silent after tool call
- Never repeat empathy - it was already said""",
                SECURITY_INSTRUCTIONS,
            )
        else:
            instructions = compose_instructions(
                "You are Aizellee, helping a caller file a claim after hours.",
                "GOAL: Explain we're closed but help find their carrier's claims number. The caller already heard empathy from the receptionist - do NOT repeat it.",
                """TONE:
- Stay warm, caring, and supportive throughout (the caller had a distressing experience)
- Keep responses concise but human
- Even when asking practical questions, maintain a supportive tone""",
                """FLOW:
1. Start with ONLY this (no empathy - receptionist already said it):
   "Our office is closed, but I can help you reach your carrier's 24/7 claims line. Do you know which insurance carrier you're with?"

2. If YES: Use record_carrier_name to look up and provide the number.
   If NO: "You can find their claims number on your insurance card or policy documents."

3. Only if they ask: Offer callback option using request_callback.

NOTE: Do NOT ask "Are you okay?" - the receptionist already asked this. Jump straight to helping them.""",
                """CARRIER INFO:
- We have numbers for: Progressive, Travelers, Hartford, Liberty Mutual
- Unknown carrier: Direct them to check their insurance card""",
                """AVOID:
- Saying "I'm sorry to hear that" - already said by receptionist
- Repeating that we're closed
- Over-explaining the situation""",
                SECURITY_INSTRUCTIONS,
            )

        super().__init__(instructions=instructions)

    async def on_enter(self) -> None:
        """Called when this agent becomes active - start the claims flow."""
        if self._is_business_hours:
            await self.session.generate_reply(
                instructions="Call transfer_to_claims IMMEDIATELY. Do NOT say anything before calling the tool - empathy was already expressed by the receptionist."
            )
        else:
            await self.session.generate_reply(
                instructions="Say ONLY: 'Our office is closed, but I can help you reach your carrier's 24/7 claims line. Do you know which insurance carrier you're with?' Do NOT say empathy or ask if they're okay - that was already handled by the receptionist."
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
    ) -> None:
        """Transfer the caller to the claims department.

        Call this during business hours to connect the caller with the claims team.
        DO NOT say anything before calling this - the tool handles the transfer message.

        Returns None to signal the LLM to be silent after the transfer.
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

        # Speak the transfer message directly to avoid repetition
        transfer_message = (
            f"I'm connecting you with our claims team now. {HOLD_MESSAGE}"
        )
        await context.session.say(transfer_message, allow_interruptions=False)

        # TODO (Needs Client Input): What extension(s) handle claims during business hours?
        # For now, this is a placeholder that logs the transfer attempt.
        # In production, this would initiate actual SIP transfer.

        # Return None to signal completion - LLM should stay silent
        # (per LiveKit docs: return None for silent completion)

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
