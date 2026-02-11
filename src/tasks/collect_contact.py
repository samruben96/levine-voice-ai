"""Contact info collection task using LiveKit's AgentTask pattern.

This module provides a reusable task for collecting caller contact
information (name and phone number) in a structured way.
"""

import logging
from dataclasses import dataclass

from livekit.agents import AgentTask, RunContext, function_tool

from models import CallerInfo
from utils import mask_name, mask_phone

logger = logging.getLogger("agent")


@dataclass
class ContactInfoResult:
    """Result of contact info collection task."""

    first_name: str
    last_name: str
    phone_number: str


class CollectContactInfoTask(AgentTask[ContactInfoResult]):
    """Task to collect caller's name and phone number.

    This task takes temporary control of the session to collect:
    - First name
    - Last name
    - Phone number

    It asks one question at a time and returns a ContactInfoResult
    when all information is collected.

    Example:
        task = CollectContactInfoTask(chat_ctx=session.chat_ctx)
        result = await task
        print(f"Collected: {result.first_name} {result.last_name}")
    """

    def __init__(self, chat_ctx=None):
        super().__init__(
            instructions=(
                "Collect the caller's first name, last name, and phone number. "
                "Ask ONE question at a time. Wait for each answer before asking the next. "
                "Be warm and professional. "
                "After collecting the phone number, call record_contact_info."
            ),
            chat_ctx=chat_ctx,
        )

    async def on_enter(self) -> None:
        """Called when the task becomes active.

        Initiates the contact collection by asking for the caller's name.
        """
        await self.session.generate_reply(
            instructions="Ask for the caller's first and last name."
        )

    @function_tool
    async def record_contact_info(
        self,
        context: RunContext[CallerInfo],
        first_name: str,
        last_name: str,
        phone_number: str,
    ) -> None:
        """Record the caller's name and phone number.

        Call this after collecting first name, last name, and phone number.

        Args:
            first_name: The caller's first name
            last_name: The caller's last name
            phone_number: The caller's phone number for callback
        """
        # Write directly to CallerInfo userdata for compatibility
        context.userdata.first_name = first_name
        context.userdata.last_name = last_name
        context.userdata.name = f"{first_name} {last_name}"
        context.userdata.phone_number = phone_number

        full_name = f"{first_name} {last_name}"
        logger.info(
            f"Contact info collected via task: "
            f"{mask_name(full_name)}, "
            f"{mask_phone(phone_number)}"
        )

        # Complete the task with the result
        self.complete(
            ContactInfoResult(
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
            )
        )
