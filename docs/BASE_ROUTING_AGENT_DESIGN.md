# BaseRoutingAgent Design Document

> **Status: SUPERSEDED** (2026-01-14 - Phase 5)
>
> **IMPORTANT:** This design document is kept for historical reference only. The BaseRoutingAgent approach was **replaced by a single-agent architecture** in Phase 5.
>
> ## Why This Was Superseded
>
> The multi-agent handoff system described in this document caused a **"double-asking" bug** where callers were asked the same questions twice after being handed off to a sub-agent. This happened because:
> 1. Sub-agents had their own `on_enter()` methods with separate conversation flows
> 2. Context (CallerInfo) was passed but conversation history was not
> 3. Sub-agents re-confirmed information to be safe
>
> ## Current Architecture (Phase 5)
>
> Instead of multiple routing agents, the **Assistant now handles all routing directly** using transfer tools:
> - `transfer_new_quote` - replaces NewQuoteAgent
> - `transfer_payment` - replaces PaymentIDDecAgent
> - `transfer_policy_change` - replaces MakeChangeAgent
> - `transfer_cancellation` - replaces CancellationAgent
> - `transfer_coverage_question` - replaces CoverageRateAgent
> - `transfer_something_else` - replaces SomethingElseAgent
>
> Only 4 agents remain: Assistant, ClaimsAgent, MortgageeCertificateAgent, AfterHoursAgent
>
> ---
>
> # Historical Documentation (Phases 2-4)
>
> The following was the original design that has been superseded:

---

## Historical: Original Design Summary

## Executive Summary

This document outlines the design for a `BaseRoutingAgent` class to consolidate duplicated transfer/fallback logic across 7+ agent classes in `src/agent.py`. The goal is to reduce code duplication, improve maintainability, and ensure consistent behavior across all routing agents.

## 1. Duplicated Methods Analysis

### 1.1 Methods Found Duplicated Across Agents

The following methods are duplicated across multiple agent classes:

| Method | Description | Found In |
|--------|-------------|----------|
| `_initiate_transfer()` | Initiates SIP transfer to a staff member | NewQuoteAgent, MakeChangeAgent, CancellationAgent, SomethingElseAgent, CoverageRateAgent (5 agents) |
| `_handle_fallback()` | Handles fallback when assigned agent is unavailable | NewQuoteAgent, MakeChangeAgent, CancellationAgent, SomethingElseAgent, CoverageRateAgent (5 agents) |
| `_take_data_sheet()` | Records callback information when no agent available | NewQuoteAgent, MakeChangeAgent, CancellationAgent, SomethingElseAgent, CoverageRateAgent (5 agents) |
| `transfer_to_account_executive()` | @function_tool for transferring to Account Executive | MakeChangeAgent, CancellationAgent, SomethingElseAgent, CoverageRateAgent (4 agents) |
| `record_business_*_info()` | Records business insurance info with alpha-split routing | 8 variants across agents |
| `record_personal_*_info()` | Records personal insurance info with alpha-split routing | 8 variants across agents |

### 1.2 Detailed Duplication Analysis

#### `_initiate_transfer()` - 5 Occurrences

**Pattern observed:**
```python
async def _initiate_transfer(
    self, context: RunContext[CallerInfo], agent: dict
) -> str:
    agent_name = agent.get("name", "an agent") if isinstance(agent, dict) else agent
    agent_ext = agent.get("ext", "unknown") if isinstance(agent, dict) else "unknown"

    # Log transfer attempt (PII masked)
    logger.info(f"[MOCK TRANSFER] Initiating transfer to {agent_name} (ext {agent_ext})...")

    # Return hold message
    return f"I'm connecting you with {agent_name} now. {HOLD_MESSAGE}"
```

**Variations:**
- SomethingElseAgent has additional "warm transfer" context relay logic
- Log messages have different prefixes (e.g., "policy change transfer", "cancellation transfer")

#### `_handle_fallback()` - 5 Occurrences

**Pattern observed:**
```python
async def _handle_fallback(
    self, context: RunContext[CallerInfo], unavailable_agent: str | None
) -> str:
    if unavailable_agent:
        logger.info(f"Agent {unavailable_agent} unavailable, using fallback: take_data_sheet")
    else:
        logger.info("No agent assigned, using fallback: take_data_sheet")

    return await self._take_data_sheet(context)
```

