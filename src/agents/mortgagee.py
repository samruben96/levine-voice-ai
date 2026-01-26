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
    get_ring_group,
)
from utils import format_email_for_speech

logger = logging.getLogger("agent")


class MortgageeCertificateAgent(Agent):
    """Specialized agent for handling certificate of insurance and mortgagee requests.

    This agent is handed off to when the caller needs:
    - Certificate of insurance (COI)
    - Mortgagee/lienholder information updates
    - Proof of insurance for contractors/vendors
    - Loss payee information

    Certificate Flow (COMMERCIAL ONLY):
    - For ALL certificate requests (new or existing): Provide email (Certificate@hlinsure.com)
      and self-service app option. No transfer needed.

    Mortgagee Flow:
    1. Inform about email requirement (info@hlinsure.com)
    2. Offer additional help

    This agent handles BOTH certificate and mortgagee requests - it determines
    which type from context and routes to the appropriate flow.
    """

    def __init__(self, request_type: str = "unknown") -> None:
        """Initialize MortgageeCertificateAgent.

        Args:
            request_type: Either "certificate", "mortgagee", or "unknown".
                         Used to customize initial response.
        """
        self._request_type = request_type
        super().__init__(
            instructions=compose_instructions(
                "You are Aizellee, helping a caller with a certificate of insurance or mortgagee/lienholder request.",
                "GOAL: Provide email and self-service options for certificate/mortgagee requests. No transfer needed.",
                """KEY INFORMATION:
- Certificates are for COMMERCIAL insurance only
- Certificate requests email: Certificate@hlinsure.com
- Mortgagee requests email: info@hlinsure.com
- Self-service app: Harry Levine Insurance app (24/7 certificate issuance)""",
                """CERTIFICATE REQUEST FLOW:
For ALL certificate requests (new or existing):
1. Provide email: Certificate@hlinsure.com
2. Offer self-service app option (Harry Levine Insurance app for 24/7 issuance)
3. Ask if they need help with login credentials
4. No transfer needed for any certificate request

Use check_certificate_type or handle_new_certificate tool to provide this info.""",
                """MORTGAGEE/LIENHOLDER REQUEST FLOW:
1. INFORM about email requirement:
   "Got it. HLI requires all mortgagee requests to be sent in writing to info@hlinsure.com."
   Use provide_mortgagee_email_info tool.

2. OFFER additional help:
   "Is there anything else I can help you with today?" """,
                """RULES:
- Be helpful and informative
- Certificates are commercial only - no need to ask business/personal
- For ALL certificate requests: provide email + self-service app info
- No transfer needed for certificate requests
- Provide email addresses clearly
- Encourage self-service option""",
                SECURITY_INSTRUCTIONS,
            ),
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
                    instructions="Use the handle_new_certificate tool immediately to provide the email (Certificate@hlinsure.com) and self-service app option. Do NOT say 'I can help you with that' - just provide the information directly."
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
                # For certificates, acknowledge and provide email + self-service info directly
                await self.session.generate_reply(
                    instructions="Acknowledge the caller's certificate request briefly, then use the handle_new_certificate tool to provide the email (Certificate@hlinsure.com) and self-service app option. Example: 'I can help you with that.'"
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
        """Handle certificate request - provides email and self-service info for ALL certificate requests.

        Call this when a caller mentions certificates. Both new and existing certificate
        requests get the same response: email + self-service app info.

        Args:
            is_new_certificate: True if caller needs a NEW certificate issued,
                              False if calling about an EXISTING certificate (issue, question, update)
        """
        context.userdata.call_intent = CallIntent.CERTIFICATES

        cert_type = "NEW" if is_new_certificate else "EXISTING"
        logger.info(
            f"Certificate request - {cert_type} certificate, providing email/self-service info"
        )
        cert_email = format_email_for_speech("Certificate@hlinsure.com")
        return (
            f"All certificates need to be requested in writing. You can email them to "
            f"{cert_email} Or issue them 24/7 using the Harry Levine Insurance app. "
            "Do you know your login information, or do you need us to resend it?"
        )

    @function_tool
    async def handle_new_certificate(
        self,
        context: RunContext[CallerInfo],
    ) -> str:
        """Provide information for requesting a NEW certificate.

        Call this when caller confirms they need a NEW certificate issued.
        Provides the email address and self-service app option.
        """
        context.userdata.call_intent = CallIntent.CERTIFICATES
        logger.info(
            "Certificate request - NEW certificate, providing email/self-service info"
        )
        cert_email = format_email_for_speech("Certificate@hlinsure.com")
        return (
            f"All certificates need to be requested in writing. You can email them to "
            f"{cert_email} Or issue them 24/7 using the Harry Levine Insurance app. "
            "Do you know your login information, or do you need us to resend it?"
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
            logger.info(f"Certificate - recorded business: {identifier}")
        else:
            context.userdata.insurance_type = InsuranceType.PERSONAL
            context.userdata.last_name_spelled = identifier
            logger.info(f"Certificate - recorded personal, last name: {identifier}")

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
        - Business (CL): A-F -> Adriana, G-O -> Rayvon, P-Z -> Dionna
        - Personal (PL): A-G -> Yarislyn, H-M -> Al, N-Z -> Luis
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

        agent_name = agent.get("name", "an agent")
        agent_ext = agent.get("ext", "unknown")

        logger.info(
            f"[MOCK TRANSFER] Certificate transfer to {agent_name} (ext {agent_ext}) "
            f"for {department} client: {identifier}"
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
            f"Got it. HLI requires all mortgagee and lienholder requests to be sent in writing to "
            f"{info_email} Is there anything else I can help you with today?"
        )

    @function_tool
    async def check_login_status(
        self,
        context: RunContext[CallerInfo],
        knows_login: bool,
    ) -> str:
        """Check if the caller knows their app login credentials.

        Call this tool after asking if they know their login information.

        Args:
            knows_login: True if the caller knows their login, False if they need help
        """
        if knows_login:
            logger.info("Certificate request - caller knows login, can self-service")
            return (
                "Great! You can log into the Harry Levine Insurance app to issue your certificate right away. "
                "Is there anything else I can help you with today?"
            )
        else:
            logger.info("Certificate request - caller needs login help")
            return (
                "No problem, I can help with that. Would you like me to have your login credentials resent to your email, "
                "or would you prefer to speak with someone from our customer service team?"
            )

    @function_tool
    async def collect_email_for_credentials(
        self,
        context: RunContext[CallerInfo],
        email_address: str,
    ) -> str:
        """Collect the caller's email address to resend app credentials.

        Call this tool when the caller wants their login credentials resent.

        Args:
            email_address: The email address to send credentials to
        """
        context.userdata.additional_notes = (
            f"Resend app credentials to: {email_address}"
        )
        logger.info(
            f"Certificate request - collecting email for credential resend: {email_address[:3]}***"
        )
        return (
            f"Perfect, I'll have your login credentials sent to {email_address}. "
            "You should receive them shortly. Once you're logged in, you'll be able to issue your own certificates "
            "24/7 through the app. Is there anything else I can help you with today?"
        )

    @function_tool
    async def transfer_for_login_help(
        self,
        context: RunContext[CallerInfo],
    ) -> str:
        """Transfer the caller to the VA ring group for login assistance.

        Call this tool when the caller wants to speak with someone about their login.
        This transfers to the customer service team (VA ring group).
        """
        context.userdata.additional_notes = "Needs help with app login credentials"

        # Try VA ring group for login help
        va_group = get_ring_group("VA")
        if va_group:
            logger.info(
                f"[MOCK TRANSFER] Transferring for login help to VA ring group: {va_group['extensions']}"
            )
            return (
                "I'm connecting you with our customer service team who can help you with your login. "
                "Please hold for just a moment."
            )

        # Fallback message if no ring group configured
        logger.info("Certificate request - no VA ring group available for login help")
        return (
            "I apologize, but our customer service team is currently unavailable. "
            "Please email info@hlinsure.com and they'll help you reset your login credentials. "
            "Is there anything else I can help you with?"
        )
