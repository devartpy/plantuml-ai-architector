[← Getting Started](getting-started.md) · [Back to README](../README.md) · [Agent Setup →](agent-setup.md)

# Configuration

`ai-architect init` writes `.ai-architect/config.json` in the target project:

```json
{
  "schema_version": 1,
  "diagrams_dir": "docs/architecture/diagrams",
  "plantuml_server_url": "https://www.plantuml.com/plantuml"
}
```

| Field | Meaning |
| --- | --- |
| `schema_version` | Must be integer `1` for this package version. |
| `diagrams_dir` | Project-relative directory for new `.puml` files. |
| `plantuml_server_url` | HTTP(S) base URL of a PlantUML **renderer**. |

The diagram path cannot be absolute, escape through `..`, or point inside
`.ai-architect/`. `init` rejects symlink/reparse-point escapes and file/directory
collisions. It creates a missing diagram directory recursively without changing
existing diagrams.

The renderer URL may be a local container (`http://127.0.0.1:18080`), an internal
company host, or the default public service. It must have an HTTP(S) host, no
credentials, query, or fragment; a trailing slash is normalized. `init` does not
test connectivity. Diagram text sent to a public renderer leaves your machine,
so choose an appropriate server for private diagrams.

## Changing Settings

`--diagrams-dir` and `--plantuml-server-url` set values on the first run. On a
repeat run, `init` validates and reuses the existing JSON. Edit the JSON to change
a value, then rerun `ai-architect init`. A conflicting CLI option causes an error
instead of silently replacing the stored setting. `init` regenerates
`.ai-architect/mcp-config-example.json` from the effective renderer URL; update
your agent's MCP configuration separately if that URL changes.

The generated MCP example passes `plantuml_server_url` as
`PLANTUML_SERVER_URL` to a separate MCP server process. The renderer URL is not
itself an MCP endpoint. The `plantuml-create` workflow reads `diagrams_dir` to
choose where to save diagrams. The `modify` and `verify` workflows use the
existing `.puml` path supplied to them.

For CLI diagnostics, set `LOG_LEVEL=DEBUG` in the environment. For example, in
PowerShell run `$env:LOG_LEVEL = "DEBUG"` before `ai-architect init`.

## See Also

- [Getting Started](getting-started.md) — first run and repeat behavior
- [Agent Setup](agent-setup.md) — using the generated MCP example