**Variations:**
- Log messages have different context strings (e.g., "for policy change", "for cancellation")
- All currently delegate to `_take_data_sheet()` but TODOs indicate future variations

#### `_take_data_sheet()` - 5 Occurrences

**Pattern observed:**
```python
async def _take_data_sheet(self, context: RunContext[CallerInfo]) -> str:
    userdata = context.userdata
    logger.info(
        f"Taking data sheet for callback: "
        f"name={mask_name(userdata.name)}, phone={mask_phone(userdata.phone_number)}, ..."
    )
    return "I apologize, but [agent] is currently busy... I have all your information..."
```

**Variations:**
- Return messages differ based on context (cancellation asks for reason, coverage asks for question)
- Logging includes different context fields

#### `record_business_*_info()` and `record_personal_*_info()` - 16 Occurrences Total

**Common pattern:**
```python
@function_tool
async def record_business_*_info(
    self, context: RunContext[CallerInfo], business_name: str
) -> str:
    context.userdata.insurance_type = InsuranceType.BUSINESS
    context.userdata.business_name = business_name
    context.userdata.call_intent = CallIntent.*

    route_key = get_alpha_route_key(business_name)
    agent = find_agent_by_alpha(route_key, "CL", is_new_business=True/False)

    if agent:
        context.userdata.assigned_agent = agent["name"]
        logger.info(f"* request - Business: {business_name} -> {agent['name']}")
        return f"Got it, I have this noted for {business_name}. Let me connect you with {agent['name']}."
    else:
        return f"Got it, I have this noted for {business_name}. Let me connect you with your Account Executive."
```

**Variations:**
- `call_intent` differs by agent
- `is_new_business` varies (True for NewQuoteAgent, False for others)
- Return message slightly varies

## 2. Proposed BaseRoutingAgent Class Structure

### 2.1 Class Hierarchy

```
Agent (LiveKit)
    |
    +-- BaseRoutingAgent (NEW)
            |
            +-- NewQuoteAgent
            +-- MakeChangeAgent
            +-- CancellationAgent
            +-- SomethingElseAgent
            +-- CoverageRateAgent
            +-- PaymentIDDecAgent (partial - has custom VA ring group logic)
```

**Note:** The following agents do NOT need BaseRoutingAgent:
- `ClaimsAgent` - Different routing logic (ring group, after-hours carrier lookup)
- `AfterHoursAgent` - Routes to voicemail, not live agents
- `MortgageeCertificateAgent` - No transfer, provides email/self-service info
- `Assistant` - Orchestration agent, doesn't route to staff directly

### 2.2 BaseRoutingAgent Class Definition

