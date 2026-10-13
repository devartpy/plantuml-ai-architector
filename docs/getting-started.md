[Back to README](../README.md) · [Configuration →](configuration.md)

# Getting Started

## Prerequisites and Installation

Use Python 3.10 or later and install Git. Pip installs this project directly
from [GitHub](https://github.com/devartpy/plantuml-ai-architector) without a
package index. Create a virtual environment in the **target project**. In PowerShell:

```powershell
cd C:\path\to\your-project
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install "git+https://github.com/devartpy/plantuml-ai-architector.git"
.\.venv\Scripts\ai-architect.exe --help
```

The URL without a ref follows the repository's default branch. For a stable
installation, append a published tag such as `@v0.1.0` after `.git`. For work
on the package itself, run `python -m pip install -e .` from a local checkout.
On POSIX, use `python3 -m venv .venv`,
`./.venv/bin/python -m pip install "git+https://github.com/devartpy/plantuml-ai-architector.git"`,
and `./.venv/bin/ai-architect --help`. You can also invoke
`python -m ai_architect.cli` with the installed interpreter if its console script
is unavailable.

For package development, run the checks in [Development](development.md).
End users install from GitHub; no distribution archive is committed or uploaded.

## Initialize Your Project

Stay in the **target project root** when invoking `init`; it acts on the current
working directory, not the package checkout:

```powershell
.\.venv\Scripts\ai-architect.exe init
```

To customize the first run, pass project-relative output and renderer settings:

```powershell
.\.venv\Scripts\ai-architect.exe init --diagrams-dir docs/architecture/views --plantuml-server-url http://127.0.0.1:18080
```

The default run creates:

```text
.ai-architect/
  config.json                # Persistent project settings
  mcp-config-example.json    # Generated MCP setup example
  specs/                    # Package-managed diagram specifications
  skills/                   # Package-managed agent workflows
  references/               # Persistent project rules, including learned syntax guards
docs/architecture/diagrams/  # Default diagram output directory
```

Successful steps print `CREATED` or `UPDATED`; reused paths print `SKIP`.
Errors print `ERROR` and exit with status 1. `init` does not contact the renderer.

## Repeat Runs and Next Step

Run `ai-architect init` again after upgrading the Python package to refresh the
managed `specs/` and `skills/` directories. It reuses `config.json` without
rewriting it, regenerates the MCP example, and preserves `references/` and the
configured diagram directory. Edits inside managed directories will be lost.
To change a setting, edit `config.json` and rerun `init`; passing a conflicting
option on a repeat run is an error.

Copying workflows does not register them with every agent. Follow
[Agent Setup](agent-setup.md) to connect the optional MCP server and expose the
skills to your agent.

## See Also

- [Configuration](configuration.md) — settings and safe path rules
- [Agent Setup](agent-setup.md) — MCP and skill activation
