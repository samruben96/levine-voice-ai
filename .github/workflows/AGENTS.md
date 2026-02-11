<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-11 -->

# workflows/

## Purpose
GitHub Actions CI workflows that run on push to `main` and pull requests.

## Key Files

| File | Description |
|------|-------------|
| `ruff.yml` | Linting and formatting checks: `ruff check` and `ruff format --check` on the entire codebase |
| `tests.yml` | Test runner: installs deps with `uv`, runs `ruff check`, `ruff format --check`, then unit tests only (staff directory + agent validation). No integration tests in CI (they require API keys) |

## For AI Agents

### Working In This Directory
- Both workflows use Python 3.12 on `ubuntu-latest`
- Both install deps via `uv sync --dev`
- **CI only runs unit tests** — integration tests require `OPENAI_API_KEY` and are not run in CI
- Ensure `uv run ruff check src/ tests/` and `uv run ruff format --check` pass before committing

### Common Patterns
- Workflows trigger on `push` to `main` and `pull_request` targeting `main`
- Uses `astral-sh/setup-uv@v1` for uv installation
- Uses `actions/setup-python@v4` with Python 3.12

<!-- MANUAL: -->