```python
from abc import abstractmethod
from typing import TypedDict
from livekit.agents import Agent, RunContext, function_tool

class StaffAgent(TypedDict):
    """Type definition for staff directory entries."""
    name: str
    ext: str
    department: str
    role: str
    alpha_range: str | None
    transferable: bool


class BaseRoutingAgent(Agent):
    """Base class for agents that route callers to staff members via alpha-split.

    Provides common functionality for:
    - SIP transfer initiation
    - Fallback handling when agents are unavailable
    - Data sheet collection for callbacks
    - Business/personal insurance info recording with alpha-split routing

    Subclasses must:
    - Set `_call_intent` for the specific intent type
    - Set `_is_new_business` for alpha-split routing behavior
    - Override `_get_transfer_context()` for custom log messages
    - Override `_get_data_sheet_message()` for custom callback messages

    Attributes:
        _call_intent: The CallIntent enum value for this agent's purpose
        _is_new_business: Whether to route to Sales Agents (True) or Account Executives (False)
        _supports_warm_transfer: Whether this agent relays context during transfer
    """

    # Subclasses should override these class attributes
    _call_intent: CallIntent
    _is_new_business: bool = False  # Default: route to Account Executives
    _supports_warm_transfer: bool = False  # Default: cold transfer

    # --- Core Transfer Methods ---

    async def _initiate_transfer(
        self,
        context: RunContext[CallerInfo],
        agent: StaffAgent,
    ) -> str:
        """Initiate the transfer to a staff member with hold experience.

        Handles logging, PII masking, and generating the transfer message.
        Subclasses can extend this for warm transfer context relay.

        Args:
            context: The run context with caller userdata.
            agent: Staff directory entry with name, ext, department, etc.

        Returns:
            Message to speak while initiating the transfer.
        """
        agent_name = agent.get("name", "an agent")
        agent_ext = agent.get("ext", "unknown")

        transfer_context = self._get_transfer_context()
        caller_name = context.userdata.name
        caller_phone = context.userdata.phone_number

        logger.info(
            f"[MOCK TRANSFER] Initiating {transfer_context} to {agent_name} "
            f"(ext {agent_ext}) for caller: "
            f"name={mask_name(caller_name) if caller_name else 'unknown'}, "
            f"phone={mask_phone(caller_phone) if caller_phone else 'unknown'}"
        )

        if self._supports_warm_transfer:
            await self._relay_warm_transfer_context(context, agent)

        return f"I'm connecting you with {agent_name} now. {HOLD_MESSAGE}"

    async def _relay_warm_transfer_context(
        self,
        context: RunContext[CallerInfo],
        agent: StaffAgent,
    ) -> None:
        """Relay context to receiving agent for warm transfers.

        Override in subclasses that need warm transfer functionality.

        Args:
            context: The run context with caller userdata.
            agent: Staff directory entry for the receiving agent.
        """
        # Default implementation: no-op
        # SomethingElseAgent overrides this to relay caller summary
        pass

    async def _handle_fallback(
        self,
        context: RunContext[CallerInfo],
        unavailable_agent: str | None,
    ) -> str:
        """Handle the fallback when the assigned agent is unavailable.

        Default behavior is to take a data sheet for callback.
        Subclasses can override for different fallback strategies.

        Args:
            context: The run context with caller userdata.
            unavailable_agent: Name of the agent that was unavailable, if any.

        Returns:
            Message explaining the fallback action.
        """
        transfer_context = self._get_transfer_context()

        if unavailable_agent:
            logger.info(
                f"Agent {unavailable_agent} unavailable for {transfer_context}, "
                f"using fallback: take_data_sheet"
            )
        else:
            logger.info(
                f"No agent assigned for {transfer_context}, "
                f"using fallback: take_data_sheet"
            )

        return await self._take_data_sheet(context)

    async def _take_data_sheet(self, context: RunContext[CallerInfo]) -> str:
        """Collect information for a callback when no agent is available.

        Logs all relevant information for callback purposes.
        Subclasses should override `_get_data_sheet_message()` for custom messages.

        Args:
            context: The run context with caller userdata.

        Returns:
            Message explaining the callback process.
        """
        userdata = context.userdata
        transfer_context = self._get_transfer_context()

        logger.info(
            f"Taking data sheet for {transfer_context} callback: "
            f"name={mask_name(userdata.name) if userdata.name else 'unknown'}, "
            f"phone={mask_phone(userdata.phone_number) if userdata.phone_number else 'unknown'}, "
            f"type={userdata.insurance_type}, "
            f"business={userdata.business_name}, "
            f"last_name={mask_name(userdata.last_name_spelled) if userdata.last_name_spelled else 'unknown'}, "
            f"notes={userdata.additional_notes if userdata.additional_notes else 'none'}"
        )

        return self._get_data_sheet_message()

    # --- Abstract/Customization Methods ---

    @abstractmethod
    def _get_transfer_context(self) -> str:
        """Get context string for logging (e.g., 'policy change', 'cancellation').

        Returns:
            String describing the type of transfer for logging purposes.
        """
        ...

    def _get_data_sheet_message(self) -> str:
        """Get the message to return when taking a data sheet.

        Override in subclasses for context-specific messages.

        Returns:
            Message explaining the callback process to the caller.
        """
        return (
            "I apologize, but your Account Executive is currently busy helping other customers. "
            "I have all your information and they will call you back "
            "as soon as possible. Is there anything else I can note for them?"
        )

    # --- Common Recording Methods ---

    async def _record_business_info(
        self,
        context: RunContext[CallerInfo],
        business_name: str,
    ) -> str:
        """Record business insurance information with alpha-split routing.

        Common implementation used by subclass @function_tool methods.

        Args:
            context: The run context with caller userdata.
            business_name: The name of the business.

        Returns:
            Confirmation message with assigned agent name if found.
        """
        context.userdata.insurance_type = InsuranceType.BUSINESS
        context.userdata.business_name = business_name
        context.userdata.call_intent = self._call_intent

        route_key = get_alpha_route_key(business_name)
        agent = find_agent_by_alpha(route_key, "CL", is_new_business=self._is_new_business)

        transfer_context = self._get_transfer_context()

        if agent:
            context.userdata.assigned_agent = agent["name"]
            logger.info(
                f"{transfer_context.title()} - Business: {business_name} "
                f"(route key: {route_key}) -> {agent['name']} ext {agent['ext']}"
            )
            return self._get_business_confirmation_message(business_name, agent["name"])
        else:
            logger.info(f"{transfer_context.title()} - Business: {business_name} (no agent found)")
            return self._get_business_confirmation_message(business_name, None)

    async def _record_personal_info(
        self,
        context: RunContext[CallerInfo],
        last_name_spelled: str,
    ) -> str:
        """Record personal insurance information with alpha-split routing.

        Common implementation used by subclass @function_tool methods.

        Args:
            context: The run context with caller userdata.
            last_name_spelled: The caller's last name as spelled.

        Returns:
            Confirmation message with assigned agent name if found.
        """
        context.userdata.insurance_type = InsuranceType.PERSONAL
        context.userdata.last_name_spelled = last_name_spelled
        context.userdata.call_intent = self._call_intent

        first_letter = (
            last_name_spelled[0].upper()
            if last_name_spelled and len(last_name_spelled) > 0
            else "A"
        )
        agent = find_agent_by_alpha(first_letter, "PL", is_new_business=self._is_new_business)

        transfer_context = self._get_transfer_context()

        if agent:
            context.userdata.assigned_agent = agent["name"]
            logger.info(
                f"{transfer_context.title()} - Personal, last name: {mask_name(last_name_spelled)} "
                f"(letter: {first_letter}) -> {agent['name']} ext {agent['ext']}"
            )
            return self._get_personal_confirmation_message(last_name_spelled, agent["name"])
        else:
            logger.info(
                f"{transfer_context.title()} - Personal, last name: {mask_name(last_name_spelled)} "
                f"(no agent found)"
            )
            return self._get_personal_confirmation_message(last_name_spelled, None)

    def _get_business_confirmation_message(
        self,
        business_name: str,
        agent_name: str | None,
    ) -> str:
        """Get confirmation message for business info recording.

        Override in subclasses for custom confirmation messages.

        Args:
            business_name: The recorded business name.
            agent_name: The assigned agent name, or None if no agent found.

        Returns:
            Confirmation message to speak to the caller.
        """
        if agent_name:
            return f"Got it, I have this noted for {business_name}. Let me connect you with {agent_name}, your Account Executive."
        return f"Got it, I have this noted for {business_name}. Let me connect you with your Account Executive."

    def _get_personal_confirmation_message(
        self,
        last_name_spelled: str,
        agent_name: str | None,
    ) -> str:
        """Get confirmation message for personal info recording.

        Override in subclasses for custom confirmation messages.

        Args:
            last_name_spelled: The recorded last name.
            agent_name: The assigned agent name, or None if no agent found.

        Returns:
            Confirmation message to speak to the caller.
        """
        if agent_name:
            return f"Thank you, I have that as {last_name_spelled}. Let me connect you with {agent_name}, your Account Executive."
        return f"Thank you, I have that as {last_name_spelled}. Let me connect you with your Account Executive."

    # --- Common Transfer Execution ---

    async def _execute_transfer_to_account_executive(
        self,
        context: RunContext[CallerInfo],
    ) -> str:
        """Execute the transfer to Account Executive using alpha-split routing.

        Common implementation for the transfer_to_account_executive tool.
        Handles both business and personal insurance types.

        Args:
            context: The run context with caller userdata.

        Returns:
            Transfer message or fallback message.
        """
        userdata = context.userdata
        transfer_context = self._get_transfer_context()

        if userdata.insurance_type == InsuranceType.BUSINESS:
            agent_name = userdata.assigned_agent
            if agent_name:
                agent = get_agent_by_name(agent_name)
                if agent:
                    logger.info(f"Transferring {transfer_context} to {agent['name']} ext {agent['ext']}")
                    return await self._initiate_transfer(context, agent)
            logger.info(f"Transferring {transfer_context} - no agent assigned, using fallback")
            return await self._handle_fallback(context, None)

        elif userdata.insurance_type == InsuranceType.PERSONAL:
            agent_name = userdata.assigned_agent
            if agent_name:
                agent = get_agent_by_name(agent_name)
                if agent:
                    logger.info(f"Transferring {transfer_context} to {agent['name']} ext {agent['ext']}")
                    return await self._initiate_transfer(context, agent)
                else:
                    return await self._handle_fallback(context, agent_name)
            else:
                return await self._handle_fallback(context, None)

        return f"I'll connect you with your Account Executive who can help."
```

