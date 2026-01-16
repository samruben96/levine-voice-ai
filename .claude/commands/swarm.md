# Swarm - Parallel Multi-Agent Orchestration

Execute complex tasks by decomposing them and running multiple specialized agents in parallel, with MCP tool integration.

## Task to Execute
$ARGUMENTS

## Instructions

You are orchestrating a swarm of specialized agents. Follow this process exactly:

### Step 0: Parse Options

Check if the task includes any flags:
- `--dry-run` or `-d`: Show execution plan without running agents
- `--focus=<phase>`: Only run specific phase (e.g., `--focus=2`)
- `--fast`: Use haiku model for simple subtasks to reduce token usage
- `--no-mcp`: Disable MCP tool usage (agents only)

If `--dry-run` is present, skip to Step 3 and stop after showing the plan.

### MCP Tools Available

The swarm can leverage these MCP tools when beneficial:

#### Documentation & Research
| MCP | Tool | Use For |
|-----|------|---------|
| 🔷 **context7** | `resolve-library-id`, `query-docs` | Look up library documentation (FastAPI, pytest, asyncio, etc.) |
| 🔷 **livekit-docs** | `get_docs_overview` | Get full LiveKit docs structure and table of contents |
| 🔷 **livekit-docs** | `docs_search`, `get_pages` | Search and fetch LiveKit documentation pages |
| 🔷 **livekit-docs** | `get_python_agent_example` | Browse 100+ Python agent examples with full source |
| 🔷 **livekit-docs** | `code_search` | Search LiveKit GitHub repos (agents, SDKs, protocol) |
| 🔷 **livekit-docs** | `get_changelog` | Check recent releases for LiveKit packages |

#### Code Intelligence
| MCP | Tool | Use For |
|-----|------|---------|
| 🔶 **serena** | `find_symbol`, `get_symbols_overview` | Symbolic code navigation and understanding |
| 🔶 **serena** | `replace_symbol_body`, `insert_after_symbol` | Precise code modifications |
| 🔶 **serena** | `find_referencing_symbols`, `rename_symbol` | Find usages, rename across codebase |
| 🔶 **serena** | `search_for_pattern` | Regex search in code and non-code files |
| 🟤 **morph-mcp** | `edit_file` | Fast, accurate file editing (10k+ tokens/sec) |
| 🟤 **morph-mcp** | `warpgrep_codebase_search` | AI-powered codebase search |

#### Browser Testing
| MCP | Tool | Use For |
|-----|------|---------|
| 🟢 **playwright** | `browser_navigate`, `browser_snapshot` | E2E testing, UI verification |
| 🟢 **playwright** | `browser_click`, `browser_type` | Automated user interactions |
| 🔵 **chrome-devtools** | `take_snapshot`, `list_network_requests` | Debug frontend issues |
| 🔵 **chrome-devtools** | `list_console_messages`, `performance_*` | Performance analysis |

#### Problem Solving
| MCP | Tool | Use For |
|-----|------|---------|
| 🟣 **sequential-thinking** | `sequentialthinking` | Complex multi-step reasoning |

**When to use MCPs:**
- 📚 Need library docs → Use **context7** or **livekit-docs** before implementing
- 🔍 Complex code search → Use **morph-mcp** warpgrep or **serena** symbols
- ✏️ Precise edits → Use **serena** symbolic editing or **morph-mcp** edit_file
- 🌐 UI verification → Use **playwright** or **chrome-devtools**
- 🧠 Complex reasoning → Use **sequential-thinking**

### Agent Color Reference

Use these colored indicators for each agent in ALL output:

```
🐍 python-pro (python emoji - primary for Python development)
🎙️ livekit-expert (microphone - primary for LiveKit/voice agents)
💬 conversation-designer (speech bubble - voice UX and dialog flows)
📞 telephony-expert (phone - SIP, transfers, voicemail)
🏢 insurance-specialist (building - insurance domain knowledge)
🏗️ llm-architect (construction - LLM system design)
🔀 fullstack-developer (cross arrows - end-to-end features)
✍️ prompt-engineer (writing - prompts and instructions)
📚 documentation-engineer (books - documentation)
🧪 qa-expert (test tube - testing and quality)
🔍 code-reviewer (magnifying glass - code review)
📊 task-distributor (chart - work distribution)
⚪ Explore, Plan, general-purpose (white/default - built-in agents)
```

