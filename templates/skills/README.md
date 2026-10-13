# Agent Workflows

Place built-in agent workflows here. Write template content in English.
`ai-architect init` copies these workflows and the diagram specifications into
`.ai-architect/skills/` and `.ai-architect/specs/`. Both directories are
package-managed and replaced on every successful `init` run. Keep project-specific
rules and examples in `.ai-architect/references/`; keep diagrams in the directory
configured by `.ai-architect/config.json`. Do not customize the managed copies.

Copying a workflow does not automatically register it with every agent. If an
agent needs a separate skill-discovery location, register or install the workflow
there and keep its access to the current project's `.ai-architect/specs/`.

Available workflows:

- [plantuml-create](plantuml-create/SKILL.md) creates a new `.puml` diagram from requirements.
- [plantuml-modify](plantuml-modify/SKILL.md) edits an existing `.puml` diagram without changing its type.
- [plantuml-verify](plantuml-verify/SKILL.md) reviews an existing `.puml` file against its source requirements and the matching diagram specification.
- [self-correct](self-correct/SKILL.md) repairs a confirmed syntax error with at most three attempts and records a verified prevention rule.

Each workflow reads the matching `.ai-architect/references/<diagram_type>_rules.md`
when it exists. Project rules guide modeling ahead of baseline specifications;
requirements remain the source of facts. Verification never edits a diagram or a
rule file. The create and modify workflows call `self-correct` for confirmed
syntax failures; renderer outages do not create learned rules.