### 2.3 Method Signatures Summary

| Method | Signature | Purpose |
|--------|-----------|---------|
| `_initiate_transfer` | `async (context, agent) -> str` | Core SIP transfer logic |
| `_relay_warm_transfer_context` | `async (context, agent) -> None` | Hook for warm transfer |
| `_handle_fallback` | `async (context, unavailable_agent) -> str` | Fallback when agent unavailable |
| `_take_data_sheet` | `async (context) -> str` | Record callback info |
| `_get_transfer_context` | `() -> str` | **ABSTRACT** - context string for logs |
| `_get_data_sheet_message` | `() -> str` | Customizable callback message |
| `_record_business_info` | `async (context, business_name) -> str` | Common business recording |
| `_record_personal_info` | `async (context, last_name_spelled) -> str` | Common personal recording |
| `_get_business_confirmation_message` | `(business_name, agent_name) -> str` | Customizable confirmation |
| `_get_personal_confirmation_message` | `(last_name_spelled, agent_name) -> str` | Customizable confirmation |
| `_execute_transfer_to_account_executive` | `async (context) -> str` | Common transfer execution |

## 3. Sub-Agent Inheritance Examples

### 3.1 MakeChangeAgent (Standard Pattern)

```python
class MakeChangeAgent(BaseRoutingAgent):
    """Specialized agent for handling policy change and modification requests."""

    _call_intent = CallIntent.MAKE_CHANGE
    _is_new_business = False  # Existing clients go to Account Executives
    _supports_warm_transfer = False

    def __init__(self) -> None:
        super().__init__(
            instructions="""You are Aizellee, helping a caller who wants to make changes to their policy..."""
        )

    def _get_transfer_context(self) -> str:
        return "policy change"

    def _get_data_sheet_message(self) -> str:
        return (
            "I apologize, but your Account Executive is currently busy helping other customers. "
            "I have all your information and they will call you back "
            "as soon as possible. Is there anything else I can note for them about the changes you need?"
        )

    async def on_enter(self) -> None:
        self.session.generate_reply(
            instructions="""Check if the caller already indicated business or personal context..."""
        )

    @function_tool
    async def record_business_change_info(
        self, context: RunContext[CallerInfo], business_name: str
    ) -> str:
        """Record business insurance policy change information."""
        return await self._record_business_info(context, business_name)

    @function_tool
    async def record_personal_change_info(
        self, context: RunContext[CallerInfo], last_name_spelled: str
    ) -> str:
        """Record personal insurance policy change information."""
        return await self._record_personal_info(context, last_name_spelled)

    @function_tool
    async def transfer_to_account_executive(self, context: RunContext[CallerInfo]) -> str:
        """Transfer the caller to their Account Executive for policy changes."""
        return await self._execute_transfer_to_account_executive(context)
```