### Step 1: Announce Swarm Initiation

Output this EXACT format:

```
╔══════════════════════════════════════════════════════════════╗
║                     🐝 INITIATING SWARM                      ║
╚══════════════════════════════════════════════════════════════╝

Bringing in 📊 task-distributor to assign tasks for:
► "$ARGUMENTS"

⏳ Analyzing task complexity...
```

### Step 2: Call Task Distributor

Use the Task tool to call the **task-distributor** agent with this prompt:

"Analyze and decompose this task into subtasks that can be executed by specialized agents. Identify which agents to use, map dependencies, and determine which tasks can run in parallel.

Task: $ARGUMENTS

Available agents (use subagent_type values):
- Explore: Codebase exploration, finding files, understanding structure
- Plan: Architecture and design planning
- python-pro: Python development, type hints, pytest, async/await, uv package management (PRIMARY for this project)
- livekit-expert: LiveKit Agents framework, voice pipelines, STT/TTS/LLM config, handoffs, rooms (PRIMARY for voice agent work)
- conversation-designer: Voice UX, dialog flows, error recovery, intent handling, turn-taking
- telephony-expert: SIP integration, call transfers, voicemail, DTMF, carrier configs
- insurance-specialist: Insurance domain knowledge, policy types, claims workflows, compliance
- llm-architect: LLM system design, RAG, fine-tuning, model serving, token optimization
- fullstack-developer: End-to-end features, backend to frontend, WebSocket integration
- prompt-engineer: System prompts, few-shot examples, chain-of-thought, token efficiency
- documentation-engineer: API docs, README updates, tutorials, architecture guides
- qa-expert: Test strategy, test planning, coverage analysis, quality gates
- code-reviewer: Security review, performance audit, best practices compliance
- task-distributor: Load balancing, queue management, work distribution
- general-purpose: Complex research, multi-step tasks

Available MCP tools (use when beneficial):
- context7: Library documentation lookup (FastAPI, pytest, asyncio docs)
- livekit-docs: LiveKit-specific documentation (docs_search, get_pages, get_python_agent_example)
- serena: Symbolic code navigation (find_symbol, replace_symbol_body)
- morph-mcp: Smart file editing (edit_file) and search (warpgrep_codebase_search)
- playwright: Browser automation for E2E testing
- chrome-devtools: Frontend debugging and performance
- sequential-thinking: Complex multi-step reasoning

For each subtask, specify:
1. Agent: Which agent handles this (use subagent_type name)
2. Complexity: Low/Medium/High
3. Estimated tokens: Small (<2k), Medium (2-5k), Large (5k+)
4. MCP tools: List SPECIFIC MCP tools that SHOULD be used (be explicit):
   - context7: For looking up library docs (specify which library)
   - livekit-docs: For LiveKit-specific docs and examples
   - serena: For code navigation/editing (specify: find_symbol, replace_symbol_body, etc.)
   - morph-mcp: For file editing (edit_file) or search (warpgrep_codebase_search)
   - playwright: For browser testing (browser_navigate, browser_snapshot, browser_click)
   - chrome-devtools: For frontend debugging (take_snapshot, list_console_messages)
   - sequential-thinking: For complex multi-step reasoning
   - 'none': Only if no MCP tools apply

Be specific about WHY each MCP tool helps the subtask (e.g., 'livekit-docs: Look up voice pipeline configuration').

Provide a clear execution plan with phases, identifying which agents can run in parallel."

### Step 3: Display Execution Plan

After task-distributor responds, output the plan with colors and MCP indicators:

