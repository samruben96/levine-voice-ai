# CLAUDE.md

This project uses `AGENTS.md` as the primary reference. See @AGENTS.md for LiveKit-specific conventions.

## Persistent Memory

### Task Tracking
- **TODO file**: `TODO.md` - Maintain this document with all tasks, checking off completed items
- Always update TODO.md when starting or completing work

### Custom Coding Agents
Use these agents from `.claude/agents/` for implementation work:

| Agent | File | When to Use |
|-------|------|-------------|
| **python-pro** | `.claude/agents/python-pro.md` | Python development, type hints, pytest, async, uv package management - PRIMARY agent for this project |
| **llm-architect** | `.claude/agents/llm-architect.md` | LLM system design, fine-tuning, RAG, prompt engineering, model optimization |
| **fullstack-developer** | `.claude/agents/fullstack-developer.md` | Complete features spanning multiple layers, end-to-end implementations |
| **prompt-engineer** | `.claude/agents/prompt-engineer.md` | Prompt design, optimization, few-shot learning, chain-of-thought, token efficiency |
| **documentation-engineer** | `.claude/agents/documentation-engineer.md` | Technical documentation, API docs, tutorials, guides, README updates |
| **qa-expert** | `.claude/agents/qa-expert.md` | QA strategy, test planning, test automation, defect management, quality metrics |
| **code-reviewer** | `.claude/agents/code-reviewer.md` | Code review, security vulnerabilities, performance issues, best practices compliance |

### Agent Usage Protocol
1. Evaluate which custom agent(s) apply to the task
2. Launch appropriate agent(s) using Task tool with matching subagent_type
3. For Python/LiveKit work, prefer **python-pro** agent
4. Update TODO.md after completing work

## Project Quick Reference
- Package manager: `uv`
- Run agent: `uv run python src/agent.py dev`
- Run tests: `.venv/bin/python -m pytest tests/`
- Format: `uv run ruff format`
- Lint: `uv run ruff check`