### 3.2 CancellationAgent (Custom Data Sheet Message)

```python
class CancellationAgent(BaseRoutingAgent):
    """Specialized agent for handling policy cancellation requests."""

    _call_intent = CallIntent.CANCELLATION
    _is_new_business = False
    _supports_warm_transfer = False

    def __init__(self) -> None:
        super().__init__(
            instructions="""You are Aizellee, helping a caller who wants to cancel their policy..."""
        )

    def _get_transfer_context(self) -> str:
        return "cancellation"

    def _get_data_sheet_message(self) -> str:
        # Custom message that asks for cancellation reason
        return (
            "I apologize, but your Account Executive is currently busy helping other customers. "
            "I have all your information and they will call you back "
            "as soon as possible. Before I let you go, may I ask the reason for the cancellation "
            "so I can note it for them? And is there a preferred time for them to call you back?"
        )

    # ... rest of implementation
```

### 3.3 SomethingElseAgent (Warm Transfer)

```python
class SomethingElseAgent(BaseRoutingAgent):
    """Specialized agent for handling requests that don't fit other categories."""

    _call_intent = CallIntent.SOMETHING_ELSE
    _is_new_business = False
    _supports_warm_transfer = True  # Enable warm transfer

    def __init__(self) -> None:
        super().__init__(
            instructions="""You are Aizellee, helping a caller whose request doesn't fit standard categories..."""
        )

    def _get_transfer_context(self) -> str:
        return "other request"

    async def _relay_warm_transfer_context(
        self, context: RunContext[CallerInfo], agent: StaffAgent
    ) -> None:
        """Relay caller summary to receiving agent for warm transfer."""
        caller_name = context.userdata.name or "a caller"
        summary = context.userdata.additional_notes or "a general inquiry"
        agent_name = agent.get("name", "an agent")

        warm_transfer_intro = (
            f"Hi {agent_name}, I have {caller_name} on the line. "
            f"They're calling about {summary}."
        )
        logger.info(f"[WARM TRANSFER CONTEXT] {warm_transfer_intro}")
        # TODO: Implement actual SIP warm transfer context relay

    @function_tool
    async def record_request_summary(
        self, context: RunContext[CallerInfo], summary: str
    ) -> str:
        """Record a summary of what the caller is calling about."""
        context.userdata.additional_notes = summary
        context.userdata.call_intent = CallIntent.SOMETHING_ELSE
        logger.info(f"Recorded request summary: {summary[:100]}...")
        return f"Got it, I understand you're calling about {summary}. Let me get you to the right person."

    # ... rest of implementation
```