```
╔══════════════════════════════════════════════════════════════╗
║                   📋 SWARM EXECUTION PLAN                    ║
╚══════════════════════════════════════════════════════════════╝

📋 Task: [Brief summary]

┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: [Description]                          [PARALLEL]  │
├─────────────────────────────────────────────────────────────┤
│  🐍 python-pro        │ [task]           │ ~3k tokens    │
│     └─ 🔷 context7: pytest docs                            │
│  🎙️ livekit-expert    │ [task]           │ ~4k tokens    │
│     └─ 🔷 livekit-docs: voice pipeline                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: [Description]                         [SEQUENTIAL] │
├─────────────────────────────────────────────────────────────┤
│  🧪 qa-expert         │ [task]           │ ~2k tokens    │
│     └─ 🟤 morph-mcp: edit_file                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      📊 ESTIMATES                           │
├─────────────────────────────────────────────────────────────┤
│  Agents: [X]  │  Phases: [Y]  │  Est. Tokens: ~[Z]k        │
│  MCPs Used: [N]  │  Parallel Efficiency: [X]%              │
└─────────────────────────────────────────────────────────────┘
```

**Parallel Efficiency** = (Total if sequential - Actual with parallel) / Total if sequential * 100
- Higher is better (more work done in parallel)

**If `--dry-run` was specified, STOP HERE and output:**
```
════════════════════════════════════════════════════════════════
DRY RUN COMPLETE - No agents were deployed
Estimated token usage: ~[X]k tokens
Run without --dry-run to execute this plan
════════════════════════════════════════════════════════════════
```

### Step 4: Deploy Agents

Output:
```
╔══════════════════════════════════════════════════════════════╗
║                    🚀 DEPLOYING AGENTS                       ║
╚══════════════════════════════════════════════════════════════╝
```

### Step 5: Execute Each Phase

For EACH phase, track time and show status with colors:

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: [Description]                                      │
│ Started: [timestamp]  │  Agents: [X]  │  Mode: PARALLEL     │
└─────────────────────────────────────────────────────────────┘

  ⚡ 🐍 python-pro starting...
     └─ Task: [brief description]
     └─ MCPs: 🔷 context7 (docs), 🔶 serena (code)

  ⚡ 🎙️ livekit-expert starting...
     └─ Task: [brief description]
     └─ MCPs: 🔷 livekit-docs (examples)
