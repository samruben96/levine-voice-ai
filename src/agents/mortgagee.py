"""Mortgagee/Certificate Agent for the Harry Levine Insurance Voice Agent.

This module contains the MortgageeCertificateAgent class which handles
certificate of insurance and mortgagee/lienholder requests from callers.
"""

import logging

from livekit.agents import Agent, RunContext, function_tool

from constants import HOLD_MESSAGE
from instruction_templates import (
    SECURITY_INSTRUCTIONS,
    compose_instructions,
)
from models import CallerInfo, CallIntent, InsuranceType
from staff_directory import (
    find_agent_by_alpha,
    get_alpha_route_key,
)
from utils import format_email_for_speech, mask_name

logger = logging.getLogger("agent")


class MortgageeCertificateAgent(Agent):
    """Specialized agent for handling certificate of insurance and mortgagee requests.

    This agent is handed off to when the caller needs:
    - Certificate of insurance (COI)
    - Mortgagee/lienholder information updates
    - Proof of insurance for contractors/vendors
    - Loss payee information

    Certificate Flow:
    - NEW certificate: Provide email (Certificate@hlinsure.com)
    - EXISTING certificate question: Transfer to Account Executive via alpha-split

    Mortgagee Flow:
    1. Inform about email requirement (info@hlinsure.com)
    2. Offer additional help

    This agent handles BOTH certificate and mortgagee requests - it determines
    which type from context and routes to the appropriate flow.
    """

    def __init__(self, request_type: str = "unknown", chat_ctx=None) -> None:
        """Initialize MortgageeCertificateAgent.

        Args:
            request_type: Either "certificate", "mortgagee", or "unknown".
                         Used to customize initial response.
            chat_ctx: Optional chat context from the parent agent handoff.
                     Preserves conversation history across agent transitions.
        """
        self._request_type = request_type
        super().__init__(
            instructions=compose_instructions(
                "You are Aizellee, helping a caller with a certificate of insurance or mortgagee/lienholder request.",
                "GOAL: Handle certificate and mortgagee requests efficiently.",
                """KEY INFORMATION:
- Certificates are for COMMERCIAL insurance only
- Certificate requests email: Certificate@hlinsure.com
- Mortgagee requests email: info@hlinsure.com""",
                """CERTIFICATE REQUEST FLOW:
1. First ask: "Is this for a new certificate request, or do you have a question about an existing certificate?"
2. NEW CERTIFICATE: Use check_certificate_type tool with is_new_certificate=True to provide the email (Certificate@hlinsure.com)
3. EXISTING CERTIFICATE: Say "No problem, let me get you over to an agent that can help you with that."
   Then collect insurance type and identifier using record_caller_info, and transfer using transfer_existing_certificate.""",
                """MORTGAGEE/LIENHOLDER REQUEST FLOW:
1. INFORM about email requirement:
   "Got it. HLI requires all mortgagee requests to be sent in writing to info@hlinsure.com."
   Use provide_mortgagee_email_info tool.

2. OFFER additional help:
   "Is there anything else I can help you with today?" """,
                """RULES:
- Be helpful and informative
- Certificates are commercial only - no need to ask business/personal
- For NEW certificate requests: provide email only
- For EXISTING certificate questions: transfer to Account Executive
- Provide email addresses clearly""",
                SECURITY_INSTRUCTIONS,
            ),
            chat_ctx=chat_ctx,
        )

    async def on_enter(self) -> None:
        """Called when this agent becomes active - start the appropriate flow."""
        userdata: CallerInfo = self.session.userdata

        # Check if speech was already delivered by Assistant during handoff
        if getattr(userdata, "_handoff_speech_delivered", False):
            # Reset flag to prevent affecting future interactions
            userdata._handoff_speech_delivered = False

            # Skip the "I can help you with that" acknowledgment - go straight to info
            if self._request_type == "certificate":
                await self.session.generate_reply(
                    instructions="Ask the caller: 'Is this for a new certificate request, or do you have a question about an existing certificate?' Based on their answer, use check_certificate_type with is_new_certificate=True for new requests, or for existing certificate questions say 'No problem, let me get you over to an agent that can help you with that.' and collect their info for transfer."
                )
            elif self._request_type == "mortgagee":
                await self.session.generate_reply(
                    instructions="Use the provide_mortgagee_email_info tool immediately to provide the email requirement (info@hlinsure.com). Do NOT say 'I can help you with that' - just provide the information directly."
                )
            else:
                # Unknown type - still ask to clarify
                await self.session.generate_reply(
                    instructions="Ask to clarify whether they need a certificate of insurance or have a mortgagee/lienholder request. Based on their answer, use the appropriate tool."
                )
        else:
            # Original flow - include acknowledgment
            if self._request_type == "certificate":
                await self.session.generate_reply(
                    instructions="Acknowledge the caller's certificate request briefly, then ask: 'Is this for a new certificate request, or do you have a question about an existing certificate?' Based on their answer, use check_certificate_type with is_new_certificate=True for new requests, or for existing certificate questions say 'No problem, let me get you over to an agent that can help you with that.' and collect their info for transfer."
                )
            elif self._request_type == "mortgagee":
                # For mortgagee, acknowledge and provide email info
                await self.session.generate_reply(
                    instructions="Acknowledge the caller's request briefly, then inform them about the email requirement (info@hlinsure.com) using the provide_mortgagee_email_info tool, then ask if there's anything else you can help with. Example: 'I can help you with that.'"
                )
            else:
                # Unknown type - ask to clarify
                await self.session.generate_reply(
                    instructions="Acknowledge the caller briefly, then ask to clarify whether they need a certificate of insurance or have a mortgagee/lienholder request. Based on their answer, use the appropriate tool."
                )

    @function_tool
    async def check_certificate_type(
        self,
        context: RunContext[CallerInfo],
        is_new_certificate: bool,
    ) -> str:
        """Handle certificate request based on whether it's new or existing.

        Call this when a caller has indicated whether they need a new certificate
        or have a question about an existing one.

        Args:
            is_new_certificate: True if caller needs a NEW certificate issued,
                              False if calling about an EXISTING certificate (issue, question, update)
        """
        context.userdata.call_intent = CallIntent.CERTIFICATES

        if is_new_certificate:
            logger.info("Certificate request - NEW certificate, providing email info")
            cert_email = format_email_for_speech("Certificate@hlinsure.com")
            return (
                f"You can email your certificate request to {cert_email} "
                "You can also issue your own certificates through the portal on our website at "
                "harry levine insurance dot com. "
                "Is there anything else I can help you with today?"
            )
        else:
            logger.info(
                "Certificate request - EXISTING certificate, transferring to AE"
            )
            return (
                "No problem, let me get you over to an agent that can help you with that. "
                "What is the name of the business on the certificate?"
            )

    @function_tool
    async def record_caller_info(
        self,
        context: RunContext[CallerInfo],
        insurance_type: str,
        identifier: str,
    ) -> str:
        """Record caller information for existing certificate transfer.

        Call this after collecting insurance type and identifier.

        Args:
            insurance_type: Either "business" or "personal"
            identifier: For business: the business name. For personal: the spelled last name.
        """
        if insurance_type.lower() == "business":
            context.userdata.insurance_type = InsuranceType.BUSINESS
            context.userdata.business_name = identifier
            logger.info(f"Certificate - recorded business: {mask_name(identifier)}")
        else:
            context.userdata.insurance_type = InsuranceType.PERSONAL
            context.userdata.last_name_spelled = identifier
            logger.info(f"Certificate - recorded personal: {mask_name(identifier)}")

        return "Got it. Let me connect you with your Account Executive now."

    @function_tool
    async def transfer_existing_certificate(
        self,
        context: RunContext[CallerInfo],
    ) -> str:
        """Transfer caller to Account Executive for existing certificate issues.

        REQUIREMENTS: record_caller_info must be called first to set insurance_type
        and identifier (business_name or last_name_spelled).

        Routes to Account Executives via alpha-split:
        - Business (CL): A-L -> Adriana, M-Z -> Rayvon
        - Personal (PL): A-G -> Yarislyn, H-M -> Al, N-Z -> Louis
        """
        userdata = context.userdata

        # Validate requirements
        if not userdata.insurance_type:
            return "I need to know if this is for business or personal insurance first."

        if (
            userdata.insurance_type == InsuranceType.BUSINESS
            and not userdata.business_name
        ):
            return "I need the name of your business before I can connect you."

        if (
            userdata.insurance_type == InsuranceType.PERSONAL
            and not userdata.last_name_spelled
        ):
            return "I need you to spell your last name for me before I can connect you."

        # Determine routing
        if userdata.insurance_type == InsuranceType.BUSINESS:
            department = "CL"
            route_key = get_alpha_route_key(userdata.business_name or "")
            identifier = userdata.business_name
        else:
            department = "PL"
            route_key = (
                userdata.last_name_spelled[0].upper()
                if userdata.last_name_spelled
                else "A"
            )
            identifier = userdata.last_name_spelled

        # Find the Account Executive (existing client, so is_new_business=False)
        agent = find_agent_by_alpha(route_key, department, is_new_business=False)

        if not agent:
            logger.warning(
                f"No agent found for certificate transfer: key={route_key}, dept={department}"
            )
            return (
                "I apologize, but I'm having trouble connecting you right now. "
                "Can you please hold while I find someone to help?"
            )

        agent_name = agent.get("pronunciation", agent.get("name", "an agent"))
        agent_ext = agent.get("ext", "unknown")

        logger.info(
            f"[MOCK TRANSFER] Certificate transfer to {agent_name} (ext {agent_ext}) "
            f"for {department} client: {mask_name(identifier) if identifier else 'unknown'}"
        )

        userdata.assigned_agent = agent_name
        userdata.additional_notes = "Existing certificate issue"

        return f"I'm connecting you with {agent_name} now. {HOLD_MESSAGE}"

    @function_tool
    async def provide_mortgagee_email_info(
        self,
        context: RunContext[CallerInfo],
    ) -> str:
        """Provide mortgagee/lienholder request email information.

        Call this tool when the caller has a mortgagee, lienholder, loss payee,
        or mortgage clause request.
        """
        context.userdata.call_intent = CallIntent.MORTGAGEE_LIENHOLDERS
        logger.info("Mortgagee request - provided email info")
        info_email = format_email_for_speech("info@hlinsure.com")
        return (
            f"HLI requires all mortgagee and lienholder requests to be sent in writing. "
            f"The email address is {info_email} "
            "Would you like me to repeat that, or is there anything else I can help you with today?"
        )
