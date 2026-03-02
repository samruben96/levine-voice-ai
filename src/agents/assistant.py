"""Main Assistant Agent for the Harry Levine Insurance Voice Agent.

This module contains the Assistant class which is the main front-desk
receptionist that handles initial call intake and routes to specialized
sub-agents based on caller intent.
"""

import logging

from livekit.agents import Agent, RunContext, ToolError, function_tool

from agents.after_hours import AfterHoursAgent
from agents.claims import ClaimsAgent
from agents.mortgagee import MortgageeCertificateAgent
from business_hours import (
    format_business_hours_prompt,
    get_next_open_time,
    is_lunch_hour,
    is_office_open,
)
from constants import HOLD_MESSAGE
from instruction_templates import (
    ASSISTANT_DTMF_NOTE,
    ASSISTANT_EDGE_CASES,
    ASSISTANT_IDENTITY,
    ASSISTANT_INSURANCE_TYPE_DETECTION,
    ASSISTANT_OFFICE_INFO,
    ASSISTANT_OFFICE_STATUS_GATE,
    ASSISTANT_OUTPUT_RULES,
    ASSISTANT_PERSONALITY,
    ASSISTANT_ROUTING_REFERENCE,
    ASSISTANT_SPECIAL_NOTES,
    ASSISTANT_STANDARD_FLOW,
    ASSISTANT_TONE_GUIDANCE,
    CAPABILITY_BOUNDARIES,
    SECURITY_INSTRUCTIONS_EXTENDED,
    UNCERTAINTY_HANDLING,
    compose_instructions,
)
from models import CallerInfo, CallIntent, InsuranceType
from staff_directory import (
    find_agent_by_alpha,
    find_pl_sales_agent_with_fallback,
    get_agent_by_name,
    get_agents_by_department,
    get_agents_by_name_prefix,
    get_alpha_route_key,
    get_bilingual_agents,
    get_ring_group,
    is_agent_available,
    is_transferable,
)
from utils import format_email_for_speech, log_route_decision, mask_name, mask_phone

logger = logging.getLogger("agent")


