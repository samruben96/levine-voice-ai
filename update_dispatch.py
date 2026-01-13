"""Update dispatch rule to add phone number via LiveKit API."""
import asyncio
import os
from dotenv import load_dotenv
from livekit import api

# Load environment variables
load_dotenv(".env.local")


async def main():
    """Update the dispatch rule to include the phone number."""
    livekit_api = api.LiveKitAPI()

    rule_id = "SDR_rvbFD9LXqpup"
    phone_number = "+14849382056"

    # Create the rule info with numbers field
    rule = api.SIPDispatchRule(
        dispatch_rule_individual=api.SIPDispatchRuleIndividual(
            room_prefix="hli-",
        )
    )

    rule_info = api.SIPDispatchRuleInfo(
        rule=rule,
        name="Harry Levine Inbound",
        numbers=[phone_number],  # This is the key field
        room_config=api.RoomConfiguration(
            agents=[
                api.RoomAgentDispatch(
                    agent_name="Aizellee",
                )
            ]
        ),
    )

    try:
        # Update the dispatch rule using replace action
        result = await livekit_api.sip.update_sip_dispatch_rule(
            rule_id,
            rule_info,
        )
        print(f"Successfully updated dispatch rule: {result}")
    except Exception as e:
        print(f"Error updating dispatch rule: {e}")

    await livekit_api.aclose()


if __name__ == "__main__":
    asyncio.run(main())