### 3.4 NewQuoteAgent (New Business Routing)

```python
class NewQuoteAgent(BaseRoutingAgent):
    """Specialized agent for handling new quote requests."""

    _call_intent = CallIntent.NEW_QUOTE
    _is_new_business = True  # Routes to Sales Agents instead of Account Executives
    _supports_warm_transfer = False

    def __init__(self) -> None:
        super().__init__(
            instructions="""You are Aizellee, helping a caller who wants a new insurance quote..."""
        )

    def _get_transfer_context(self) -> str:
        return "new quote"

    def _get_business_confirmation_message(self, business_name: str, agent_name: str | None) -> str:
        # Custom message for new business quotes
        if agent_name:
            return f"Got it, I have this noted for {business_name}. Let me connect you with {agent_name}."
        return f"Got it, I have this noted for {business_name}. Let me connect you with one of our commercial insurance specialists."

    def _get_personal_confirmation_message(self, last_name_spelled: str, agent_name: str | None) -> str:
        # Custom message for new personal quotes
        if agent_name:
            return f"Thank you, I have that as {last_name_spelled}. Let me connect you with {agent_name}."
        return f"Thank you, I have that as {last_name_spelled}. Let me connect you with one of our agents."

    # ... rest of implementation
```

## 4. LiveKit-Specific Considerations

### 4.1 Agent Inheritance

LiveKit Agents framework supports class inheritance from the `Agent` base class. Key considerations:

1. **`super().__init__(instructions=...)`** - Must call parent constructor with instructions
2. **`on_enter()`** - Can be overridden for greeting/initialization behavior
3. **`on_exit()`** - Can be overridden for cleanup when handing off
4. **`@function_tool`** - Decorators must be on concrete class methods, not inherited
5. **`self.session`** - Access to AgentSession for generating replies

### 4.2 Function Tools Cannot Be Inherited

**Important:** The `@function_tool` decorator registers methods at class definition time. This means:

- Tool methods **cannot be inherited** from a base class
- Each subclass must define its own `@function_tool` decorated methods
- Base class can provide helper methods that tools call

**Solution:** BaseRoutingAgent provides `_record_business_info()` and `_record_personal_info()` helper methods. Subclasses create thin `@function_tool` wrappers:

```python
# In subclass
@function_tool
async def record_business_change_info(self, context, business_name: str) -> str:
    """Record business insurance policy change information."""
    return await self._record_business_info(context, business_name)  # Delegate to base
```

### 4.3 RunContext Type Parameter

The `RunContext[CallerInfo]` type parameter ensures:
- Type safety for `context.userdata` access
- Proper IDE autocompletion
- Runtime validation of userdata structure

All inherited methods must maintain this type parameter:

```python
async def _initiate_transfer(
    self,
    context: RunContext[CallerInfo],  # Type parameter preserved
    agent: StaffAgent,
) -> str:
    ...
```

### 4.4 Handoff Compatibility

