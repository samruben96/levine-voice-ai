# Operations Guide

This guide covers the operational aspects of the Harry Levine Insurance Voice Agent, including staff directory management, routing configuration, deployment procedures, and troubleshooting.

## Table of Contents

- [Telephony Setup](#telephony-setup)
- [Staff Directory Management](#staff-directory-management)
- [Routing Configuration](#routing-configuration)
- [Ring Groups](#ring-groups)
- [Restricted Transfers](#restricted-transfers)
- [Deployment and Rollback](#deployment-and-rollback)
- [Troubleshooting](#troubleshooting)

---

## Telephony Setup

This agent uses LiveKit Phone Numbers for inbound calling. The setup requires three components working together:

1. **LiveKit Phone Number** - The phone number callers dial
2. **SIP Dispatch Rule** - Routes incoming calls to the agent
3. **Agent Registration** - The agent must register with an explicit name

### Current Configuration

| Component | Value |
|-----------|-------|
| Phone Number | +1 (484) 938-2056 |
| Phone Number ID | `PN_PPN_qqYEy29Fwdyq` |
| Dispatch Rule ID | `SDR_9iuRMJaLoJF9` |
| Agent Name | `Aizellee` |
| Room Prefix | `hli-` |

### How It Works

1. Caller dials +1 (484) 938-2056
2. LiveKit matches the phone number ID to the dispatch rule via `trunkIds`
3. Dispatch rule creates a room with prefix `hli-` and dispatches agent `Aizellee`
4. Agent wakes up and handles the call

### Critical: Agent Name Registration

For explicit dispatch to work, the agent **must** register itself with the same name specified in the dispatch rule. This is done in `src/agent.py`:

```python
@server.rtc_session(agent_name="Aizellee")
async def my_agent(ctx: JobContext) -> None:
    ...
```

**Without `agent_name` in the decorator, the dispatch rule cannot find the agent and calls will just ring.**

### Managing Phone Numbers

List phone numbers:
```bash
lk number list
```

Search for available numbers:
```bash
lk number search --country-code US --area-code 484
```

Purchase a new number:
```bash
lk number purchase --numbers +14845550100
```

### Managing Dispatch Rules

List dispatch rules:
```bash
lk sip dispatch list --json
```

Create a dispatch rule (save as `dispatch-rule.json`):
```json
{
  "dispatch_rule": {
    "name": "Harry Levine Inbound",
    "rule": {
      "dispatchRuleIndividual": {
        "roomPrefix": "hli-"
      }
    },
    "roomConfig": {
      "agents": [{
        "agentName": "Aizellee"
      }]
    }
  }
}
```

```bash
lk sip dispatch create dispatch-rule.json
```

Associate dispatch rule with phone number (set trunkIds):
```bash
lk sip dispatch update --id <DISPATCH_RULE_ID> --trunks "<PHONE_NUMBER_ID>"
```

Delete a dispatch rule:
```bash
lk sip dispatch delete <DISPATCH_RULE_ID>
```

### Troubleshooting Telephony

#### Calls Just Ring (Agent Not Answering)

**Most likely cause**: Missing `agent_name` in `@server.rtc_session()` decorator.

**Check**:
1. Verify agent status shows "Running":
   ```bash
   lk agent status
   ```
   - If "Sleeping" or "Pending", the agent isn't registered for explicit dispatch

2. Verify agent code has `agent_name`:
   ```python
   @server.rtc_session(agent_name="Aizellee")  # Required!
   ```

3. Verify dispatch rule has matching agent name:
   ```bash
   lk sip dispatch list --json | grep agentName
   ```

4. Redeploy after fixing:
   ```bash
   lk agent deploy
   ```

#### Dispatch Rule Shows as "Catch-All"

**Cause**: Dispatch rule without `trunkIds` matches all trunks.

**Fix**: Update the dispatch rule to include the phone number ID:
```bash
lk sip dispatch update --id <DISPATCH_RULE_ID> --trunks "<PHONE_NUMBER_ID>"
```

#### Phone Number Not Associated with Dispatch Rule

**Note**: When using `trunkIds` in the dispatch rule, the phone number's "SIP Dispatch Rule" column may appear empty in `lk number list`. This is expected - the routing works via the dispatch rule's `trunkIds` field, not the phone number's dispatch rule assignment.

---

## Staff Directory Management

The staff directory is the source of truth for call routing decisions. It is configured in `src/staff_directory.py`.

### Staff Entry Format

Each staff member is defined with the following fields:

```python
{
    "department": str,      # Department name (e.g., "CL-Account Executive")
    "name": str,           # Full name with optional initial (e.g., "Jason L.")
    "assigned": str,       # Assignment range or role (e.g., "A-F", "CSR", "Platinum")
    "ext": str,            # Phone extension (e.g., "7002")
    "timeBlock": str | None,  # Optional time block (e.g., "9:00-10:00", "12:00-1:00 L")
    "transferable": bool,  # Optional - defaults to True if not specified
}
```

### Current Staff Directory

| Department | Name | Assigned | Extension | Time Block | Transferable |
|------------|------|----------|-----------|------------|--------------|
| Agency Support | Anamer L. | Agency Support | 7013 | 12:00-1:00 L | Yes |
| CL-Account Executive | Adriana | A-F | 7002 | 1:00-2:00 | Yes |
| CL-Account Executive | Rayvon | G-O | 7018 | 9:00-10:00 | Yes |
| CL-Account Executive | Dionna | P-Z | 7006 | 2:00-3:00 | Yes |
| CL-Department Manager | Rachel T. | Platinum | 7005 | 1:00-2:00 | Yes |
| CL-Producer | Kevin K. | Producer | 7003 | - | Yes |
| CL-Service | Stephanie | CSR | 7014 | 2:00-3:00 L | Yes |
| Management | Julie L. | Manager, Admin | 7001 | - | Yes |
| Management | Jason L. | Manager, General | 7000 | - | **No** |
| Management | Kelly U. | Manager, Operations | 7009 | 4:00-5:00 | Yes |
| PL-Account Executive | Yarislyn | A-G | 7011 | 11:00-12:00 | Yes |
| PL-Account Executive | Al | H-M | 7015 | 9:00-10:00 | Yes |
| PL-Account Executive | Luis | N-Z | 7017 | 10:00-11:00 | Yes |
| PL-Sales Agent | Rachel Moreno | A-L | 7010 | - | Yes |
| PL-Sales Agent | Brad | M-Z | 7007 | - | Yes |
| PL-Service | Ann | CSR | 7016 | 1:00-2:00 L | Yes |
| PL-Service | Sheree | CSR | 7008 | 2:00-3:00 L | Yes |
| PL-Special Projects | Fred | - | 7012 | - | **No** |

### Adding a New Staff Member

1. Open `src/staff_directory.py`
2. Add a new entry to the `STAFF_DIRECTORY["staff"]` list:

```python
{
    "department": "PL-Account Executive",
    "name": "New Person",
    "assigned": "A-G",  # Or appropriate alpha range
    "ext": "7020",
    "timeBlock": "10:00-11:00",
    "transferable": True,  # Optional, defaults to True
},
```

3. Update routing if necessary (adjust alpha ranges for other agents)
4. Run tests to verify routing still works correctly:

```bash
uv run pytest tests/test_staff_directory.py -v
```

5. Deploy the updated agent

### Removing a Staff Member

1. Remove the entry from `STAFF_DIRECTORY["staff"]`
2. Reassign their alpha range to another agent
3. If they were in a ring group, update the ring group
4. Run tests and deploy

### Modifying Alpha Ranges

When changing alpha ranges, ensure:

- **No gaps**: Every letter A-Z should route to someone
- **No overlaps**: Each letter should only match one agent
- **Consistency**: CL and PL have different routing structures

Example: To move "H" from Rayvon to Adriana in CL:
- Change Adriana's assigned from "A-F" to "A-H"
- Change Rayvon's assigned from "G-O" to "I-O"

---

## Routing Configuration

### Commercial Lines (CL) Routing

Commercial Lines uses a single alpha-split across Account Executives. Both new business and existing clients follow the same routing.

| Alpha Range | Agent | Extension |
|-------------|-------|-----------|
| A-F | Adriana | 7002 |
| G-O | Rayvon | 7018 |
| P-Z | Dionna | 7006 |
| Platinum | Rachel T. | 7005 |

**Routing key**: First letter of the business name (after handling exception prefixes).

### Personal Lines (PL) Routing

Personal Lines has separate routing for new business vs. existing clients.

#### New Business (Sales Agents)

| Alpha Range | Agent | Extension |
|-------------|-------|-----------|
| A-L | Rachel Moreno | 7010 |
| M-Z | Brad | 7007 |

#### Existing Clients (Account Executives)

| Alpha Range | Agent | Extension |
|-------------|-------|-----------|
| A-G | Yarislyn | 7011 |
| H-M | Al | 7015 |
| N-Z | Luis | 7017 |

**Routing key**: First letter of the caller's last name.

### Alpha Exception Prefixes

Certain business name prefixes are skipped when determining the routing letter:

| Prefix | Example | Routes On |
|--------|---------|-----------|
| "The" | "The Great Company" | G |
| "Law office of" | "Law office of Smith" | S |
| "Law offices of" | "Law Offices of Harry Levine" | H |

These prefixes are case-insensitive.

To add a new exception prefix:

1. Add the prefix to `STAFF_DIRECTORY["alphaExceptionPrefixes"]`:

```python
"alphaExceptionPrefixes": ["The", "Law office of", "Law offices of", "New Prefix"],
```

2. Run tests to verify behavior
3. Deploy

---

## Ring Groups

Ring groups allow multiple extensions to ring simultaneously for specific request types.

### Current Ring Groups

#### VA (Virtual Assistant Team)

- **Purpose**: Payment and ID/Dec requests
- **Extensions**: 7016 (Ann), 7008 (Sheree)
- **Priority**: VA ring group is tried first for payment/document requests, with fallback to Account Executives

### Configuring Ring Groups

Ring groups are defined in `STAFF_DIRECTORY["ringGroups"]`:

```python
"ringGroups": {
    "VA": {
        "name": "Virtual Assistant Team",
        "extensions": ["7016", "7008"],
        "description": "Payment and ID/Dec requests",
    },
    "SALES": {  # Example new ring group
        "name": "Sales Team",
        "extensions": ["7010", "7007"],
        "description": "New business inquiries",
    },
},
```

### Adding a New Ring Group

1. Add a new entry to `STAFF_DIRECTORY["ringGroups"]`
2. Update the agent code in `src/agent.py` to use the new ring group where appropriate
3. Run tests and deploy

---

## Restricted Transfers

Some staff members cannot receive direct transfers from the AI agent. These calls must be handled by a live person first.

### Current Restrictions

| Name | Extension | Reason |
|------|-----------|--------|
| Jason L. | 7000 | Manager, General - requires live person |
| Fred | 7012 | Special Projects - requires live person |

When a caller requests these individuals:
1. The AI informs the caller the person is not available
2. The AI offers to take a message
3. The message is logged for follow-up

### Adding a Restriction

Option 1: Add to the restricted transfers list:

```python
"restrictedTransfers": ["Jason L.", "Fred", "New Person"],
```

Option 2: Set `transferable: False` on the staff entry:

```python
{
    "name": "New Person",
    "transferable": False,
    ...
}
```

### Removing a Restriction

1. Remove the name from `restrictedTransfers` list
2. If the staff entry has `"transferable": False`, change it to `True` or remove the field
3. Run tests and deploy

---

## Deployment and Rollback

### Deployment

Deploy to LiveKit Cloud using the LiveKit CLI:

```bash
# Deploy the current code
lk agent deploy
```

What happens during deployment:
1. **Build**: CLI uploads code and builds container from Dockerfile
2. **Deploy**: New instances launch alongside existing ones
3. **Route**: New sessions go to new instances
4. **Graceful shutdown**: Old instances finish active sessions (up to 1 hour)
5. **Autoscale**: New instances scale based on demand

### Checking Status

```bash
# View current agent status and replica count
lk agent status
```

### Viewing Logs

```bash
# Stream live logs from deployed agent
lk agent logs

# Filter logs (example)
lk agent logs | grep "ERROR"
```

### Rollback

If a deployment causes issues:

```bash
# Rollback to the previous version
lk agent rollback
```

### Version Management

```bash
# List all deployed versions
lk agent versions

# Restart the current agent (without deploying new code)
lk agent restart
```

### Pre-Deployment Checklist

1. Run all tests:
   ```bash
   uv run pytest tests/ -v
   ```

2. Check code formatting:
   ```bash
   uv run ruff format --check
   uv run ruff check
   ```

3. Test locally with console mode:
   ```bash
   uv run python src/agent.py console
   ```

4. Review any changes to:
   - Staff directory entries
   - Alpha ranges
   - Restricted transfers
   - Ring group configurations

---

## Troubleshooting

### Common Issues

#### Call Not Routing to Expected Agent

**Symptoms**: Caller is transferred to wrong agent based on name/business.

**Check**:
1. Verify alpha ranges don't have gaps or overlaps
2. Check if business name has an exception prefix
3. Verify the staff entry exists and has correct `assigned` value

**Debug**:
```bash
# Check routing logic
uv run python -c "
from staff_directory import get_alpha_route_key, find_agent_by_alpha
key = get_alpha_route_key('The Great Company')
print(f'Route key: {key}')
agent = find_agent_by_alpha(key, 'CL', is_new_business=True)
print(f'Agent: {agent}')
"
```

#### Restricted Transfer Not Working

**Symptoms**: AI is transferring to Jason L. or Fred when it shouldn't.

**Check**:
1. Verify name spelling matches exactly in `restrictedTransfers`
2. Check `is_transferable()` function behavior

**Debug**:
```bash
uv run python -c "
from staff_directory import is_transferable
print(f'Jason L.: {is_transferable(\"Jason L.\")}')
print(f'Fred: {is_transferable(\"Fred\")}')
"
```

#### Ring Group Not Being Used

**Symptoms**: Payment requests not going to VA team.

**Check**:
1. Verify VA ring group exists in `STAFF_DIRECTORY["ringGroups"]`
2. Check extensions are correct
3. Verify `get_ring_group("VA")` returns expected data

#### Agent Not Responding

**Symptoms**: Deployed agent not answering calls.

**Check**:
1. Verify deployment status: `lk agent status`
2. Check for errors in logs: `lk agent logs`
3. Verify environment variables are set correctly
4. Check LiveKit Cloud dashboard for connection issues

#### Model Download Issues

**Symptoms**: Agent fails to start, errors about missing models.

**Fix**:
```bash
uv run python src/agent.py download-files
```

### Log Analysis

Key log patterns to look for:

```
# Successful routing
INFO - New quote - Business insurance for: [business] -> [agent] ext [ext]
INFO - Routing to specific agent [name] ext [ext]

# Restricted transfers
INFO - Restricted transfer requested: [name] - offering to take message

# Ring group usage
INFO - [MOCK TRANSFER] Attempting VA ring group: [extensions]

# Fallback behavior
INFO - Agent [name] unavailable, using fallback: [mode]
```

### Test Commands

Run specific test categories:

```bash
# Staff directory tests only
uv run pytest tests/test_staff_directory.py -v

# Agent behavior tests only
uv run pytest tests/test_agent.py -v

# Specific test
uv run pytest tests/test_staff_directory.py::TestFindAgentByAlpha -v

# Tests matching a pattern
uv run pytest tests/ -k "restricted" -v
```

### Getting Help

1. Check [LiveKit Agents Documentation](https://docs.livekit.io/agents/)
2. Review agent logs: `lk agent logs`
3. Run the test suite to identify issues
4. Check the [AGENTS.md](../AGENTS.md) file for project conventions
