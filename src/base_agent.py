"""Base routing agent for the Harry Levine Insurance Voice Agent.

This module contains the BaseRoutingAgent class which provides common
transfer and fallback functionality for specialized sub-agents.
"""

import logging

from livekit.agents import Agent, RunContext

from constants import HOLD_MESSAGE
from models import CallerInfo
from utils import mask_name, mask_phone

logger = logging.getLogger("agent")


class BaseRoutingAgent(Agent):
    """Base class for agents that perform call routing and transfers.

    This class provides common implementations for:
    - `_initiate_transfer`: Transfer caller to a staff member with hold message
    - `_handle_fallback`: Handle cases when assigned agent is unavailable
    - `_take_data_sheet`: Collect callback information when no one is available

    Subclasses can customize behavior via class attributes:
    - `transfer_log_prefix`: Prefix for transfer log messages (e.g., "policy change")
    - `fallback_log_context`: Context string for fallback logs (e.g., "for policy change")
    - `datasheet_log_prefix`: Prefix for data sheet logs (e.g., "policy change callback")
    - `datasheet_message`: Custom message returned to caller when taking data sheet
    - `include_notes_in_log`: Whether to include additional_notes in data sheet log

    For warm transfers (where context is relayed to the receiving agent),
    subclasses should override `_initiate_transfer` and set `is_warm_transfer = True`.

    Example:
        class MyCustomAgent(BaseRoutingAgent):
            transfer_log_prefix = "custom request"
            fallback_log_context = "for custom request"
            datasheet_log_prefix = "custom callback"
            datasheet_message = "Custom message for callbacks."

            def __init__(self):
                super().__init__(instructions="Your agent instructions here.")
    """

    # Customizable class attributes for logging and messaging
    transfer_log_prefix: str = ""
    fallback_log_context: str = ""
    datasheet_log_prefix: str = "callback"
    datasheet_message: str = (
        "I apologize, but our agents are currently busy helping other customers. "
        "I have all your information and one of our agents will call you back "
        "as soon as possible. Is there anything else I can note for them?"
    )
    include_notes_in_log: bool = False
    is_warm_transfer: bool = False

    async def _initiate_transfer(
        self, context: RunContext[CallerInfo], agent: dict
    ) -> str:
        """Initiate the transfer to an agent with hold experience.

        TODO: Implement actual SIP transfer when phone system is configured.
        For now, logs the transfer and provides appropriate messaging.

        Args:
            context: The run context containing caller information.
            agent: Staff directory entry with name, ext, department, etc.

        Returns:
            Transfer message with hold instructions.
        """
        agent_name = agent.get("name", "an agent") if isinstance(agent, dict) else agent
        agent_ext = (
            agent.get("ext", "unknown") if isinstance(agent, dict) else "unknown"
        )

        # Log the transfer attempt with extension info (mask PII)
        caller_name = context.userdata.name
        caller_phone = context.userdata.phone_number

        # Build log prefix
        log_prefix = (
            f"Initiating {self.transfer_log_prefix} transfer"
            if self.transfer_log_prefix
            else "Initiating transfer"
        )

        logger.info(
            f"[MOCK TRANSFER] {log_prefix} to {agent_name} (ext {agent_ext}) for caller: "
            f"name={mask_name(caller_name) if caller_name else 'unknown'}, "
            f"phone={mask_phone(caller_phone) if caller_phone else 'unknown'}"
        )

        # Start the on-hold experience
        # In production, this would initiate actual call transfer via SIP
        # using the agent's extension from the staff directory

        # TODO: Implement actual SIP transfer logic using agent["ext"]
        return f"I'm connecting you with {agent_name} now. {HOLD_MESSAGE}"

    async def _handle_fallback(
        self, context: RunContext[CallerInfo], unavailable_agent: str | None
    ) -> str:
        """Handle the fallback when the assigned agent is unavailable.

        Default behavior is to take a data sheet for callback.

        Args:
            context: The run context containing caller information.
            unavailable_agent: Name of the unavailable agent, or None if no agent assigned.

        Returns:
            Message indicating callback will be arranged.
        """
        log_context = (
            f" {self.fallback_log_context}" if self.fallback_log_context else ""
        )

        if unavailable_agent:
            logger.info(
                f"Agent {unavailable_agent} unavailable{log_context}, using fallback: take_data_sheet"
            )
        else:
            logger.info(
                f"No agent assigned{log_context}, using fallback: take_data_sheet"
            )

        return await self._take_data_sheet(context)

    async def _take_data_sheet(self, context: RunContext[CallerInfo]) -> str:
        """Collect information for a callback when no agent is available.

        Logs all relevant caller information for callback purposes.

        Args:
            context: The run context containing caller information.

        Returns:
            Message to the caller about the callback arrangement.
        """
        userdata = context.userdata

        # Build log message
        log_parts = [
            f"Taking data sheet for {self.datasheet_log_prefix}: ",
            f"name={mask_name(userdata.name) if userdata.name else 'unknown'}, ",
            f"phone={mask_phone(userdata.phone_number) if userdata.phone_number else 'unknown'}, ",
            f"type={userdata.insurance_type}, ",
            f"business={userdata.business_name}, ",
            f"last_name={mask_name(userdata.last_name_spelled) if userdata.last_name_spelled else 'unknown'}",
        ]

        if self.include_notes_in_log:
            log_parts.append(
                f", notes={userdata.additional_notes if userdata.additional_notes else 'none'}"
            )

        logger.info("".join(log_parts))
        return self.datasheet_message
