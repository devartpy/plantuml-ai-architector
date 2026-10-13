[← Configuration](configuration.md) · [Back to README](../README.md) · [Development →](development.md)

# Agent Setup

`init` creates `.ai-architect/mcp-config-example.json`; agents do not load this
file automatically. It defines an `mcpServers.plantuml` entry that launches the
pinned `plantuml-mcp-server@0.2.4` through `npx -y`. Install Node.js 18+ and npm
where the agent runs. The first launch may download the npm package. The
`PLANTUML_SERVER_URL` value is the renderer from `config.json`, not an MCP URL.
The [PlantUML MCP server](https://github.com/infobip/plantuml-mcp-server) provides
rendering and encode/decode tools; the renderer alone does not expose MCP tools.
When asked to save rendered files, that server limits output to its working
directory by default.

## Connect PlantUML MCP

Open the generated example and merge its `plantuml` entry with existing servers:

| Client | Project configuration |
| --- | --- |
| [Cursor](https://docs.cursor.com/context/model-context-protocol) | `.cursor/mcp.json`, under `mcpServers` |
| [Claude Code](https://code.claude.com/docs/en/mcp) | `.mcp.json` at the project root, under `mcpServers` |
| [Codex](https://developers.openai.com/codex/mcp) | `.codex/config.toml`, translated to TOML |

For Codex on Windows, use the same URL and package version as the generated
JSON, with a Windows command wrapper:

```toml
[mcp_servers.plantuml]
command = "cmd.exe"
args = ["/d", "/c", "npx", "-y", "plantuml-mcp-server@0.2.4"]

[mcp_servers.plantuml.env]
PLANTUML_SERVER_URL = "https://www.plantuml.com/plantuml"
```

Replace the URL with `plantuml_server_url` from your project's `config.json`.
On POSIX, use `command = "npx"` and
`args = ["-y", "plantuml-mcp-server@0.2.4"]`. On Windows, a JSON-based client
may need `npx.cmd` instead of `npx`. Preserve other configured MCP servers.
Restart or reload the client, approve/trust project configuration when prompted,
then check that PlantUML tools are available. In Codex, run `codex mcp list`
or use `/mcp` in its CLI; in Claude Code, run `claude mcp get plantuml`.

## Make the Skills Available

`init` copies `plantuml-create`, `plantuml-modify`, `plantuml-verify`, and
`self-correct` into
`.ai-architect/skills/`. If your agent does not discover that directory, point it
at the `SKILL.md` files or install the skill folders in its discovery location.
The skills read the current project's `.ai-architect/specs/` even when registered
elsewhere. Copying skill files does not itself connect PlantUML MCP.
The skills also read the matching `.ai-architect/references/<diagram_type>_rules.md`
when present. Requirements supply the facts; project rules guide modeling ahead
of the baseline type specification. `init` preserves these files on repeat runs.
It creates the directory but cannot override operating-system access controls;
the agent must have write access to record a learned rule.

An available local PlantUML renderer can also validate diagrams. The skills
must report when syntax validation cannot be completed, and they check
requirements and readability separately from rendering.

When create or modify encounters a **confirmed syntax error**, `self-correct`
tries at most three distinct fixes and records a deduplicated English prevention
rule only after a valid diagram is saved. A renderer outage, Graphviz failure,
or successful render with incorrect meaning does not create a syntax rule.
`plantuml-verify` remains read-only and may recommend a separate correction.

## See Also

- [Getting Started](getting-started.md) — create the workspace first
- [Configuration](configuration.md) — choose a local or internal renderer
- [Development](development.md) — this repository's additional MCP tools