```

Then launch ALL agents for that phase in a SINGLE message with multiple Task tool calls.

**CRITICAL - MCP TOOL INJECTION**: For EACH agent's Task call, you MUST include MCP instructions in the prompt. Use this template:

```
[Agent's specific task description]

**MCP TOOLS - USE THESE:**
You have access to these MCP tools and SHOULD use them:

[If context7 recommended]
- 🔷 **context7**: Look up library documentation before implementing
  - First call `mcp__context7__resolve-library-id` with the library name
  - Then call `mcp__context7__query-docs` with the resolved ID and your question
  - Example: Look up "pytest fixtures" or "asyncio patterns" docs

[If livekit-docs recommended]
- 🔷 **livekit-docs**: Look up LiveKit-specific documentation and examples
  - `mcp__livekit-docs__get_docs_overview` to see full docs structure
  - `mcp__livekit-docs__docs_search` to search documentation
  - `mcp__livekit-docs__get_pages` to fetch specific doc pages
  - `mcp__livekit-docs__get_python_agent_example` for 100+ Python agent examples
  - `mcp__livekit-docs__code_search` to search LiveKit GitHub repos
  - `mcp__livekit-docs__get_changelog` to check recent releases

[If serena recommended]
- 🔶 **serena**: Use for precise code navigation and editing
  - `mcp__serena__find_symbol` to find functions/classes by name
  - `mcp__serena__get_symbols_overview` for file structure overview
  - `mcp__serena__replace_symbol_body` for precise symbol replacement
  - `mcp__serena__insert_after_symbol` / `insert_before_symbol` to add code
  - `mcp__serena__find_referencing_symbols` to find all usages
  - `mcp__serena__rename_symbol` to rename across codebase
  - `mcp__serena__search_for_pattern` for regex search in code/non-code files

[If morph-mcp recommended]
- 🟤 **morph-mcp**: Use for fast file editing and search
  - `mcp__morph-mcp__edit_file` for efficient edits with minimal context
  - `mcp__morph-mcp__warpgrep_codebase_search` for intelligent code search

[If playwright recommended]
- 🟢 **playwright**: Use for browser automation and testing
  - `mcp__playwright__browser_navigate` to open pages
  - `mcp__playwright__browser_snapshot` to see page structure
  - `mcp__playwright__browser_click` / `browser_type` for interactions

[If chrome-devtools recommended]
- 🔵 **chrome-devtools**: Use for frontend debugging
  - `mcp__chrome-devtools__take_snapshot` for page analysis
  - `mcp__chrome-devtools__list_console_messages` for errors
  - `mcp__chrome-devtools__list_network_requests` for API debugging

[If sequential-thinking recommended]
- 🟣 **sequential-thinking**: Use for complex reasoning
  - `mcp__sequential-thinking__sequentialthinking` for multi-step analysis

**IMPORTANT**: Actively use these MCP tools during your work. They are already available and will improve your output quality.
```

**TOKEN OPTIMIZATION**: If `--fast` flag was used, add `model: "haiku"` to Task calls for Low complexity subtasks.

**MCP SKIP**: If `--no-mcp` flag was used, do NOT include the MCP TOOLS section in agent prompts. Skip all MCP tool injection and proceed with agents using only standard tools.

**CRITICAL**: Launch all phase agents in parallel (multiple Task calls in one message).
**CRITICAL**: Unless `--no-mcp` is set, each Task call MUST include the MCP tool instructions above for tools recommended in the execution plan.

### Step 6: Report Agent Completions

As each agent completes, check its response for MCP tool usage (look for `mcp__` tool calls in the output) and output with color and metrics:

**Detecting MCP usage**: Look for tool calls in the agent's response containing:
- `mcp__context7__` → Report as 🔷 context7
- `mcp__livekit-docs__` → Report as 🔷 livekit-docs
- `mcp__serena__` → Report as 🔶 serena
- `mcp__morph-mcp__` → Report as 🟤 morph-mcp
- `mcp__playwright__` → Report as 🟢 playwright
- `mcp__chrome-devtools__` → Report as 🔵 chrome-devtools
- `mcp__sequential-thinking__` → Report as 🟣 sequential-thinking

```
  ✓ 🐍 python-pro completed
    ├─ Duration: [X]s
    ├─ Result: [1-2 sentence summary]
    ├─ Files: [count] modified
    └─ MCP: 🔷 context7 (looked up pytest fixture docs)
```

If multiple MCPs were used:
```
  ✓ 🎙️ livekit-expert completed
    ├─ Duration: [X]s
    ├─ Result: [1-2 sentence summary]
    ├─ Files: [count] modified
    └─ MCPs: 🔷 livekit-docs (examples), 🔶 serena (find_symbol)
```

If no MCP was used (but was recommended, note this):
```
  ✓ 🧪 qa-expert completed
    ├─ Duration: [X]s
    ├─ Result: [1-2 sentence summary]
    ├─ Files: [count] modified
    └─ MCP: none (recommended: 🔶 serena)
```

If an agent FAILS, output:
```
  ✗ 🐍 python-pro FAILED
    ├─ Duration: [X]s
    ├─ Error: [error description]
    └─ Recovery: [Attempting retry / Skipping / Blocking]
```

### Step 7: Handle Failures

If an agent fails:

1. **Non-critical agent**: Log the failure, continue with remaining agents
```
⚠️  Non-critical failure: 🧪 qa-expert
    Continuing with remaining agents...
```

2. **Critical agent (blocks other phases)**: Attempt ONE retry
```
🔄 Critical failure: 🐍 python-pro
   Attempting retry (1/1)...
```

3. **Retry also fails**: Stop the swarm
```
🛑 SWARM HALTED
   Critical agent 🐍 python-pro failed after retry

   Completed before failure:
   - [list of completed work]

   Manual intervention required for:
   - [remaining tasks]
```

### Step 8: Phase Transitions

Between phases, show metrics:
```
┌─────────────────────────────────────────────────────────────┐
│ ✓ PHASE 1 COMPLETE                                         │
├─────────────────────────────────────────────────────────────┤
│  Duration: [X]s  │  Agents: [Y]  │  Success: [Z]/[Y]       │
│  Files Changed: [N]  │  Lines Modified: ~[M]               │
└─────────────────────────────────────────────────────────────┘

Proceeding to Phase 2...
```

### Step 9: Final Summary

After all phases, show comprehensive metrics:
```
╔══════════════════════════════════════════════════════════════╗
║                    ✅ SWARM COMPLETE                         ║
╚══════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────┐
│                     📊 STATISTICS                           │
├─────────────────────────────────────────────────────────────┤
│  Total Duration     │  [X]s                                 │
│  Agents Deployed    │  [count]                              │
│  Phases Executed    │  [count]                              │
│  Success Rate       │  [X]%                                 │
│  Retries            │  [count]                              │
├─────────────────────────────────────────────────────────────┤
│  Files Changed      │  [count]                              │
│  Lines Added        │  +[count]                             │
│  Lines Removed      │  -[count]                             │
├─────────────────────────────────────────────────────────────┤
│  Parallel Efficiency│  [X]%                                 │
│  Time Saved         │  ~[Y]s (vs sequential)                │
├─────────────────────────────────────────────────────────────┤
│  MCP Tools Used     │  [count]                              │
│  Docs Lookups       │  [count] (context7/livekit-docs)      │
│  Code Navigations   │  [count] (serena)                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   🤖 AGENTS DEPLOYED                        │
├─────────────────────────────────────────────────────────────┤
│  🐍 python-pro         │ ✓ 12s │ Impl feature│ 🔷 context7│
│  🎙️ livekit-expert     │ ✓ 15s │ Voice config│ 🔷 livekit-docs│
│  🧪 qa-expert          │ ✓  8s │ Tests       │ -          │
│  🔍 code-reviewer      │ ✓ 10s │ Review      │ 🔶 serena  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     📋 SUMMARY                              │
├─────────────────────────────────────────────────────────────┤
│  ✓ [Key outcome 1]                                         │
│  ✓ [Key outcome 2]                                         │
│  ✓ [Key outcome 3]                                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   📁 FILES CHANGED                          │
├─────────────────────────────────────────────────────────────┤
│  • src/agents/assistant.py               [+125 lines]      │
│  • tests/integration/test_new_flow.py    [+89 lines]       │
│  • src/staff_directory.py                [+15 lines]       │
└─────────────────────────────────────────────────────────────┘

════════════════════════════════════════════════════════════════
                    All tasks completed successfully.
════════════════════════════════════════════════════════════════
```

## Agent Reference with Colors

### Primary Agents (This Project)
| Color | Agent | Domain | Token Usage |
|-------|-------|--------|-------------|
| 🐍 | **python-pro** | Python development | Medium-Large |
| 🎙️ | **livekit-expert** | Voice AI, LiveKit | Medium-Large |

### Domain-Specific Agents
| Color | Agent | Domain | Token Usage |
|-------|-------|--------|-------------|
| 💬 | **conversation-designer** | Voice UX, dialog flows | Medium |
| 📞 | **telephony-expert** | SIP, transfers, voicemail | Medium |
| 🏢 | **insurance-specialist** | Insurance domain | Medium |

### Specialized Agents
| Color | Agent | Domain | Token Usage |
|-------|-------|--------|-------------|
| 🏗️ | **llm-architect** | LLM systems | Medium-Large |
| 🔀 | **fullstack-developer** | End-to-end | Large |
| ✍️ | **prompt-engineer** | Prompts/instructions | Medium |
| 📚 | **documentation-engineer** | Documentation | Medium |

### Quality & Operations
| Color | Agent | Domain | Token Usage |
|-------|-------|--------|-------------|
| 🧪 | **qa-expert** | Testing/QA | Medium |
| 🔍 | **code-reviewer** | Code quality | Small-Medium |
| 📊 | **task-distributor** | Work distribution | Small-Medium |

### Research & Planning
| Color | Agent | Domain | Token Usage |
|-------|-------|--------|-------------|
| ⚪ | **Explore** | Research | Small |
| ⚪ | **Plan** | Architecture | Medium |
| ⚪ | **general-purpose** | General | Large |

## Token Usage Guide

**Estimated tokens per agent complexity:**
- **Small** (<2k): Simple lookups, small edits, config changes
- **Medium** (2-5k): Feature implementation, component creation
- **Large** (5k+): Complex features, multi-file changes, research

**Tips to reduce token usage:**
1. Use `--fast` flag to use haiku model for simple subtasks
2. Be specific in task description to reduce exploration
3. Use `--focus=N` to run only needed phases
4. Use `--dry-run` first to preview and refine the plan

## Examples

### Standard Execution
```
/swarm Add a new tool function for looking up policy status by policy number
```

### Dry Run (Preview Only)
```
/swarm --dry-run Refactor the ClaimsAgent to support multiple carrier APIs
```

### Fast Mode (Reduced Tokens)
```
/swarm --fast Add a simple greeting variation to the assistant
```

### Focus on Specific Phase
```
/swarm --focus=2 Add voice latency improvements with turn detection tuning
```

### LiveKit-Specific Task
```
/swarm Implement a new sub-agent for handling certificate of insurance requests with proper handoff
```

## Example Output

```
╔══════════════════════════════════════════════════════════════╗
║                     🐝 INITIATING SWARM                      ║
╚══════════════════════════════════════════════════════════════╝

Bringing in 📊 task-distributor to assign tasks for:
► "Add a new tool function for policy status lookup"

⏳ Analyzing task complexity...

╔══════════════════════════════════════════════════════════════╗
║                   📋 SWARM EXECUTION PLAN                    ║
╚══════════════════════════════════════════════════════════════╝

📋 Task: Implement policy status lookup tool with tests

┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: Discovery & Design                     [PARALLEL]  │
├─────────────────────────────────────────────────────────────┤
│  ⚪ Explore              │ Find patterns       │ ~1k tokens │
│  🎙️ livekit-expert       │ Tool patterns       │ ~2k tokens │
│     └─ 🔷 livekit-docs: function_tool examples             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: Implementation                         [PARALLEL]  │
├─────────────────────────────────────────────────────────────┤
│  🐍 python-pro          │ Implement tool      │ ~4k tokens │
│     └─ 🔶 serena: find_symbol, replace_symbol_body         │
│  🧪 qa-expert           │ Write tests         │ ~3k tokens │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: Quality                               [SEQUENTIAL] │
├─────────────────────────────────────────────────────────────┤
│  🔍 code-reviewer       │ Review code         │ ~2k tokens │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      📊 ESTIMATES                           │
├─────────────────────────────────────────────────────────────┤
│  Agents: 5   │  Phases: 3   │  Est. Tokens: ~12k           │
│  MCPs Used: 3  │  Parallel Efficiency: 58%                 │
└─────────────────────────────────────────────────────────────┘

╔══════════════════════════════════════════════════════════════╗
║                    🚀 DEPLOYING AGENTS                       ║
╚══════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: Discovery & Design                                 │
│ Started: 14:32:05  │  Agents: 2  │  Mode: PARALLEL          │
└─────────────────────────────────────────────────────────────┘

  ⚡ ⚪ Explore starting...
     └─ Task: Find existing tool patterns in codebase

  ⚡ 🎙️ livekit-expert starting...
     └─ Task: Research LiveKit function_tool best practices

  ✓ ⚪ Explore completed
    ├─ Duration: 8s
    ├─ Result: Found tool patterns in src/agents/assistant.py
    └─ Files: 0 modified

  ✓ 🎙️ livekit-expert completed
    ├─ Duration: 12s
    ├─ Result: Documented tool function patterns for voice agents
    └─ Files: 0 modified

┌─────────────────────────────────────────────────────────────┐
│ ✓ PHASE 1 COMPLETE                                         │
├─────────────────────────────────────────────────────────────┤
│  Duration: 12s  │  Agents: 2  │  Success: 2/2              │
│  Files Changed: 0  │  Lines Modified: 0                    │
└─────────────────────────────────────────────────────────────┘

Proceeding to Phase 2...
```

Now begin the swarm execution for the provided task.
