"""Mortgagee/Certificate Agent for the Harry Levine Insurance Voice Agent.

This module contains the MortgageeCertificateAgent class which handles
certificate of insurance and mortgagee/lienholder requests from callers.
"""

import logging

from livekit.agents import Agent, RunContext, function_tool

from instruction_templates import (
    SECURITY_INSTRUCTIONS,
    compose_instructions,
)
from models import CallerInfo, CallIntent
from staff_directory import get_ring_group

logger = logging.getLogger("agent")


class MortgageeCertificateAgent(Agent):
    """Specialized agent for handling certificate of insurance and mortgagee requests.

    This agent is handed off to when the caller needs:
    - Certificate of insurance (COI)
    - Mortgagee/lienholder information updates
    - Proof of insurance for contractors/vendors
    - Loss payee information

    IMPORTANT: This agent does NOT transfer to a person. It redirects callers to
    email/self-service options:
    - Certificate requests: Certificate@hlinsure.com
    - Mortgagee requests: info@hlinsure.com
    - Self-service: Harry Levine Insurance app for 24/7 certificate issuance

    Flow for Certificate Requests:
    1. Inform about email requirement (Certificate@hlinsure.com)
    2. Offer self-service option (HLI app)
    3. Offer login help if needed
    4. If login help needed -> Transfer to VA ring group or collect email

    Flow for Mortgagee Requests:
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
                "GOAL: Provide email/self-service information for their request - NO transfer to a person needed.",
                """KEY INFORMATION:
- Certificate requests email: Certificate@hlinsure.com
- Mortgagee requests email: info@hlinsure.com
- Self-service app: Harry Levine Insurance app (24/7 certificate issuance)""",
                """CERTIFICATE REQUEST FLOW:
1. INFORM about email requirement:
   "Thank you for reaching out. HLI requires all certificate requests to be sent in writing to Certificate@hlinsure.com."
   Use provide_certificate_email_info tool.

2. OFFER self-service option:
   "Did you know you can also issue your own certificates using the Harry Levine Insurance app 24/7?"

3. CHECK login status:
   "Do you know what your login information is, or do you need us to resend it?"
   Use check_login_status tool.

4. If they NEED login help:
   - Ask for their email: "What email address should we send your login credentials to?"
   - Use collect_email_for_credentials tool
   - OR use transfer_for_login_help to connect them with customer service""",
                """MORTGAGEE/LIENHOLDER REQUEST FLOW:
1. INFORM about email requirement:
   "Thank you for reaching out. HLI requires all mortgagee requests to be sent in writing to info@hlinsure.com."
   Use provide_mortgagee_email_info tool.

2. OFFER additional help:
   "Is there anything else I can help you with today?" """,
                """CERTIFICATE KEYWORDS (for context):
- "certificate of insurance", "COI", "certificate request"
- "need a certificate", "proof of insurance for"
- "certificate for a job", "general contractor needs certificate"
- "vendor certificate", "additional insured" """,
                """MORTGAGEE KEYWORDS (for context):
- "mortgagee", "lienholder", "mortgage company"
- "lender needs", "bank needs proof", "add mortgagee"
- "mortgagee change", "lien holder", "mortgage clause", "loss payee" """,
                """RULES:
- Be helpful and informative
- Provide email addresses clearly
- Encourage self-service option for certificates
- Only transfer for login help if they can't remember credentials""",
                """IMPORTANT:
- This flow does NOT require collecting business/personal info
- No alpha-split routing needed
- Email addresses are the primary solution""",
                SECURITY_INSTRUCTIONS,
            ),
        )

    async def on_enter(self) -> None:
        """Called when this agent becomes active - start the appropriate flow."""
        if self._request_type == "certificate":
            self.session.generate_reply(
                instructions="The caller needs a certificate of insurance. Start by informing them about the email requirement (Certificate@hlinsure.com) using the provide_certificate_email_info tool, then offer the self-service app option."
            )
        elif self._request_type == "mortgagee":
            self.session.generate_reply(
                instructions="The caller has a mortgagee or lienholder request. Inform them about the email requirement (info@hlinsure.com) using the provide_mortgagee_email_info tool, then ask if there's anything else you can help with."
            )
        else:
            # Unknown type - ask to clarify
            self.session.generate_reply(
                instructions="Ask the caller to clarify whether they need a certificate of insurance or have a mortgagee/lienholder request. Based on their answer, use the appropriate tool."
            )

    @function_tool
    async def provide_certificate_email_info(
        self,
        context: RunContext[CallerInfo],
    ) -> str:
        """Provide certificate of insurance email and self-service information.

        Call this tool when the caller needs a certificate of insurance (COI).
        This provides the email address and mentions the self-service app option.
        """
        context.userdata.call_intent = CallIntent.CERTIFICATES
        logger.info("Certificate request - provided email info and self-service option")
        return (
            "Thank you for reaching out. HLI requires all certificate requests to be sent in writing to "
            "Certificate@hlinsure.com. Did you know you can also issue your own certificates using the "
            "Harry Levine Insurance app 24/7? Do you know what your login information is, or do you need us to resend it?"
        )

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
        return (
            "Thank you for reaching out. HLI requires all mortgagee and lienholder requests to be sent in writing to "
            "info@hlinsure.com. Is there anything else I can help you with today?"
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