class Assistant(Agent):
    """Main front-desk receptionist agent for Harry Levine Insurance.

    This agent handles initial call intake, detects caller intent, and routes
    to specialized sub-agents via handoffs. It serves as the entry
    point for all incoming calls.

    The Assistant:
    - Delivers appropriate greeting based on business hours
    - Collects basic caller information (name, phone)
    - Detects call intent from caller statements
    - Routes to specialized agents via handoffs
    - Handles direct queries (hours/location) without transfer
    """

    def __init__(
        self,
        business_hours_context: str | None = None,
        is_after_hours: bool | None = None,
    ) -> None:
        """Initialize Assistant with business hours context.

        Args:
            business_hours_context: Pre-generated business hours context for testing.
                                  If None, generates context from current time.
            is_after_hours: Explicit after-hours flag for testing. If None, determined
                           from business_hours_context or is_office_open().
        """
        # Generate business hours context at agent initialization
        hours_context = (
            business_hours_context
            if business_hours_context is not None
            else format_business_hours_prompt()
        )

        # Determine after-hours and lunch status for on_enter behavior
        if is_after_hours is not None:
            self._is_after_hours = is_after_hours
            self._is_lunch = False
        elif business_hours_context is not None:
            self._is_after_hours = "OFFICE STATUS: Closed" in business_hours_context
            self._is_lunch = "OFFICE STATUS: Lunch" in business_hours_context
        else:
            # Use real-time check; lunch and after-hours are mutually exclusive
            self._is_lunch = is_lunch_hour()
            self._is_after_hours = not is_office_open() and not self._is_lunch

        # Determine the greeting instruction based on office status
        if self._is_lunch:
            greeting_instruction = """GREETING (SAY THIS FIRST when you start):
"Thank you for calling Harry Leveen Insurance. I'm Aizellee, an automated assistant. Our staff is on lunch break right now and we'll be back at 1. How can I help you?"
You may vary the wording slightly but you MUST mention the lunch break and 1 PM return.
EXCEPTION: If the caller's first message is DISTRESSING (accident, break-in, theft, fire, claim), SKIP the greeting and respond with empathy FIRST. Then mention the lunch break after showing empathy."""
        elif self._is_after_hours:
            greeting_instruction = """GREETING (SAY THIS FIRST when you start):
"Thanks for calling Harry Leveen Insurance. I'm Aizellee, an automated assistant. We're closed now, but open weekdays 9 to 5 Eastern. How can I help with your insurance?"
IMPORTANT: You MUST mention that the office is closed in your first response.
EXCEPTION: If the caller's first message is DISTRESSING (accident, break-in, theft, fire, claim), SKIP the greeting and respond with empathy FIRST. Example: "Oh no, I'm so sorry to hear that. Are you okay?" Then mention office hours briefly after showing empathy."""
        else:
            greeting_instruction = """GREETING (SAY THIS FIRST when you start):
"Thank you for calling Harry Leveen Insurance. I'm Aizellee, an automated assistant. How can I help you today?"
You may vary the greeting slightly but keep it warm and professional.
EXCEPTION: If the caller's first message is DISTRESSING (accident, break-in, theft, fire, claim), SKIP the greeting and respond with empathy FIRST. Example: "Oh no, I'm so sorry to hear that. Are you okay?" """

        super().__init__(
            instructions=compose_instructions(
                ASSISTANT_IDENTITY,
                hours_context,
                greeting_instruction,
                ASSISTANT_OUTPUT_RULES,
                ASSISTANT_OFFICE_STATUS_GATE,
                ASSISTANT_ROUTING_REFERENCE,
                ASSISTANT_STANDARD_FLOW,
                ASSISTANT_DTMF_NOTE,
                ASSISTANT_INSURANCE_TYPE_DETECTION,
                ASSISTANT_TONE_GUIDANCE,
                ASSISTANT_SPECIAL_NOTES,
                ASSISTANT_EDGE_CASES,
                SECURITY_INSTRUCTIONS_EXTENDED,
                UNCERTAINTY_HANDLING,
                CAPABILITY_BOUNDARIES,
                ASSISTANT_OFFICE_INFO,
                ASSISTANT_PERSONALITY,
            ),
        )

    async def on_enter(self) -> None:
        """Called when this agent becomes active - deliver appropriate greeting.

        Checks after-hours status and generates either:
        - After-hours greeting mentioning office is closed
        - Normal business hours greeting
        """
        # Use a simple instruction that references the GREETING section in the agent's instructions
        await self.session.generate_reply(
            instructions="Deliver the GREETING as specified in your instructions. This is the start of the call."
        )

    @function_tool
    async def record_caller_contact_info(
        self,
        context: RunContext[CallerInfo],
        first_name: str,
        last_name: str,
        phone_number: str,
    ) -> str:
        """Record the caller's name and phone number for callback purposes.

        Call this tool after the caller provides their first name, last name,
        and phone number. This captures contact information at the start of the call.

        Args:
            first_name: The caller's first name
            last_name: The caller's last name
            phone_number: The caller's phone number
        """
        # Store individual name components
        context.userdata.first_name = first_name
        context.userdata.last_name = last_name
        # Maintain full name for backwards compatibility
        context.userdata.name = f"{first_name} {last_name}"
        context.userdata.phone_number = phone_number

        full_name = f"{first_name} {last_name}"
        logger.info(
            f"Recorded caller info: {mask_name(full_name)}, {mask_phone(phone_number)}"
        )

        # Format phone for voice confirmation with chunking for easier verification
        # e.g., "5551234567" -> "5-5-5, 1-2-3, 4-5-6-7"
        digits = "".join(filter(str.isdigit, phone_number))
        if len(digits) == 10:
            formatted = (
                f"{digits[0]}-{digits[1]}-{digits[2]}, "
                f"{digits[3]}-{digits[4]}-{digits[5]}, "
                f"{digits[6]}-{digits[7]}-{digits[8]}-{digits[9]}"
            )
        elif len(digits) == 11 and digits[0] == "1":
            # Handle 1-xxx-xxx-xxxx format
            formatted = (
                f"{digits[1]}-{digits[2]}-{digits[3]}, "
                f"{digits[4]}-{digits[5]}-{digits[6]}, "
                f"{digits[7]}-{digits[8]}-{digits[9]}-{digits[10]}"
            )
        else:
            formatted = phone_number  # Fallback to original

        return f"Recorded: {full_name}, {formatted}"

    @function_tool
    async def record_business_insurance_info(
        self,
        context: RunContext[CallerInfo],
        business_name: str,
    ) -> str:
        """Record that this is a business insurance inquiry and the business name.

        Call this tool when the caller indicates this is for business insurance.
        NOTE: This tool does NOT assign an agent - sub-agents handle their own routing
        based on whether the caller is new business or existing client.

        Args:
            business_name: The name of the business
        """
        context.userdata.insurance_type = InsuranceType.BUSINESS
        context.userdata.business_name = business_name

        logger.info(f"Business insurance inquiry recorded for: {business_name}")
        return f"Recorded business insurance for: {business_name}"

    @function_tool
    async def record_personal_insurance_info(
        self,
        context: RunContext[CallerInfo],
        last_name_spelled: str,
    ) -> str:
        """Record that this is a personal insurance inquiry with the spelled last name.

        Call this tool when the caller indicates this is for personal insurance.
        NOTE: This tool does NOT assign an agent - sub-agents handle their own routing
        based on whether the caller is new business or existing client.

        Args:
            last_name_spelled: The caller's last name as they spelled it out
        """
        context.userdata.insurance_type = InsuranceType.PERSONAL

        # Normalize spelled name: extract only letters (handles STT errors like
        # "you are b a n" instead of "U R B A N")
        normalized = "".join(c.upper() for c in last_name_spelled if c.isalpha())

        # If we already have last_name from contact info and normalized spelled
        # version doesn't match first letter, prefer the contact info last_name
        if (
            context.userdata.last_name
            and normalized
            and normalized[0] != context.userdata.last_name[0].upper()
        ):
            # STT likely misheard the spelling - use the last_name we already have
            logger.warning(
                f"Spelled name mismatch: heard '{last_name_spelled}' -> '{normalized}', "
                f"but contact info has last_name='{context.userdata.last_name}'. "
                f"Using last_name for routing."
            )
            normalized = context.userdata.last_name.upper()

        context.userdata.last_name_spelled = (
            normalized if normalized else last_name_spelled
        )

        logger.info(
            f"Personal insurance inquiry recorded, last name: {mask_name(context.userdata.last_name_spelled)}"
        )
        return f"Recorded personal insurance for last name: {context.userdata.last_name_spelled}"

    @function_tool
    async def route_call_claims(
        self,
        context: RunContext[CallerInfo],
    ) -> Agent:
        """Route the call for filing or inquiring about a claim.

        Call this IMMEDIATELY when the caller needs to file a claim - do NOT speak first.
        This tool handles ALL speech (empathy + transfer message) automatically.

        Trigger phrases:
        - "file a claim", "make a claim", "need to report a claim"
        - "I had an accident", "car accident", "fender bender"
        - "someone hit me", "got into an accident"
        - "water damage", "pipe burst", "flooded"
        - "fire damage", "there was a fire"
        - "theft", "break-in", "someone stole", "my car was stolen"
        - "vandalism", "someone vandalized"
        - "roof damage", "storm damage", "hail damage"
        - "need to report a loss"

        IMPORTANT: Do NOT speak before or after calling this tool. The tool speaks
        the empathy and transfer message directly to the caller.
        """
        context.userdata.call_intent = CallIntent.CLAIMS
        context.userdata._handoff_speech_delivered = True  # Mark speech as delivered
        logger.info(
            f"Detected claims request, handing off to ClaimsAgent: {context.userdata.to_safe_log()}"
        )

        # Log the routing decision
        log_route_decision(
            intent=CallIntent.CLAIMS,
            agent=None,
            insurance_type=context.userdata.insurance_type,
            identifier=context.userdata.business_name
            or context.userdata.last_name_spelled,
            destination="handoff:ClaimsAgent",
            is_personal=context.userdata.insurance_type == InsuranceType.PERSONAL,
        )

        # Speak the COMPLETE transfer message here (deterministic, not LLM)
        # This is the ONLY speech for claims handoff - ClaimsAgent will be silent
        await context.session.say(
            f"I'm so sorry to hear about that. Let me connect you with our claims team now. {HOLD_MESSAGE}",
            allow_interruptions=False,
        )

        # Return just the agent (no tuple) for SILENT handoff
        # The tool already spoke via session.say() above
        return ClaimsAgent(
            chat_ctx=self.session.chat_ctx.copy(exclude_config_update=True)
        )

    @function_tool
    async def route_call_certificate(
        self,
        context: RunContext[CallerInfo],
    ) -> Agent:
        """Route the call for certificate of insurance requests.

        Call this when the caller needs a certificate of insurance (COI).
        This includes requests like:
        - "certificate of insurance", "COI", "certificate request"
        - "need a certificate", "proof of insurance for"
        - "certificate for a job", "general contractor needs certificate"
        - "vendor certificate", "additional insured"
        - "proof of insurance for a contract"

        IMPORTANT: This hands off to MortgageeCertificateAgent which handles
        new certificate requests (email) and existing certificate questions (transfer to AE).
        """
        context.userdata.call_intent = CallIntent.CERTIFICATES
        logger.info(
            f"Detected certificate request, handing off to MortgageeCertificateAgent: {context.userdata.to_safe_log()}"
        )

        # Log the routing decision
        log_route_decision(
            intent=CallIntent.CERTIFICATES,
            agent=None,
            insurance_type=context.userdata.insurance_type,
            identifier=context.userdata.business_name
            or context.userdata.last_name_spelled,
            destination="handoff:MortgageeCertificateAgent",
            is_personal=context.userdata.insurance_type == InsuranceType.PERSONAL,
        )

        # Hand off to the specialized MortgageeCertificateAgent with conversation context
        return MortgageeCertificateAgent(
            request_type="certificate",
            chat_ctx=self.session.chat_ctx.copy(exclude_config_update=True),
        ), "I can help you with your certificate request."

    @function_tool
    async def route_call_mortgagee(
        self,
        context: RunContext[CallerInfo],
    ) -> Agent:
        """Route the call for mortgagee or lienholder requests.

        Call this when:
        - Caller has mortgagee or lienholder questions/requests
        - Caller needs to add, change, or update mortgagee information
        - Caller has loss payee questions

        Trigger phrases:
        - "mortgagee", "lienholder", "mortgage company", "loss payee"
        - "lender needs", "add mortgagee", "mortgagee change"

        IMPORTANT: This does NOT transfer to a person - it redirects to
        email (info@hlinsure.com).
        """
        context.userdata.call_intent = CallIntent.MORTGAGEE_LIENHOLDERS
        logger.info(
            f"Detected mortgagee request, handing off to MortgageeCertificateAgent: {context.userdata.to_safe_log()}"
        )

        # Log the routing decision
        log_route_decision(
            intent=CallIntent.MORTGAGEE_LIENHOLDERS,
            agent=None,
            insurance_type=context.userdata.insurance_type,
            identifier=context.userdata.business_name
            or context.userdata.last_name_spelled,
            destination="handoff:MortgageeCertificateAgent",
            is_personal=context.userdata.insurance_type == InsuranceType.PERSONAL,
        )

        # Hand off to the specialized MortgageeCertificateAgent with conversation context
        return MortgageeCertificateAgent(
            request_type="mortgagee",
            chat_ctx=self.session.chat_ctx.copy(exclude_config_update=True),
        ), "I can help you with that."

    @function_tool
    async def handle_bank_caller(
        self,
        context: RunContext[CallerInfo],
    ) -> None:
        """Handle bank representative callers directly without transfer.

        Call this ONLY when the caller identifies as a bank representative.
        Bank callers are NOT policyholders - they are calling about a mutual customer.

        CRITICAL: Do NOT call this for customers who mention their bank in passing.

        Trigger phrases (MUST be from bank rep, not customer):
        - "calling from [bank name]" (e.g., "calling from Chase")
        - "calling on behalf of [bank name]"
        - "on a recorded line" (common bank identifier)
        - "mutual client" or "mutual customer"
        - Explicitly says "I'm a bank representative" or "I work for [bank]"
        - "lender calling about"

        FALSE POSITIVE EXAMPLES TO AVOID:
        - Customer: "I bank with Chase and need home insurance" → This is a NEW_QUOTE request
        - Customer: "My bank needs proof of insurance" → This is a MORTGAGEE request through MortgageeCertificateAgent
        - Customer: "I have an account with Wells Fargo" → Not a bank caller

        IMPORTANT: This tool does NOT transfer to a person.
        It provides email information and confirms no fax is available.
        This is a DIRECT, COMPLETE response - do not add anything before or after.
        After speaking this response, END THE CALL.

        Returns None to signal the LLM to be silent after speaking.
        """
        context.userdata.call_intent = CallIntent.BANK_CALLER
        logger.info(
            f"Bank caller detected, handling directly: {context.userdata.to_safe_log()}"
        )

        # Log the routing decision
        log_route_decision(
            intent=CallIntent.BANK_CALLER,
            agent=None,
            insurance_type=None,
            identifier=None,
            destination="direct:email_response",
        )

        # Speak the response directly to ensure consistent delivery
        info_email = format_email_for_speech("Info@HLInsure.com")
        bank_response = (
            f"All requests must be submitted in writing to {info_email} "
            "No, we don't have a fax number. "
            "Have a good day. Goodbye."
        )
        await context.session.say(bank_response, allow_interruptions=False)

        # Return None to signal completion - LLM should stay silent
        # (per LiveKit docs: return None for silent completion)

    @function_tool
    async def detect_spanish_speaker(
        self,
        context: RunContext[CallerInfo],
    ) -> str:
        """Route Spanish-speaking caller to a bilingual staff member.

        Call this when:
        - Caller speaks Spanish
        - Caller requests Spanish-speaking assistance
        - Caller says "Español" or "habla español"

        This tool finds an available bilingual agent and initiates the transfer.
        Say "Un momento, por favor" before calling this tool.
        """
        # Find available bilingual agents
        bilingual_agents = get_bilingual_agents("es")

        for agent in bilingual_agents:
            if is_agent_available(agent):
                context.userdata.additional_notes = "Spanish-speaking caller"
                logger.info(
                    f"Routing Spanish speaker to bilingual agent: {agent['name']} "
                    f"(ext {agent['ext']})"
                )

                # Log the routing decision
                log_route_decision(
                    intent=CallIntent.SPANISH_SPEAKER,
                    agent=agent["name"],
                    insurance_type=context.userdata.insurance_type,
                    identifier=context.userdata.business_name
                    or context.userdata.last_name_spelled,
                    destination="transfer:bilingual_agent",
                    is_personal=context.userdata.insurance_type
                    == InsuranceType.PERSONAL,
                )

                return await self._initiate_transfer(context, agent, "Spanish speaker")

        # No bilingual agent available - provide alternative
        logger.warning("No bilingual agents available for Spanish speaker")
        return (
            "I apologize, but our Spanish-speaking team members are currently unavailable. "
            "You can call back during business hours, Monday through Friday 9 AM to 5 PM Eastern, "
            "or email us at info@hlinsure.com. Lo siento, gracias por llamar."
        )

    @function_tool
    async def collect_phone_via_keypad(
        self,
        context: RunContext[CallerInfo],
    ) -> str:
        """Collect phone number via keypad or voice for telephony callers.

        Use this tool ONLY when the caller is on a phone line (not web).
        This allows them to dial their number on the keypad for better accuracy.

        The caller can either speak the digits or dial them on their keypad.
        Example: "4-0-7, 5-5-5, 1-2-3-4"
        """
        from tasks.phone_collection import collect_phone_number_dtmf

        phone = await collect_phone_number_dtmf(self.session.chat_ctx)
        if phone:
            context.userdata.phone_number = phone
            return f"Recorded phone number: {phone}"
        else:
            return "I wasn't able to capture that. Could you tell me your phone number?"

    @function_tool
    async def route_call_after_hours(
        self,
        context: RunContext[CallerInfo],
    ) -> Agent:
        """Route the call to the after-hours voicemail flow.

        Call this when:
        - The OFFICE STATUS shows "Closed"
        - AND the caller's intent is NOT one of these exceptions:
          - CLAIMS: Route to ClaimsAgent as normal (handles after-hours with carrier numbers)
          - HOURS/LOCATION: Answer directly using provide_hours_and_location
          - CERTIFICATES: Route to MortgageeCertificateAgent (provides email info)
          - MORTGAGEE: Route to MortgageeCertificateAgent (provides email info)

        For ALL OTHER INTENTS when office is closed, use this function to route
        the caller to the after-hours voicemail flow. This includes:
        - New quote requests
        - Payment or document requests
        - Policy changes
        - Cancellations
        - Coverage/rate questions
        - Policy review/renewal
        - Requests for specific agents
        - Any other general inquiries

        The AfterHoursAgent will:
        1. Inform caller the office is closed
        2. Collect name and phone number
        3. Determine insurance type (business/personal)
        4. Get business name or spelled last name
        5. Transfer to the appropriate agent's voicemail
        """
        logger.info(
            f"Detected after-hours call, handing off to AfterHoursAgent: {context.userdata.to_safe_log()}"
        )

        # Log the routing decision
        log_route_decision(
            intent=context.userdata.call_intent or "after_hours",
            agent=None,
            insurance_type=context.userdata.insurance_type,
            identifier=context.userdata.business_name
            or context.userdata.last_name_spelled,
            destination="handoff:AfterHoursAgent",
            is_personal=context.userdata.insurance_type == InsuranceType.PERSONAL,
        )

        # Hand off to the specialized AfterHoursAgent with conversation context
        return AfterHoursAgent(
            chat_ctx=self.session.chat_ctx.copy(exclude_config_update=True),
        ), "Let me connect you with our after-hours system."

    @function_tool
    async def route_call(
        self,
        context: RunContext[CallerInfo],
        intent: str,
        reason: str | None = None,
    ) -> str:
        """Route call to appropriate department based on caller's intent.

        Call this tool to route the caller based on what they need help with.

        Args:
            intent: The type of request. Must be one of:
                - "policy_change" - Caller wants to make changes to their policy
                - "cancellation" - Caller wants to cancel their policy
                - "coverage_questions" - Questions about coverage or rates
                - "policy_review" - Annual policy review or renewal
                - "mortgagee_lienholder" - Questions about mortgagee/lienholder info
                - "certificates" - Requests for certificate of insurance
                - "claims" - Filing or checking on a claim
                - "other" - Doesn't fit other categories
            reason: Brief description of the caller's request (required for "other" intent)
        """
        intent_map: dict[str, tuple[CallIntent, str]] = {
            "policy_change": (
                CallIntent.MAKE_CHANGE,
                "I'll connect you with an agent who can help you make changes to your policy.",
            ),
            "cancellation": (
                CallIntent.CANCELLATION,
                "I'll connect you with an agent who can assist with your cancellation request.",
            ),
            "coverage_questions": (
                CallIntent.COVERAGE_RATE_QUESTIONS,
                "I'll connect you with an agent who can answer your coverage questions.",
            ),
            "policy_review": (
                CallIntent.POLICY_REVIEW_RENEWAL,
                "I'll connect you with an agent for your policy review.",
            ),
            "mortgagee_lienholder": (
                CallIntent.MORTGAGEE_LIENHOLDERS,
                "I'll connect you with someone who can help with mortgagee information.",
            ),
            "certificates": (
                CallIntent.CERTIFICATES,
                "I'll connect you with someone who can help with your certificate request.",
            ),
            "claims": (
                CallIntent.CLAIMS,
                "I'll connect you with our claims department.",
            ),
            "other": (
                CallIntent.SOMETHING_ELSE,
                "Let me connect you with someone who can help.",
            ),
        }

        if intent not in intent_map:
            intent = "other"

        call_intent, response = intent_map[intent]
        context.userdata.call_intent = call_intent

        if intent == "other" and reason:
            context.userdata.additional_notes = reason
            logger.info(
                f"Routing call for other reason ({reason}): intent={call_intent}"
            )
        else:
            logger.info(f"Routing call: intent={call_intent}")

        return response

    @function_tool
    async def provide_hours_and_location(
        self,
        context: RunContext[CallerInfo],
    ) -> str:
        """Provide office hours and location information.

        Call this when the caller asks about office hours or directions.
        Returns a contextual response based on whether the office is currently open.
        """
        context.userdata.call_intent = CallIntent.HOURS_LOCATION
        logger.info(f"Providing hours/location info: {context.userdata.to_safe_log()}")

        # Generate contextual response based on current business hours status
        if is_office_open():
            hours_info = "We're open right now until 5 PM"
        elif is_lunch_hour():
            hours_info = "We're on our lunch break right now, but we'll be back at 1 PM"
        else:
            next_open = get_next_open_time()
            hours_info = f"We're currently closed, but we'll reopen {next_open}"

        return (
            f"{hours_info}. Our regular hours are Monday through Friday, 9 AM to 5 PM Eastern. "
            "We do close from 12 to 1 for lunch, so keep that in mind if you're planning to call or visit. "
            "We're located at 7208 West Sand Lake Road, Suite 206, Orlando, Florida 32819. "
            "While we are available for walk-ins, appointments are strongly recommended "
            "so that enough time is allotted to review and address any concerns, questions, "
            "or changes you would like to go over."
        )

    @function_tool
    async def route_call_specific_agent(
        self,
        context: RunContext[CallerInfo],
        agent_name: str,
    ) -> str:
        """Route the call to a specific agent or extension.

        Call this when the caller asks for a specific agent by name or extension.

        IMPORTANT: This tool asks "What is this in reference to?" for ALL agents
        before transferring. After the caller explains their reason, use
        complete_specific_agent_transfer to proceed with the transfer.

        For Sales Agents (Rachel Moreno, Brad), the caller may be redirected to
        their Account Executive if the request is service-related (not a new quote).

        Args:
            agent_name: The name of the agent or extension number the caller requested
        """
        context.userdata.call_intent = CallIntent.SPECIFIC_AGENT
        context.userdata.specific_agent_name = agent_name

        # Look up the agent in staff directory (exact match first)
        agent = get_agent_by_name(agent_name)

        # If no exact match, check for ambiguous names (e.g., "Rachel" matches Rachel T. and Rachel Moreno)
        if not agent:
            matches = get_agents_by_name_prefix(agent_name)
            if len(matches) > 1:
                names = " and ".join(m["name"] for m in matches)
                logger.info(
                    f"Ambiguous agent name '{agent_name}' matches {len(matches)} agents: {names}"
                )
                return f"We have {names}. Which one would you like to speak with?"
            elif len(matches) == 1:
                agent = matches[0]

        if agent:
            # Check if this agent can receive direct AI transfers
            if not is_transferable(agent["name"]):
                # Jason L. and Fred are not available for direct transfers
                logger.info(
                    f"Restricted transfer requested: {agent['name']} - offering to take message"
                )
                return (
                    f"{agent['name']} isn't available right now. "
                    "Can I take a message for them?"
                )

            # For ALL transferable agents, ask what the call is about
            context.userdata.requested_agent_name = agent["name"]
            logger.info(
                f"Agent {agent['name']} requested - asking for reason: {context.userdata.to_safe_log()}"
            )
            return f"Sure, I can connect you with {agent['name']}. May I ask what this is in reference to?"
        else:
            logger.info(f"Agent not found in directory: {agent_name}")
            return "I'm not finding that name in our directory. Could you double-check the name for me?"

    @function_tool
    async def complete_specific_agent_transfer(
        self,
        context: RunContext[CallerInfo],
        reason: str,
        is_new_business: bool = False,
    ) -> str | None:
        """Complete the transfer after learning what the call is about.

        Call this AFTER route_call_specific_agent asked "May I ask what this is
        in reference to?" and the caller has explained their reason.

        DECISION LOGIC FOR SALES AGENTS (Rachel Moreno, Brad):
        - If is_new_business=True: Transfer to the originally requested Sales Agent
        - If is_new_business=False: Redirect to the caller's Account Executive instead

        DECISION LOGIC FOR ALL OTHER AGENTS:
        - Transfer directly to the requested agent (is_new_business is ignored)

        Args:
            reason: Brief summary of what the caller said their call is about
            is_new_business: True if caller wants a new quote/policy, False if
                           they're an existing client with a service request.
                           Only relevant for Sales Agents.

        Returns:
            Error/question string if more info needed, None on successful transfer.
        """
        requested_agent_name = getattr(context.userdata, "requested_agent_name", None)

        if not requested_agent_name:
            logger.warning(
                "complete_specific_agent_transfer called without prior route_call_specific_agent"
            )
            raise ToolError(
                "No prior route_call_specific_agent call found. "
                "Call route_call_specific_agent first to get the requested agent name."
            )

        # Store the reason
        context.userdata.additional_notes = reason

        # Look up agent
        agent = get_agent_by_name(requested_agent_name)
        if not agent:
            raise ToolError(
                f"Agent '{requested_agent_name}' not found in staff directory"
            )

        # Check if this is a Sales Agent — special routing logic applies
        sales_agents = get_agents_by_department("PL-Sales Agent")
        sales_agent_names = [sa["name"] for sa in sales_agents]

        if agent["name"] in sales_agent_names:
            if is_new_business:
                # Transfer to the originally requested Sales Agent
                logger.info(
                    f"Completing transfer to Sales Agent {agent['name']} for new business: {reason}"
                )
                return await self._initiate_transfer(context, agent, "new quote")
            else:
                # Service request - redirect to Account Executive
                validation_error = self._validate_transfer_requirements(context)
                if validation_error:
                    context.userdata.pending_ae_redirect = True
                    return validation_error

                ae_agent = self._find_agent_for_transfer(context, is_new_business=False)

                if not ae_agent:
                    logger.warning("No Account Executive found for redirect")
                    raise ToolError(
                        f"No Account Executive found for insurance_type={context.userdata.insurance_type}, "
                        f"business_name={context.userdata.business_name}, "
                        f"last_name_spelled={context.userdata.last_name_spelled}"
                    )

                logger.info(
                    f"Redirecting from Sales Agent {requested_agent_name} to Account Executive "
                    f"{ae_agent['name']} for service request: {reason}"
                )

                await context.session.say(
                    "Let me see if your account executive is available.",
                    allow_interruptions=False,
                )
                return await self._initiate_transfer(
                    context, ae_agent, "service request"
                )
        else:
            # Non-Sales Agent — transfer directly after logging the reason
            logger.info(f"Completing transfer to {agent['name']} for: {reason}")
            return await self._initiate_transfer(
                context, agent, "specific agent request"
            )

    # =========================================================================
    # TRANSFER UTILITY METHODS
    # =========================================================================
    # These methods provide common transfer functionality used by the new
    # unified transfer tools below. They mirror the BaseRoutingAgent pattern
    # but are designed for direct transfer (no handoff to sub-agents).

    async def _initiate_transfer(
        self, context: RunContext[CallerInfo], agent: dict, transfer_type: str
    ) -> None:
        """Initiate the transfer to an agent with hold experience.

        This method:
        1. Logs the transfer attempt
        2. Speaks the transfer message to the caller
        3. Waits for the message to finish playing
        4. Returns None to signal the LLM to stay silent

        TODO: Implement actual SIP transfer when phone system is configured.
        Once SIP is configured, this will call ctx.transfer_sip_participant()
        and the session will end automatically after the transfer.

        Args:
            context: The run context containing caller information.
            agent: Staff directory entry with name, ext, department, etc.
            transfer_type: Type of transfer for logging (e.g., "cancellation", "quote")
        """
        agent_name = agent.get("name", "an agent") if isinstance(agent, dict) else agent
        agent_ext = (
            agent.get("ext", "unknown") if isinstance(agent, dict) else "unknown"
        )

        # Log the transfer attempt with extension info (mask PII)
        caller_name = context.userdata.name
        caller_phone = context.userdata.phone_number

        logger.info(
            f"[MOCK TRANSFER] Initiating {transfer_type} transfer to {agent_name} "
            f"(ext {agent_ext}) for caller: "
            f"name={mask_name(caller_name) if caller_name else 'unknown'}, "
            f"phone={mask_phone(caller_phone) if caller_phone else 'unknown'}"
        )

        # Speak the transfer message and wait for it to finish
        # Using allow_interruptions=False ensures the full message plays
        transfer_message = f"I'm connecting you with {agent_name} now. {HOLD_MESSAGE}"
        await context.session.say(transfer_message, allow_interruptions=False)

        # TODO: Implement actual SIP transfer logic using agent["ext"]
        # When implemented, call:
        #   job_ctx = get_job_context()
        #   await job_ctx.transfer_sip_participant(participant, f"tel:{phone_number}")
        # The session will end automatically after a cold transfer.

        # Return None to signal completion - LLM should stay silent
        # (per LiveKit docs: return None for silent completion)

    async def _initiate_ring_group_transfer(
        self,
        context: RunContext[CallerInfo],
        group_name: str,
        transfer_type: str,
    ) -> None:
        """Initiate transfer to a ring group.

        This method:
        1. Logs the transfer attempt
        2. Speaks the transfer message to the caller
        3. Waits for the message to finish playing
        4. Returns None to signal the LLM to stay silent

        TODO: Implement actual SIP ring group transfer.

        Args:
            context: The run context containing caller information.
            group_name: Name of the ring group (e.g., "VA").
            transfer_type: Type of transfer for logging.
        """
        ring_group = get_ring_group(group_name)
        if not ring_group:
            logger.warning(f"Ring group not found: {group_name}")
            # Still speak the message and stay silent
            await context.session.say(
                f"I'm connecting you with our team now. {HOLD_MESSAGE}",
                allow_interruptions=False,
            )
            return  # Return None implicitly for silent completion

        # Log the transfer attempt
        caller_name = context.userdata.name
        caller_phone = context.userdata.phone_number

        logger.info(
            f"[MOCK TRANSFER] Initiating {transfer_type} transfer to ring group "
            f"{ring_group['name']} (extensions: {ring_group['extensions']}) for caller: "
            f"name={mask_name(caller_name) if caller_name else 'unknown'}, "
            f"phone={mask_phone(caller_phone) if caller_phone else 'unknown'}"
        )

        # Speak the transfer message and wait for it to finish
        await context.session.say(
            f"I'm connecting you with our team now. {HOLD_MESSAGE}",
            allow_interruptions=False,
        )

        # TODO: Implement actual SIP ring group transfer

        # Return None to signal completion - LLM should stay silent
        # (per LiveKit docs: return None for silent completion)

    def _find_agent_for_transfer(
        self,
        context: RunContext[CallerInfo],
        is_new_business: bool = False,
    ) -> dict | None:
        """Find the appropriate agent for transfer using alpha-split routing.

        Determines the correct agent based on:
        - Insurance type (business vs personal)
        - Identifier (business name or last name)
        - Whether it's new business or existing client

        Args:
            context: The run context containing caller information.
            is_new_business: Whether this is a new business inquiry.

        Returns:
            Staff directory entry dict, or None if no match found.
        """
        userdata = context.userdata

        # Determine department and routing key based on insurance type
        if userdata.insurance_type == InsuranceType.BUSINESS:
            department = "CL"
            route_key = get_alpha_route_key(userdata.business_name or "")
            identifier = userdata.business_name
        elif userdata.insurance_type == InsuranceType.PERSONAL:
            department = "PL"
            route_key = (
                userdata.last_name_spelled[0].upper()
                if userdata.last_name_spelled
                else "A"
            )
            identifier = userdata.last_name_spelled
        else:
            logger.warning("No insurance type set, cannot determine routing")
            return None

        # Find the agent via alpha-split routing
        agent = find_agent_by_alpha(route_key, department, is_new_business)

        if agent:
            logger.info(
                f"Alpha-split routing: identifier={identifier}, "
                f"key={route_key}, department={department}, "
                f"is_new_business={is_new_business} -> {agent['name']}"
            )
            # Store the assigned agent for reference
            userdata.assigned_agent = agent["name"]
        else:
            logger.warning(
                f"No agent found for alpha-split: key={route_key}, "
                f"department={department}, is_new_business={is_new_business}"
            )

        return agent

    def _validate_transfer_requirements(
        self, context: RunContext[CallerInfo]
    ) -> str | None:
        """Validate that all required information is collected before transfer.

        Checks that:
        - Insurance type is set
        - Appropriate identifier is collected (business_name or last_name_spelled)

        Args:
            context: The run context containing caller information.

        Returns:
            Error message if validation fails, None if all requirements met.
        """
        userdata = context.userdata

        if not userdata.insurance_type:
            return (
                "I need to know if this is for business or personal insurance "
                "before I can connect you with the right person."
            )

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

        return None

    # =========================================================================
    # UNIFIED TRANSFER TOOLS (Phase 1 - Architecture Simplification)
    # =========================================================================
    # These tools replace sub-agent handoffs with direct transfers.
    # The Assistant collects ALL required info, then uses these tools to route.
    # Each tool validates requirements, sets intent, and initiates transfer.

    @function_tool
    async def transfer_cancellation(
        self,
        context: RunContext[CallerInfo],
    ) -> str | None:
        """Transfer caller to Account Executive for policy cancellation.

        REQUIREMENTS BEFORE CALLING:
        - insurance_type must be set (business or personal)
        - For business: business_name must be collected
        - For personal: last_name_spelled must be collected
        - Empathy should already have been expressed

        Routes to Account Executives via alpha-split:
        - Business (CL): A-F -> Adriana, G-O -> Rayvon, P-Z -> Dionna
        - Personal (PL): A-G -> Yarislyn, H-M -> Al, N-Z -> Luis

        Returns:
            Validation error string if requirements not met, None on successful transfer.
        """
        # Validate requirements
        validation_error = self._validate_transfer_requirements(context)
        if validation_error:
            return validation_error

        # Set call intent
        context.userdata.call_intent = CallIntent.CANCELLATION

        # Find appropriate agent via alpha-split
        agent = self._find_agent_for_transfer(context, is_new_business=False)

        if not agent:
            logger.warning("No agent found for cancellation transfer")
            return (
                "I apologize, but I'm having trouble connecting you right now. "
                "Can you please hold while I find someone to help?"
            )

        # Log the routing decision
        identifier = (
            context.userdata.business_name or context.userdata.last_name_spelled
        )
        log_route_decision(
            intent=CallIntent.CANCELLATION,
            agent=agent["name"],
            insurance_type=context.userdata.insurance_type,
            identifier=identifier,
            destination="transfer",
            is_personal=context.userdata.insurance_type == InsuranceType.PERSONAL,
        )

        logger.info(
            f"Transferring cancellation call to {agent['name']}: {context.userdata.to_safe_log()}"
        )

        return await self._initiate_transfer(context, agent, "cancellation")

    @function_tool
    async def transfer_new_quote(
        self,
        context: RunContext[CallerInfo],
    ) -> str | None:
        """Transfer caller to Sales Agent for a new insurance quote.

        REQUIREMENTS BEFORE CALLING:
        - insurance_type must be set (business or personal)
        - For business: business_name must be collected
        - For personal: last_name_spelled must be collected

        Routes to Sales Agents via alpha-split (is_new_business=True):
        - Business (CL): A-F -> Adriana, G-O -> Rayvon, P-Z -> Dionna
        - Personal (PL): A-L -> Rachel Moreno, M-Z -> Brad

        FALLBACK LOGIC (Personal Lines only):
        If both PL Sales Agents (Brad and Rachel Moreno) are unavailable:
        1. Try the other PL Sales Agent (if one is available)
        2. Fall back to PL Account Executive for the alpha range
        3. Fall back to Management (Kelly U. or Julie L.)
        4. If all unavailable, offer to take a message

        Returns:
            Validation error string if requirements not met, None on successful transfer.
        """
        # Validate requirements
        validation_error = self._validate_transfer_requirements(context)
        if validation_error:
            return validation_error

        # Set call intent
        context.userdata.call_intent = CallIntent.NEW_QUOTE

        userdata = context.userdata

        # For Personal Lines new quotes, use fallback-enabled routing
        if userdata.insurance_type == InsuranceType.PERSONAL:
            route_key = (
                userdata.last_name_spelled[0].upper()
                if userdata.last_name_spelled
                else "A"
            )

            agent, fallback_type = find_pl_sales_agent_with_fallback(route_key)

            if agent:
                userdata.assigned_agent = agent["name"]

                # Log with fallback information
                logger.info(
                    f"PL new quote routing: key={route_key}, "
                    f"fallback_type={fallback_type}, agent={agent['name']}"
                )

                # Log the routing decision with fallback context
                log_route_decision(
                    intent=CallIntent.NEW_QUOTE,
                    agent=agent["name"],
                    insurance_type=InsuranceType.PERSONAL,
                    identifier=userdata.last_name_spelled,
                    destination=f"transfer:fallback_{fallback_type}",
                    is_personal=True,
                )

                # Customize messaging based on fallback type
                if fallback_type == "primary":
                    # Normal routing to designated sales agent
                    return await self._initiate_transfer(context, agent, "new quote")
                elif fallback_type == "alternate_sales":
                    # Routing to the other sales agent
                    logger.info(
                        f"Primary PL Sales Agent unavailable, using alternate: {agent['name']}"
                    )
                    return await self._initiate_transfer(context, agent, "new quote")
                elif fallback_type == "account_executive":
                    # Routing to Account Executive as fallback
                    logger.info(
                        f"Both PL Sales Agents unavailable, falling back to Account Executive: {agent['name']}"
                    )
                    return await self._initiate_transfer(context, agent, "new quote")
                elif fallback_type == "management":
                    # Routing to Management as last resort
                    logger.info(
                        f"All PL Sales Agents and Account Executives unavailable, falling back to Management: {agent['name']}"
                    )
                    return await self._initiate_transfer(context, agent, "new quote")
            else:
                # All agents unavailable - offer voicemail
                logger.warning(
                    "All PL Sales Agents, Account Executives, and Management unavailable for new quote"
                )
                return (
                    "I'm sorry, but all of our sales team members are currently unavailable. "
                    "I can take your information and have someone call you back, or you can "
                    "try again during our regular business hours, Monday through Friday, "
                    "9 AM to 5 PM Eastern. Would you like to leave a message?"
                )

        # For Commercial Lines, use standard routing (CL Account Executives handle new business)
        agent = self._find_agent_for_transfer(context, is_new_business=True)

        if not agent:
            logger.warning("No agent found for new quote transfer")
            raise ToolError(
                f"No agent found for new quote: insurance_type={context.userdata.insurance_type}, "
                f"business_name={context.userdata.business_name}, "
                f"last_name_spelled={context.userdata.last_name_spelled}"
            )

        # Log the routing decision for Commercial Lines
        log_route_decision(
            intent=CallIntent.NEW_QUOTE,
            agent=agent["name"],
            insurance_type=context.userdata.insurance_type,
            identifier=context.userdata.business_name,
            destination="transfer",
            is_personal=False,
        )

        logger.info(
            f"Transferring new quote call to {agent['name']}: {context.userdata.to_safe_log()}"
        )

        return await self._initiate_transfer(context, agent, "new quote")

    @function_tool
    async def transfer_policy_change(
        self,
        context: RunContext[CallerInfo],
    ) -> str | None:
        """Transfer caller to Account Executive for policy changes.

        REQUIREMENTS BEFORE CALLING:
        - insurance_type must be set (business or personal)
        - For business: business_name must be collected
        - For personal: last_name_spelled must be collected

        Routes to Account Executives via alpha-split:
        - Business (CL): A-F -> Adriana, G-O -> Rayvon, P-Z -> Dionna
        - Personal (PL): A-G -> Yarislyn, H-M -> Al, N-Z -> Luis

        Returns:
            Validation error string if requirements not met, None on successful transfer.
        """
        # Validate requirements
        validation_error = self._validate_transfer_requirements(context)
        if validation_error:
            return validation_error

        # Set call intent
        context.userdata.call_intent = CallIntent.MAKE_CHANGE

        # Find appropriate agent via alpha-split (existing client)
        agent = self._find_agent_for_transfer(context, is_new_business=False)

        if not agent:
            logger.warning("No agent found for policy change transfer")
            raise ToolError(
                f"No agent found for policy change: insurance_type={context.userdata.insurance_type}, "
                f"business_name={context.userdata.business_name}, "
                f"last_name_spelled={context.userdata.last_name_spelled}"
            )

        # Log the routing decision
        identifier = (
            context.userdata.business_name or context.userdata.last_name_spelled
        )
        log_route_decision(
            intent=CallIntent.MAKE_CHANGE,
            agent=agent["name"],
            insurance_type=context.userdata.insurance_type,
            identifier=identifier,
            destination="transfer",
            is_personal=context.userdata.insurance_type == InsuranceType.PERSONAL,
        )

        logger.info(
            f"Transferring policy change call to {agent['name']}: {context.userdata.to_safe_log()}"
        )

        return await self._initiate_transfer(context, agent, "policy change")

    @function_tool
    async def transfer_coverage_question(
        self,
        context: RunContext[CallerInfo],
    ) -> str | None:
        """Transfer caller to Account Executive for coverage or rate questions.

        REQUIREMENTS BEFORE CALLING:
        - insurance_type must be set (business or personal)
        - For business: business_name must be collected
        - For personal: last_name_spelled must be collected

        Routes to Account Executives via alpha-split:
        - Business (CL): A-F -> Adriana, G-O -> Rayvon, P-Z -> Dionna
        - Personal (PL): A-G -> Yarislyn, H-M -> Al, N-Z -> Luis

        Returns:
            Validation error string if requirements not met, None on successful transfer.
        """
        # Validate requirements
        validation_error = self._validate_transfer_requirements(context)
        if validation_error:
            return validation_error

        # Set call intent
        context.userdata.call_intent = CallIntent.COVERAGE_RATE_QUESTIONS

        # Find appropriate agent via alpha-split (existing client)
        agent = self._find_agent_for_transfer(context, is_new_business=False)

        if not agent:
            logger.warning("No agent found for coverage question transfer")
            raise ToolError(
                f"No agent found for coverage question: insurance_type={context.userdata.insurance_type}, "
                f"business_name={context.userdata.business_name}, "
                f"last_name_spelled={context.userdata.last_name_spelled}"
            )

        # Log the routing decision
        identifier = (
            context.userdata.business_name or context.userdata.last_name_spelled
        )
        log_route_decision(
            intent=CallIntent.COVERAGE_RATE_QUESTIONS,
            agent=agent["name"],
            insurance_type=context.userdata.insurance_type,
            identifier=identifier,
            destination="transfer",
            is_personal=context.userdata.insurance_type == InsuranceType.PERSONAL,
        )

        logger.info(
            f"Transferring coverage question call to {agent['name']}: {context.userdata.to_safe_log()}"
        )

        return await self._initiate_transfer(context, agent, "coverage question")

    @function_tool
    async def transfer_payment(
        self,
        context: RunContext[CallerInfo],
    ) -> str | None:
        """Transfer caller to VA ring group for payment or document requests.

        REQUIREMENTS BEFORE CALLING:
        - insurance_type must be set (business or personal)
        - For business: business_name must be collected
        - For personal: last_name_spelled must be collected

        Routing logic:
        1. First try VA ring group (Ann ext 7016, Sheree ext 7008)
        2. If VA unavailable, fall back to Account Executives via alpha-split

        Returns:
            Validation error string if requirements not met, None on successful transfer.
        """
        # Validate requirements
        validation_error = self._validate_transfer_requirements(context)
        if validation_error:
            return validation_error

        # Set call intent
        context.userdata.call_intent = CallIntent.MAKE_PAYMENT

        # Try VA ring group first
        va_group = get_ring_group("VA")
        if va_group and va_group.get("extensions"):
            # Log the routing decision for ring group
            identifier = (
                context.userdata.business_name or context.userdata.last_name_spelled
            )
            log_route_decision(
                intent=CallIntent.MAKE_PAYMENT,
                agent=None,
                insurance_type=context.userdata.insurance_type,
                identifier=identifier,
                destination="ring_group:VA",
                is_personal=context.userdata.insurance_type == InsuranceType.PERSONAL,
            )

            logger.info(
                f"Transferring payment call to VA ring group: {context.userdata.to_safe_log()}"
            )
            return await self._initiate_ring_group_transfer(context, "VA", "payment")

        # Fallback to Account Executive via alpha-split
        logger.info("VA ring group unavailable, falling back to Account Executive")
        agent = self._find_agent_for_transfer(context, is_new_business=False)

        if not agent:
            logger.warning("No agent found for payment transfer fallback")
            raise ToolError(
                f"No agent found for payment (VA unavailable, AE fallback failed): "
                f"insurance_type={context.userdata.insurance_type}, "
                f"business_name={context.userdata.business_name}, "
                f"last_name_spelled={context.userdata.last_name_spelled}"
            )

        # Log the routing decision for AE fallback
        identifier = (
            context.userdata.business_name or context.userdata.last_name_spelled
        )
        log_route_decision(
            intent=CallIntent.MAKE_PAYMENT,
            agent=agent["name"],
            insurance_type=context.userdata.insurance_type,
            identifier=identifier,
            destination="transfer:va_fallback",
            is_personal=context.userdata.insurance_type == InsuranceType.PERSONAL,
        )

        logger.info(
            f"Transferring payment call to {agent['name']} (fallback): {context.userdata.to_safe_log()}"
        )

        return await self._initiate_transfer(context, agent, "payment")

    @function_tool
    async def transfer_something_else(
        self,
        context: RunContext[CallerInfo],
        summary: str | None = None,
    ) -> str | None:
        """Transfer caller to Account Executive for miscellaneous requests.

        This is a WARM TRANSFER - the context/summary is relayed to the agent.

        REQUIREMENTS BEFORE CALLING:
        - insurance_type must be set (business or personal)
        - For business: business_name must be collected
        - For personal: last_name_spelled must be collected
        - summary: Brief description of caller's request (optional but recommended)

        Routes to Account Executives via alpha-split:
        - Business (CL): A-F -> Adriana, G-O -> Rayvon, P-Z -> Dionna
        - Personal (PL): A-G -> Yarislyn, H-M -> Al, N-Z -> Luis

        Args:
            summary: Brief summary of the caller's request for warm transfer context.

        Returns:
            Validation error string if requirements not met, None on successful transfer.
        """
        # Validate requirements
        validation_error = self._validate_transfer_requirements(context)
        if validation_error:
            return validation_error

        # Set call intent and store notes
        context.userdata.call_intent = CallIntent.SOMETHING_ELSE
        if summary:
            context.userdata.additional_notes = summary

        # Find appropriate agent via alpha-split (existing client)
        agent = self._find_agent_for_transfer(context, is_new_business=False)

        if not agent:
            logger.warning("No agent found for 'something else' transfer")
            raise ToolError(
                f"No agent found for 'something else': insurance_type={context.userdata.insurance_type}, "
                f"business_name={context.userdata.business_name}, "
                f"last_name_spelled={context.userdata.last_name_spelled}"
            )

        # Log the routing decision
        identifier = (
            context.userdata.business_name or context.userdata.last_name_spelled
        )
        log_route_decision(
            intent=CallIntent.SOMETHING_ELSE,
            agent=agent["name"],
            insurance_type=context.userdata.insurance_type,
            identifier=identifier,
            destination="transfer:warm",
            is_personal=context.userdata.insurance_type == InsuranceType.PERSONAL,
        )

        # Log with summary for warm transfer context
        log_msg = f"Transferring 'something else' call to {agent['name']}"
        if summary:
            log_msg += f" with summary: {summary}"
        logger.info(f"{log_msg}: {context.userdata.to_safe_log()}")

        # For warm transfer, include context in the message
        return await self._initiate_transfer(context, agent, "other inquiry")
