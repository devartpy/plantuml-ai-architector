[← Using Skills](skills-usage.md) · [Back to README](../README.md)

# Development

## Source Layout

| Path | Purpose |
| --- | --- |
| `src/ai_architect/cli.py` | Argument parsing and colored command output |
| `src/ai_architect/core.py` | Config validation and resource deployment |
| `templates/specs/` | Selection matrix and seven English diagram guides |
| `templates/skills/` | Create, modify, verify, and self-correct workflows |
| `scripts/validate_specs.py` | Specification links, sections, and example checks |
| `scripts/evaluate_self_correct.py` | Optional live-agent correction scenarios |
| `tests/test_init.py`, `tests/test_evaluation.py` | Standard-library `unittest` behavior tests |
| `tests/skill_scenarios/` | Synthetic diagrams and expected agent outcomes |

Setuptools maps `templates/` into `ai_architect.templates` package resources.
The installed template resources are inputs; user diagrams belong in the target
project. The two copied directories under `.ai-architect/` are managed and get
replaced on repeat `init` runs.
The `self-correct` workflow writes verified, type-specific rules only under the
user project's preserved `.ai-architect/references/` directory; it never edits
packaged specifications. Agent discovery remains a client setup step.

## Local Setup and Checks

From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m pip install ruff
.\.venv\Scripts\python.exe -m ruff check src scripts tests
.\.venv\Scripts\python.exe -m ruff format --check src scripts tests
.\.venv\Scripts\python.exe scripts\validate_specs.py
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

The specification script checks Markdown structure and complete PlantUML
example blocks, but not rendered syntax or semantic correctness. Render complete
examples with PlantUML MCP or a local renderer, then review their modeling rules
separately. No coverage threshold is configured. See [AGENTS.md](../AGENTS.md)
for style and contribution guidance.

The published artifact is the Git source tree. Before pushing, verify a regular
`pip install .` from this checkout in a clean virtual environment and run its
`ai-architect init` command from another directory. Pip builds its temporary
installation wheel automatically; do not commit generated archives or `dist/`.

To evaluate agent instructions against a reachable local or internal PlantUML
renderer, install Codex CLI and Node.js/npm, then explicitly run:

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_self_correct.py --run --renderer-url http://127.0.0.1:18080
```

The runner creates isolated projects and checks seven synthetic scenarios,
including correction, duplicate-rule prevention, conflicting requirements, renderer
outage, semantic failure, read-only verification, and a pre-existing error.
It launches Codex and `npx` for each scenario; agent runs may use a remote model
and take several minutes. Without `--run`, Codex, `npx`, or a reachable renderer,
it prints `SKIP` and exits with code 2; that is **not** evidence that agent behavior passed.
The runner independently counts distinct changed candidates in Codex JSONL MCP
calls and rejects any unexpected changes in the isolated project. The three-attempt
limit is covered by deterministic regression tests; the conflicting-requirements
agent scenario does not claim to exercise three retries.

## Release Preparation

The Git remote `origin` points to the public
[project repository](https://github.com/devartpy/plantuml-ai-architector).
Before pushing, review tracked files for secrets, local virtual environments,
and machine-specific configuration. The package declares version `0.1.0`, Python
`>=3.10`, and Colorama. For subsequent releases, bump the version, rerun the
checks, push the source, and tag the tested commit (for example `v0.1.0`).
Consumers can append that tag to the Git URL. No package-index upload is required.

## Repository MCP Integrations

This checkout may have a local `.codex/config.toml` for PlantUML,
[Spec Coding](https://github.com/kevinlin/spec-coding-mcp), and
[Spec Workflow](https://github.com/pimzino/spec-workflow-mcp). The file is ignored
by Git because its `cwd` values are machine-specific. These servers are development
tools, not Python dependencies and not part of the generated user-project MCP
example. Set `PLANTUML_SERVER_URL` to a local or internal renderer for private material.

In a trusted Codex project, use `codex mcp list` to inspect registration and
`/mcp` in the Codex CLI to inspect active connections. The first `npx` launch may
download the pinned packages. To run the optional Spec Workflow dashboard in a
separate terminal, use:

```powershell
npx -y @pimzino/spec-workflow-mcp@2.2.5 --dashboard
```

The dashboard is available at `http://localhost:5000`; stop it with Ctrl+C.
Spec Workflow stores documents in `.spec-workflow/`, while Spec Coding guides
documents under `docs/specs/`. Use one specification workflow per feature.

## See Also

- [Getting Started](getting-started.md) — install and run the CLI
- [Agent Setup](agent-setup.md) — generated PlantUML MCP example
- [Using the Diagram Skills](skills-usage.md) — invoke workflows and select a type