BaseRoutingAgent subclasses are fully compatible with LiveKit handoffs:
- Can be returned from `@function_tool` methods in other agents
- Properly initialize with their own instructions
- Support `on_enter()` for post-handoff initialization

## 5. Migration Plan

> **Note:** This migration plan has been COMPLETED. All phases below have been implemented.

### 5.1 Phase 1: Create BaseRoutingAgent (PR #1) - COMPLETED

1. Add `BaseRoutingAgent` class to `src/agent.py`
2. Add `StaffAgent` TypedDict for type safety
3. Add comprehensive docstrings and type hints
4. Write unit tests for base class methods

**Files changed:**
- `src/agent.py` (add BaseRoutingAgent class) - Lines 512-646
- `tests/test_base_routing.py` (NEW - 41 tests for BaseRoutingAgent)

### 5.2 Phase 2: Migrate MakeChangeAgent (PR #2) - COMPLETED

1. Refactor `MakeChangeAgent` to inherit from `BaseRoutingAgent`
2. Remove duplicated methods
3. Verify all existing tests pass
4. Add any new tests for edge cases

**Implementation:** MakeChangeAgent now inherits from BaseRoutingAgent with custom `transfer_log_prefix="policy change"` and `fallback_log_context="for policy change"`.

### 5.3 Phase 3: Migrate CancellationAgent (PR #3) - COMPLETED

1. Refactor `CancellationAgent` to inherit from `BaseRoutingAgent`
2. Override `_get_data_sheet_message()` for custom cancellation message
3. Verify all existing tests pass

**Implementation:** CancellationAgent uses `include_notes_in_log=True` to capture cancellation reasons.

### 5.4 Phase 4: Migrate CoverageRateAgent (PR #4) - COMPLETED

1. Refactor `CoverageRateAgent` to inherit from `BaseRoutingAgent`
2. Override `_get_data_sheet_message()` for coverage question message
3. Verify all existing tests pass

**Implementation:** Clean inheritance with custom log prefixes for "coverage/rate question".

### 5.5 Phase 5: Migrate SomethingElseAgent (PR #5) - COMPLETED

1. Refactor `SomethingElseAgent` to inherit from `BaseRoutingAgent`
2. Override `_relay_warm_transfer_context()` for warm transfer
3. Keep `record_request_summary()` as a unique tool
4. Verify all existing tests pass

**Implementation:** SomethingElseAgent sets `is_warm_transfer=True` and overrides `_initiate_transfer` for warm transfer context relay.

### 5.6 Phase 6: Migrate NewQuoteAgent (PR #6) - COMPLETED

1. Refactor `NewQuoteAgent` to inherit from `BaseRoutingAgent`
2. Set `_is_new_business = True` for Sales Agent routing
3. Override confirmation message methods
4. Keep `transfer_to_sales_agent()` (different name from other agents)
5. Verify all existing tests pass

**Implementation:** First agent refactored, served as template for others.

### 5.7 Phase 7: Consider PaymentIDDecAgent (PR #7 - SKIPPED BY DESIGN)

PaymentIDDecAgent has unique VA ring group priority logic. Decision:
- **Keep PaymentIDDecAgent as-is** - Its routing pattern (VA ring group first, alpha-split fallback) differs significantly from the standard alpha-split-first pattern used by BaseRoutingAgent subclasses.

## 6. Code Reduction Results

> **Actual Results:** Phase 2 achieved ~325 lines saved across 5 agents, with ~192 net reduction after accounting for the new BaseRoutingAgent class (~133 lines).

| Agent | Before LOC | After LOC | Reduction |
|-------|------------|-----------|-----------|
| NewQuoteAgent | ~185 | ~120 | ~65 lines |
| MakeChangeAgent | ~190 | ~125 | ~65 lines |
| CancellationAgent | ~205 | ~140 | ~65 lines |
| SomethingElseAgent | ~220 | ~155 | ~65 lines |
| CoverageRateAgent | ~195 | ~130 | ~65 lines |
| **Total Saved** | | | **~325 lines** |
| BaseRoutingAgent (new) | | ~133 | (added) |
| **Net Reduction** | | | **~192 lines** |

## 7. Testing Strategy

### 7.1 Base Class Tests

