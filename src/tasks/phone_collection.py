"""Phone number collection via DTMF for SIP/telephony callers.

Uses LiveKit's GetDtmfTask to allow callers to enter their phone number
via keypad tones, with speech fallback for accuracy.
"""

import logging

from livekit import rtc
from livekit.agents import get_job_context

logger = logging.getLogger("agent")


async def collect_phone_number_dtmf(chat_ctx) -> str | None:
    """Collect phone number via DTMF+speech for SIP callers.

    Returns the phone number string, or None if collection failed.
    Uses GetDtmfTask which handles both keypad tones and spoken digits.
    """
    try:
        from livekit.agents.beta.workflows.dtmf_inputs import GetDtmfTask

        result = await GetDtmfTask(
            num_digits=10,
            chat_ctx=chat_ctx.copy(
                exclude_instructions=True,
                exclude_function_call=True,
            ),
            ask_for_confirmation=True,
            extra_instructions=(
                "Let the caller know you'll record their 10-digit phone number "
                "and that they can speak or dial it on their keypad. "
                "Provide an example such as 4-0-7, 5-5-5, 1-2-3-4, then capture the digits."
            ),
        )
        return result.user_input if result else None
    except Exception as e:
        # Beta API - gracefully fall back to speech collection
        logger.debug(f"GetDtmfTask not available or failed: {e}")
        return None


def is_sip_caller() -> bool:
    """Check if the current caller is connected via SIP (telephony)."""
    try:
        ctx = get_job_context()
        for participant in ctx.room.remote_participants.values():
            if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
                return True
    except Exception:
        pass
    return False
