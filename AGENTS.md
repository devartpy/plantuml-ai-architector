# Repository Guidelines

## Project Structure & Module Organization

The CLI lives in `src/ai_architect/cli.py`; `core.py` initializes projects and deploys resources. `templates/specs/` holds seven English diagram guides; `templates/skills/` holds four agent workflows. Treat installed templates as read-only defaults. `scripts/validate_specs.py` checks guides. `tests/` covers initialization and evaluation behavior, while `tests/skill_scenarios/` holds synthetic agent cases. `pyproject.toml` configures installation from Git.

Local AI Factory and agent-tool caches may be present during development, but they are not part of the published source tree.

The generated `.ai-architect/config.json` stores the diagram path and renderer URL. Its `mcp-config-example.json` requires manual agent setup.

## Build, Test, and Development Commands

Run these commands from the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install ruff black
.\.venv\Scripts\python.exe -m ruff check src scripts tests
.\.venv\Scripts\python.exe -m ruff format --check src scripts tests
.\.venv\Scripts\python.exe scripts\validate_specs.py
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Install with `.\.venv\Scripts\python.exe -m pip install -e .`, then run `.\.venv\Scripts\ai-architect.exe init --help`. Users install from GitHub; generated wheel and sdist files are not published. Live agent scenarios need `--run` and a reachable renderer.

## Coding Style & Naming Conventions

Target Python 3.10+. Use four-space indentation, 120-character lines, double-quoted strings, `snake_case` for functions and variables, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants.

Ruff checks `E`, `W`, `F`, and `I`, including import sorting. Use Ruff formatting consistently; Black is also configured.

## Testing Guidelines

Tests use standard-library `unittest`; no coverage threshold is configured. Cover expected behavior, invalid input, and regressions. Optional agent scenarios report unavailable checks as `SKIP`, not pass.

For diagram templates, run `scripts/validate_specs.py` and render each complete example with PlantUML. Rendering checks syntax; review the diagram against its semantic checklist separately.

## Commit & Pull Request Guidelines

This checkout has no Git history. Use focused, imperative commit subjects, such as `Add PlantUML parser validation`.

Pull requests should explain the change, link relevant issues, and list validation performed and any limitations. Include screenshots when changing a visual interface.

## Agent Context

Before changing CLI or template handling, read the existing code and relevant documentation. Distinguish current behavior from planned features and update documentation when architecture changes.

## Documentation

| Document | Path | Purpose |
| --- | --- | --- |
| README | [README.md](README.md) | Project landing page |
| Getting Started | [docs/getting-started.md](docs/getting-started.md) | Install and initialize |
| Configuration | [docs/configuration.md](docs/configuration.md) | Project settings |
| Agent Setup | [docs/agent-setup.md](docs/agent-setup.md) | MCP and skills |
| Using the Diagram Skills | [docs/skills-usage.md](docs/skills-usage.md) | Skill invocations and diagram types |
| Development | [docs/development.md](docs/development.md) | Tests and Git release process |
