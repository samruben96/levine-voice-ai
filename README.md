# Harry Levine Insurance Voice Agent

A voice AI front-desk receptionist for Harry Levine Insurance, built with [LiveKit Agents](https://docs.livekit.io/agents/). The agent, named Aizellee, handles incoming calls, routes callers to the appropriate staff member using alpha-split logic, and manages specialized workflows for quotes, payments, and document requests.

## Features

### Intelligent Call Routing

- **Alpha-split routing**: Automatically routes callers to the correct agent based on the first letter of their last name (personal lines) or business name (commercial lines)
- **Intent detection**: Recognizes caller intent across 12 categories including new quotes, payments, claims, policy changes, and more
- **Context-aware insurance type detection**: Infers business vs. personal insurance from context clues (e.g., "office", "company" vs. "car", "home")

### Staff Directory Integration

- **18 staff members** across multiple departments (Commercial Lines, Personal Lines, Management, Support)
- **Department-specific routing**: Different routing rules for CL Account Executives, PL Sales Agents, and PL Account Executives
- **Restricted transfer logic**: Certain staff members (Jason L., Fred) require a live person to answer before transfers

### Direct Transfer Tools

The main Assistant agent handles all routing directly using specialized transfer tools:

- **transfer_new_quote**: Routes new quote requests to sales agents via alpha-split
- **transfer_payment**: Routes payment and document requests to VA ring group or Account Executives
- **transfer_policy_change**: Routes policy change requests to Account Executives
- **transfer_cancellation**: Routes cancellation requests with empathy to Account Executives
- **transfer_coverage_question**: Routes coverage/rate questions to Account Executives
- **transfer_something_else**: Routes other inquiries with warm transfer support
- **handle_bank_caller**: Handles bank representatives calling about mutual customers (provides email, no transfer)

### Specialized Sub-Agents

- **ClaimsAgent**: Handles claims with business hours detection and carrier claims number lookup
- **MortgageeCertificateAgent**: Provides email addresses and self-service options (no transfer)
- **AfterHoursAgent**: Handles after-hours calls with voicemail routing

### Ring Group Support

- **VA (Virtual Assistant) team**: Routes payment and ID/Dec requests to the customer service ring group (Ann ext 7016, Sheree ext 7008)

### Alpha Exception Handling

- Intelligently handles business name prefixes:
  - "The" - Routes on the next word (e.g., "The Great Company" routes on "G")
  - "Law office of" / "Law offices of" - Routes on the following word

## Architecture

```
src/
  __init__.py              # Package init
  models.py                # CallerInfo, CallIntent, InsuranceType
  utils.py                 # PII masking: mask_phone, mask_name
  constants.py             # HOLD_MESSAGE, CARRIER_CLAIMS_NUMBERS
  main.py                  # Server setup, entry point
  agent.py                 # Backwards compatibility wrapper
  instruction_templates.py # Token-optimized instruction fragments
  business_hours.py        # Business hours and timezone handling
  staff_directory.py       # Staff data and routing logic
  agents/
    __init__.py            # Exports all agents
    assistant.py           # Main Assistant (front desk, handles all routing)
    claims.py              # ClaimsAgent (business hours + carrier lookup)
    mortgagee.py           # MortgageeCertificateAgent (email/self-service)
    after_hours.py         # AfterHoursAgent (voicemail routing)

tests/
  conftest.py              # Enhanced shared fixtures
  test_utils.py            # Utility function tests
  unit/                    # Fast unit tests
    test_caller_info.py
    test_phone_validation.py
    test_environment.py
    test_carrier_claims.py
    test_agent_instructions.py
  integration/             # LLM integration tests
    test_greeting.py
    test_security.py
    test_quote_flow.py
    test_payment_flow.py
    test_change_flow.py
    test_cancellation_flow.py
    test_claims_flow.py
    test_coverage_rate.py
    test_something_else.py
    test_mortgagee_cert.py
    test_after_hours.py
  test_agent.py            # Original (kept for compatibility)
  test_staff_directory.py  # Routing logic tests
  test_business_hours.py   # Business hours tests
```

### Agent Hierarchy

```
Agent (LiveKit base)
    |
    +-- Assistant (Main Front Desk - handles all routing directly)
    |       |
    |       +-- transfer_new_quote tool
    |       |       - Collects business/personal info
    |       |       - Routes to sales agents via alpha-split
    |       |
    |       +-- transfer_payment tool
    |       |       - Routes to VA ring group or Account Executives
    |       |
    |       +-- transfer_policy_change tool
    |       |       - Routes to Account Executives via alpha-split
    |       |
    |       +-- transfer_cancellation tool
    |       |       - Shows empathy, routes to Account Executives
    |       |
    |       +-- transfer_coverage_question tool
    |       |       - Routes to Account Executives via alpha-split
    |       |
    |       +-- transfer_something_else tool
    |               - Warm transfer support to Account Executives
    |       |
    |       +-- handle_bank_caller tool
    |               - Handles bank reps about mutual customers
    |               - Provides email address, no transfer
    |
    +-- ClaimsAgent (Claims filing - handoff from Assistant)
    |       - Business hours: empathy + transfer to claims team
    |       - After hours: empathy + carrier claims number lookup
    |
    +-- MortgageeCertificateAgent (Certificates/Mortgagee - handoff from Assistant)
    |       - Provides email addresses for requests
    |       - Offers self-service app option
    |
    +-- AfterHoursAgent (After-hours calls - handoff from Assistant)
            - Collects caller info
            - Routes to voicemail via alpha-split
```

### Architecture Benefits

The single-agent architecture with direct transfer tools provides several advantages:

1. **No double-asking**: Callers are not asked the same questions twice (previously a bug with multi-agent handoffs)
2. **Simpler conversation flow**: All routing logic in one place
3. **Faster response**: No handoff latency between agents
4. **Easier maintenance**: Fewer agent classes to manage

### Call Intent Categories

| Intent | Description | Handling |
|--------|-------------|----------|
| NEW_QUOTE | New insurance quote requests | Direct transfer via `transfer_new_quote` |
| MAKE_PAYMENT | Payments, ID cards, declarations pages | Direct transfer via `transfer_payment` |
| MAKE_CHANGE | Policy modifications | Direct transfer via `transfer_policy_change` |
| CANCELLATION | Policy cancellation requests | Direct transfer via `transfer_cancellation` |
| COVERAGE_RATE_QUESTIONS | Coverage or rate inquiries | Direct transfer via `transfer_coverage_question` |
| POLICY_REVIEW_RENEWAL | Annual reviews and renewals | Direct transfer to Account Executive |
| CLAIMS | Filing claims | Handoff to ClaimsAgent |
| MORTGAGEE_LIENHOLDERS | Mortgagee/lienholder inquiries | Handoff to MortgageeCertificateAgent |
| CERTIFICATES | Certificate of insurance requests | Handoff to MortgageeCertificateAgent |
| BANK_CALLER | Bank reps calling about mutual customers | Direct handling via `handle_bank_caller` |
| HOURS_LOCATION | Office hours and directions | Direct answer (no transfer) |
| SPECIFIC_AGENT | Requests for a specific person | Direct transfer or message |
| SOMETHING_ELSE | Other inquiries | Direct transfer via `transfer_something_else` |

## Quick Start

### Prerequisites

- Python 3.10 - 3.13
- [uv](https://docs.astral.sh/uv/) package manager
- LiveKit Cloud account or self-hosted LiveKit server

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd harry-levine-insurance-voice-agent

# Install dependencies
uv sync
```

### Environment Setup

Copy `.env.example` to `.env.local` and configure:

```bash
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
```

Or use the LiveKit CLI:

```bash
lk cloud auth
lk app env -w -d .env.local
```

### Download Required Models

Before running, download the VAD and turn detector models:

```bash
uv run python src/agent.py download-files
```

### Running the Agent

```bash
# Interactive console mode (for testing)
uv run python src/agent.py console

# Development mode (connects to LiveKit room)
uv run python src/agent.py dev

# Production mode
uv run python src/agent.py start
```

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `LIVEKIT_URL` | LiveKit server WebSocket URL |
| `LIVEKIT_API_KEY` | LiveKit API key |
| `LIVEKIT_API_SECRET` | LiveKit API secret |

### Staff Directory

The staff directory is configured in `src/staff_directory.py`. See [docs/OPERATIONS.md](docs/OPERATIONS.md) for detailed management instructions.

### Deployment Configuration

The `livekit.toml` file contains deployment settings:

```toml
[project]
  subdomain = "your-project-subdomain"

[agent]
  id = "your-agent-id"
  name = "Aizellee"
```

## Testing

The test suite is organized into unit tests (fast, no external APIs) and integration tests (require LLM API access).

### Running Tests

```bash
# Run all tests
uv run pytest tests/

# Run with verbose output
uv run pytest tests/ -v

# Fast unit tests only (~0.1s)
.venv/bin/python -m pytest tests/unit/ -v

# Integration tests only
.venv/bin/python -m pytest tests/integration/ -v

# By marker
.venv/bin/python -m pytest -m unit      # Unit tests only
.venv/bin/python -m pytest -m security  # Security tests only
.venv/bin/python -m pytest -m smoke     # Smoke tests (CI)

# Run specific test file
uv run pytest tests/test_agent.py

# Run specific test
uv run pytest tests/test_agent.py::test_receptionist_greeting
```

### Test Structure

| Directory | Tests | Description |
|-----------|-------|-------------|
| `tests/unit/` | 76 | Fast unit tests, no external API calls |
| `tests/integration/` | 131 | LLM integration tests by feature |
| `tests/test_utils.py` | 63 | Utility function tests |
| `tests/test_staff_directory.py` | 62 | Routing logic tests |
| `tests/test_business_hours.py` | 129 | Business hours tests |
| `tests/test_base_routing.py` | 41 | BaseRoutingAgent tests |
| `tests/test_agent.py` | - | Original file (compatibility) |

### Code Quality

```bash
# Format code
uv run ruff format

# Lint code
uv run ruff check
```

## Deployment

Deploy to LiveKit Cloud using the LiveKit CLI:

```bash
# Deploy the agent
lk agent deploy

# Check deployment status
lk agent status

# View live logs
lk agent logs

# Rollback to previous version
lk agent rollback
```

**Note**: Do NOT use `git push` for deployment. The `lk agent deploy` command builds and deploys directly from your local code.

## Office Information

**Harry Levine Insurance**

- **Hours**: Monday - Friday, 9:00 AM - 5:00 PM
- **Address**: 7208 West Sand Lake Road, Suite 206, Orlando, FL 32819
- **Website**: [harrylevineinsurance.com](https://harrylevineinsurance.com)

### Services Offered

- Home Insurance
- Auto Insurance
- Life Insurance
- Commercial Insurance
- Commercial Fleet Insurance
- Motorcycle Insurance
- Pet Insurance
- Boat Insurance
- RV Insurance
- Renter's Insurance

## Voice Pipeline

The agent uses a voice AI pipeline with:

- **STT (Speech-to-Text)**: AssemblyAI Universal Streaming
- **LLM**: OpenAI GPT-4.1
- **TTS (Text-to-Speech)**: Cartesia Sonic-3
- **Turn Detection**: LiveKit Multilingual Turn Detector
- **VAD**: Silero VAD
- **Noise Cancellation**: LiveKit BVC (Background Voice Cancellation)

## Coding Agents and MCP

This project is designed to work with coding agents like [Cursor](https://www.cursor.com/) and [Claude Code](https://www.anthropic.com/claude-code).

To get the most out of these tools, install the [LiveKit Docs MCP server](https://docs.livekit.io/mcp).

For Cursor, use this link:

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-light.svg)](https://cursor.com/en-US/install-mcp?name=livekit-docs&config=eyJ1cmwiOiJodHRwczovL2RvY3MubGl2ZWtpdC5pby9tY3AifQ%3D%3D)

For Claude Code, run this command:

```bash
claude mcp add --transport http livekit-docs https://docs.livekit.io/mcp
```

The project includes [AGENTS.md](AGENTS.md) with LiveKit-specific conventions for coding assistants.

## Documentation

- [OPERATIONS.md](docs/OPERATIONS.md) - Staff directory management and routing configuration
- [LATENCY_TUNING.md](docs/LATENCY_TUNING.md) - Voice latency optimization parameters and tuning guide
- [BASE_ROUTING_AGENT_DESIGN.md](docs/BASE_ROUTING_AGENT_DESIGN.md) - Historical BaseRoutingAgent design (superseded by single-agent architecture)
- [TEST_RESTRUCTURING_PLAN.md](docs/TEST_RESTRUCTURING_PLAN.md) - Test suite restructuring plan (COMPLETED)
- [PROJECT_STATUS.md](PROJECT_STATUS.md) - Current project status and Phase 1/2 completion report
- [AGENTS.md](AGENTS.md) - LiveKit Agents project conventions
- [LiveKit Agents Documentation](https://docs.livekit.io/agents/)

## Frontend Integration

Compatible with any LiveKit frontend or SIP telephony:

| Platform | Repository |
|----------|------------|
| Web (React) | [agent-starter-react](https://github.com/livekit-examples/agent-starter-react) |
| iOS/macOS | [agent-starter-swift](https://github.com/livekit-examples/agent-starter-swift) |
| Flutter | [agent-starter-flutter](https://github.com/livekit-examples/agent-starter-flutter) |
| React Native | [voice-assistant-react-native](https://github.com/livekit-examples/voice-assistant-react-native) |
| Android | [agent-starter-android](https://github.com/livekit-examples/agent-starter-android) |
| Web Embed | [agent-starter-embed](https://github.com/livekit-examples/agent-starter-embed) |
| Telephony | [SIP Documentation](https://docs.livekit.io/agents/start/telephony/) |

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
