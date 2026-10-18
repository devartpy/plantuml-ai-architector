[← Agent Setup](agent-setup.md) · [Back to README](../README.md) · [Development →](development.md)

# Using the Diagram Skills

Run `ai-architect init` in the target project, then [make the skills available to your agent](agent-setup.md). Invoke them from that project so they can read its `.ai-architect/specs/`, `.ai-architect/config.json`, and optional `.ai-architect/references/<diagram_type>_rules.md`.

These are **agent skills**, not `ai-architect` CLI subcommands. Type the invocation in your agent's chat. The only CLI command currently provided by the Python package is `ai-architect init`.

## Choose a Workflow

| Task | Codex | Claude Code / Cursor | Required input and result |
| --- | --- | --- | --- |
| Create a diagram | `$plantuml-create` | `/plantuml-create` | Describe the system or requirements; optionally include `diagram_type`. Saves a new `.puml` file without overwriting one. |
| Change a diagram | `$plantuml-modify` | `/plantuml-modify` | Give an existing `.puml` path and the requested change. Keeps its diagram type and path. |
| Review a diagram | `$plantuml-verify` | `/plantuml-verify` | Give a `.puml` path and its source requirements. Reports `PASS`, `FAIL`, or `BLOCKED` without editing the file. |
| Repair confirmed syntax | `$self-correct` | `/self-correct` | Usually called by create or modify after a renderer diagnostic. For a direct request, supply the file or candidate, type, requirements, and **actual** diagnostic. |

For example, ask Codex: `$plantuml-modify Update docs/architecture/diagrams/order-state.puml: add a Cancelled state reachable from Submitted.` In Claude Code or Cursor, begin the same request with `/plantuml-modify`.

## Create a Specific Diagram Type

Without `diagram_type`, `plantuml-create` reads the workflow matrix and selects a type from your requirements. To select one yourself, include **`diagram_type=<value>` in the chat request**. This is an input to the skill, not a `--diagram-type` CLI flag. An explicit type skips the matrix; the agent still reads that type's specification. If a required fact is missing, it asks for clarification.

The following Codex prompts show every supported value. In Claude Code or Cursor, replace `$plantuml-create` with `/plantuml-create` and keep the rest of the request.

| Type | Example invocation |
| --- | --- |
| `use_case` | `$plantuml-create diagram_type=use_case. Requirements: A customer places an order; a payment provider authorizes payment.` |
| `c4_container` | `$plantuml-create diagram_type=c4_container. Requirements: Shoppers use a browser UI; the UI calls an order API; the API stores orders in PostgreSQL.` |
| `sequence` | `$plantuml-create diagram_type=sequence. Requirements: Customer submits checkout to the API; the API requests authorization from a payment provider; the provider returns approved or declined; the API returns that outcome.` |
| `activity` | `$plantuml-create diagram_type=activity. Requirements: Start when an order is submitted; validate it; if valid, charge payment and confirm; otherwise reject; then finish.` |
| `state` | `$plantuml-create diagram_type=state. Requirements: An order starts in Draft; submit moves it to Submitted; pay moves Submitted to Paid; cancel moves Draft or Submitted to Cancelled.` |
| `class` | `$plantuml-create diagram_type=class. Requirements: Order has id and total; OrderLine has quantity; an Order contains one or more OrderLines.` |
| `deployment` | `$plantuml-create diagram_type=deployment. Requirements: A browser connects over HTTPS to a web app on an app server; the app connects to PostgreSQL on a database server.` |

Replace the example requirements with your actual system facts. `plantuml-create` uses the `diagrams_dir` setting in `.ai-architect/config.json`, defaulting to `docs/architecture/diagrams/`, and chooses a descriptive `.puml` filename. If that file already exists, use `plantuml-modify` or request a different name; creation never overwrites it.

## Checks and Project Rules

Create and modify render through an available PlantUML MCP tool or local renderer, then review requirements and readability separately. If rendering cannot be inspected, they report the syntax check as `BLOCKED`; a successful render alone does not prove the diagram matches the requirements. Use `plantuml-verify` for an independent read-only review and include the original requirements so its semantic check can be completed.

For a **confirmed syntax error**, create or modify follows `self-correct`: it tries at most three distinct candidate repairs. After a verified repair is saved, the workflow records a deduplicated English prevention rule in `.ai-architect/references/<diagram_type>_rules.md`. Renderer outages and semantic-only defects do not create syntax rules. Project rules guide modeling ahead of baseline specifications, while your requirements remain the source of facts.

## See Also

- [Agent Setup](agent-setup.md) — install skills and connect the renderer
- [Configuration](configuration.md) — choose the diagram directory and renderer URL
- [Development](development.md) — run project checks
