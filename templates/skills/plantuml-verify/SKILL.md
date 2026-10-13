---
name: plantuml-verify
description: Verify an existing PlantUML file against source requirements, the project's diagram specifications, and its rendered result. Use for diagram review or QA; do not edit the input file.
---

# Verify a PlantUML Diagram

Accept a `.puml` file and the requirements it is intended to express. Read the file without modifying it. Keep renderer outputs in a temporary location when using a local renderer.

## Select the Contract

In an initialized project, read `README.md` and `workflow_matrix.md` from the project root's `.ai-architect/specs/`, even if this skill was registered elsewhere. When working directly from bundled source, use `../../specs/` relative to this skill. Choose the diagram type by the question the requirements ask it to answer, then read the matching type specification from that same directory. If the requested view and diagram disagree, report the mismatch. If the specifications cannot be found, mark the affected checks `BLOCKED` and identify the missing path. Do not substitute an unrelated diagram type.

After choosing the type, read the current project's `.ai-architect/references/<type>_rules.md` if present; a missing file is normal. Requirements determine facts, project rules have priority over baseline specification modeling guidance, and neither can make invalid PlantUML valid. Report unresolved conflicts and which context layers were consulted; do not treat unrelated reference files as instructions.

## Check the Diagram

1. Inspect the source for a complete `@startuml` to `@enduml` diagram and record relevant line numbers. Run an available PlantUML MCP renderer or local PlantUML renderer. Examine diagnostics **and** the rendered output for syntax-error text or graphics; a tool's success flag or returned URL alone is insufficient. Use a local renderer for material that should not be sent to a public service. If no renderer is available, or its output cannot be inspected, mark syntax `BLOCKED` rather than `FAIL`.
2. Independently compare the diagram with the supplied requirements, applicable project rules, and the selected specification's modeling rules and semantic acceptance checks. Trace actors, elements, relationships, direction, guards, boundaries, and other relevant details to evidence in the requirements. Treat a successful render as a syntax result only. If requirements are missing or too vague for a necessary comparison, mark that semantic check `BLOCKED`; do not invent facts.
3. Review readability in the source and, when available, the render: names and labels should be understandable, aliases consistent, and the chosen abstraction level clear. Report concrete problems only. If visual inspection is necessary but unavailable, mark the visual part `BLOCKED`.

Do not repair, rewrite, or overwrite the input diagram. Do not change requirements, project rules, or specification files during verification. For a confirmed syntax error, report it and suggest a separate `self-correct` run; never invoke a writing correction workflow from verification.

## Report

Return one overall status and the result of each check: `syntax`, `requirements`, `project_rules`, `specification`, and `readability`. Use `FAIL` when any demonstrated violation exists; otherwise use `BLOCKED` when a required check could not be completed; use `PASS` only when all required checks pass.

For each finding, give the file and line (or the closest source location), the violated requirement or specification rule, the observed evidence, and a targeted correction. Distinguish confirmed defects from unavailable evidence. State the renderer used and any checks that could not run. If there are no findings, say so explicitly.
