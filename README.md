# PlantUML AI Architect

[![Python Version](https://img.shields.io/badge/Python3.10+-blue)](https://python.org)
[![Architecture as Code](https://img.shields.io/badge/Architecture_as_Code-orange)](#)
[![License](https://img.shields.io/badge/License:_MIT-green)](LICENSE)

An installable Python CLI designed to set up structured, **Spec-Driven PlantUML workflows** directly within your software repositories. It acts as an orchestrator that enables advanced AI agents (such as *Cursor, Codex, or Claude Code*) to generate, validate, and maintain architectural blueprints deterministically.

The package bundles **core diagram specifications** and four agent workflows:
`plantuml-create`, `plantuml-modify`, `plantuml-verify`, and `self-correct`.

---

## 🚀 Quick Start

### 1. Installation
Install the package directly from the public GitHub repository into your target project's virtual environment. No package-index (PyPI) registration is required.

**On Windows:**
```bash
cd C:\path\to\your-project
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install "git+https://github.com/devartpy/plantuml-ai-architector.git"
```

**On macOS / Linux:**
```bash
cd /path/to/your-project
python3 -m venv .venv
source .venv/bin/activate
pip install "git+https://github.com/devartpy/plantuml-ai-architector.git"
```

> 📌 **Tip:** To pin a specific release version, append its Git tag to the URL string (e.g., `...plantuml-ai-architector.git@v0.1.0`).

### 2. Initialization
Run the `init` command from the root of your project directory to deploy the environment:

```bash
# Windows
.\.venv\Scripts\ai-architect.exe init

# macOS / Linux
ai-architect init
```

### 🎛️ Advanced First-Run Flags
You can optionally customize your default diagrams directory and bind a local/internal air-gapped PlantUML rendering server during initialization:

```bash
ai-architect init --diagrams-dir docs/architecture/views --plantuml-server-url http://127.0.0.1:18080
```

---

## 📂 Deployed File Structure

Running `ai-architect init` creates the following directory layout in your workspace:

```text
your-project/
├── .ai-architect/
│   ├── config.json               # Persisted path & renderer server settings
│   ├── mcp-config-example.json   # Model Context Protocol example for Agents
│   ├── specs/                    # Managed, read-only baseline prompt templates (Refreshed on reruns)
│   │   ├── c4_container_spec.md
│   │   ├── sequence_spec.md
│   │   └── ...
│   ├── skills/                   # Managed agent workflow action profiles (Refreshed on reruns)
│   │   ├── plantuml-create/SKILL.md
│   │   └── self-correct/SKILL.md
│   └── references/               # Empty initially; learned project rules are preserved on reruns
└── docs/architecture/diagrams/   # Default directory where AI saves .puml files
```

> 🔄 **Idempotency Guard:** Running `ai-architect init` again safely refreshes the base `specs/` and `skills/` folders to deliver package updates, but **strictly preserves** your custom configurations, diagrams, and learned reference rule files.

---

## 🧠 The Evolving Self-Correction Loop

After you connect the PlantUML MCP server and make the skills available to your agent, the `self-correct` workflow can capture lessons from confirmed syntax failures:

1. **Failure Interception:** If the agent generates a diagram that breaks PlantUML syntax, it can follow the `self-correct` skill workflow.
2. **Autonomous Repair:** The agent analyzes the error logs via the local MCP server context, applies structural patches, and attempts to re-compile (up to 3 times).
3. **Knowledge Capture:** Once the syntax repair is confirmed, the agent writes a reusable English guard rule inside `.ai-architect/references/<diagram_type>_rules.md`.

When the agent follows the bundled create or modify skills, it reads matching rules from `references/` and prioritizes them over baseline modeling guidance. See the [agent setup guide](docs/agent-setup.md) for the required client configuration.

---

## 📚 Documentation Reference

### Structural Manuals

| Guide | What it covers |
| :--- | :--- |
| **Getting Started** | Basic installation pipelines, initialization protocols, and upgrade reruns. |
| **Configuration** | Dynamic diagram target paths, custom local renderer URLs, and variable limits. |
| **Agent Setup** | Binding the PlantUML Model Context Protocol (MCP) server and agent skill discovery. |
| **Development** | Execution tests, local installation checks, and Git release tags. |

### Diagram Resources
* **Specification Catalog:** Features the 7 individual schema manuals along with the automated decision selection matrix.
* **Skill Workflows:** Instructions for `plantuml-create`, `plantuml-modify`, `plantuml-verify`, and `self-correct`.

---