```python
class TestBaseRoutingAgent:
    """Tests for BaseRoutingAgent functionality."""

    async def test_initiate_transfer_logs_correctly(self):
        """Verify transfer logging with PII masking."""
        ...

    async def test_handle_fallback_calls_take_data_sheet(self):
        """Verify fallback behavior delegates to data sheet."""
        ...

    async def test_take_data_sheet_logs_all_fields(self):
        """Verify data sheet logging includes all userdata fields."""
        ...

    async def test_record_business_info_sets_intent(self):
        """Verify business info recording sets correct call_intent."""
        ...

    async def test_record_personal_info_alpha_routing(self):
        """Verify personal info uses correct alpha-split routing."""
        ...
```

### 7.2 Subclass Tests

Each subclass should have tests for:
- Correct `_call_intent` value
- Correct `_is_new_business` value
- Custom `_get_transfer_context()` return value
- Custom `_get_data_sheet_message()` return value (if overridden)
- Any unique tool methods

## 8. Open Questions / Future Considerations

1. **SIP Transfer Implementation:** When real SIP transfer is implemented, should `_initiate_transfer()` become async with actual connection logic?

2. **Fallback Strategy Configuration:** TODOs indicate future fallback options (ring all AEs, specific backup). Should this be configurable per-agent or globally?

3. **PaymentIDDecAgent:** Should this get its own base class (`BaseRingGroupAgent`) or remain standalone?

4. **Metrics/Monitoring:** Should transfer attempts be tracked for metrics? If so, add hooks in BaseRoutingAgent.

5. **Hold Timeout:** TODOs mention client input needed for hold timeout before fallback. When this is defined, update `_handle_fallback()`.

---

## Appendix A: Full Method Duplication Audit

### A.1 `_initiate_transfer()` Implementations

| Agent | Line | Key Differences |
|-------|------|-----------------|
| NewQuoteAgent | 684-715 | Standard implementation |
| MakeChangeAgent | 1145-1175 | Adds "policy change" to log |
| CancellationAgent | 1436-1466 | Adds "cancellation" to log |
| SomethingElseAgent | 2231-2277 | Adds warm transfer context relay |
| CoverageRateAgent | 2551-2581 | Adds "coverage/rate question" to log |

### A.2 `_handle_fallback()` Implementations

| Agent | Line | Key Differences |
|-------|------|-----------------|
| NewQuoteAgent | 717-731 | Standard implementation |
| MakeChangeAgent | 1177-1199 | Different log context string |
| CancellationAgent | 1468-1489 | Different log context string |
| SomethingElseAgent | 2279-2300 | Different log context string |
| CoverageRateAgent | 2583-2604 | Different log context string |

### A.3 `_take_data_sheet()` Implementations

| Agent | Line | Key Differences |
|-------|------|-----------------|
| NewQuoteAgent | 733-748 | Generic callback message |
| MakeChangeAgent | 1201-1219 | Asks about changes needed |
| CancellationAgent | 1491-1517 | Asks for cancellation reason |
| SomethingElseAgent | 2302-2327 | Includes request summary context |
| CoverageRateAgent | 2606-2632 | Asks for coverage question |

---

## Implementation Reference

The BaseRoutingAgent implementation can be found at:
- **Class definition:** `src/base_agent.py` (161 lines) - *Moved from src/agent.py in Phase 3*
- **Test suite:** `tests/test_base_routing.py` (41 tests)
- **Project status:** See `PROJECT_STATUS.md` for Phase 2 and Phase 3 completion details

### Phase 3 Module Locations

| Component | Location |
|-----------|----------|
| BaseRoutingAgent | `src/base_agent.py` |
| CallerInfo, CallIntent, InsuranceType | `src/models.py` |
| mask_phone, mask_name | `src/utils.py` |
| HOLD_MESSAGE | `src/constants.py` |
| NewQuoteAgent | `src/agents/quote.py` |
| MakeChangeAgent | `src/agents/changes.py` |
| CancellationAgent | `src/agents/cancellation.py` |
| SomethingElseAgent | `src/agents/something_else.py` |
| CoverageRateAgent | `src/agents/coverage.py` |

---

**Document Version:** 1.3 (Marked as SUPERSEDED - Phase 5 single-agent architecture)
**Created:** 2026-01-13
**Updated:** 2026-01-14
**Author:** Claude Opus 4.5 (via livekit-expert agent)

---

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) - Current single-agent architecture documentation
- [PROJECT_STATUS.md](../PROJECT_STATUS.md) - Phase 5 completion details
