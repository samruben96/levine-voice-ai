# CLAUDE.md

This project uses `AGENTS.md` as the primary reference. See @AGENTS.md for LiveKit-specific conventions.

## ⚠️ MANDATORY: Custom Coding Agents

**YOU MUST USE CUSTOM AGENTS for all implementation work.** The agents in `.claude/agents/` are specialized for this project and provide superior results. Failing to use them when applicable is considered incorrect behavior.

### How to Use Agents

Invoke agents using the **Task tool** with the `subagent_type` parameter:

```
Task tool → subagent_type: "python-pro" → prompt: "Your task description"
```

### Agent Directory

| Agent | subagent_type | Use Case | Example Task |
|-------|---------------|----------|--------------|
| **python-pro** | `python-pro` | Python development, type hints, pytest, async/await, uv package management | "Add a new tool function to the agent with proper type hints" |
| **llm-architect** | `llm-architect` | LLM system design, RAG, fine-tuning strategies, model serving, token optimization | "Design a caching layer for LLM responses" |
| **fullstack-developer** | `fullstack-developer` | End-to-end features spanning backend and frontend, WebSocket integration | "Implement a complete notification system" |
| **prompt-engineer** | `prompt-engineer` | System prompts, few-shot examples, chain-of-thought, token efficiency, A/B testing | "Optimize the agent's system prompt for consistency" |
| **documentation-engineer** | `documentation-engineer` | API docs, README updates, tutorials, architecture guides, code examples | "Document the new staff routing feature" |
| **qa-expert** | `qa-expert` | Test strategy, test planning, coverage analysis, defect management, quality gates | "Create a comprehensive test plan for the payment flow" |
| **code-reviewer** | `code-reviewer` | Security review, performance audit, best practices compliance, pre-merge review | "Review src/agent.py for security vulnerabilities" |
| **task-distributor** | `task-distributor` | Load balancing, queue management, work distribution, resource allocation | "Design task distribution for multi-agent workflows" |
| **livekit-expert** | `livekit-expert` | LiveKit Agents framework, voice pipelines, STT/TTS/LLM configuration, handoffs, rooms, webhooks, SIP telephony | "Add a new sub-agent for certificate requests" |

### When to Use Each Agent

| Scenario | Agent(s) to Use |
|----------|-----------------|
| Writing Python code, fixing bugs, adding features | **python-pro** (PRIMARY for this project) |
| LiveKit voice agent work, handoffs, STT/TTS/LLM config | **livekit-expert** (PRIMARY for LiveKit-specific work) |
| Modifying agent instructions or prompts | **prompt-engineer** |
| Adding tests or improving test coverage | **qa-expert** + **python-pro** |
| Reviewing code before commit/deploy | **code-reviewer** |
| Creating or updating documentation | **documentation-engineer** |
| Designing LLM pipelines or optimizing costs | **llm-architect** |
| Building features across multiple layers | **fullstack-developer** |
| Distributing work across multiple agents | **task-distributor** |
| Voice latency issues, pipeline optimization | **livekit-expert** |
| SIP telephony setup, webhooks, room configuration | **livekit-expert** |

### Agent Usage Protocol

1. **ALWAYS** evaluate which agent(s) apply before starting work
2. Launch appropriate agent(s) using Task tool with matching `subagent_type`
3. For general Python work, **python-pro** is the PRIMARY agent
4. For LiveKit-specific work (voice pipelines, handoffs, STT/TTS), **livekit-expert** is the PRIMARY agent
5. Use **code-reviewer** after writing significant code
6. Use **qa-expert** when test coverage is needed
7. Update TODO.md after completing work

---

## Persistent Memory

### Task Tracking
- **TODO file**: `TODO.md` - Maintain this document with all tasks, checking off completed items
- Always update TODO.md when starting or completing work

## Project Quick Reference
- Package manager: `uv`
- Run agent: `uv run python src/agent.py dev`
- Run tests: `.venv/bin/python -m pytest tests/`
- Format: `uv run ruff format`
- Lint: `uv run ruff check`
