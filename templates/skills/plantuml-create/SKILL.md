---
name: plantuml-create
description: Create a new PlantUML diagram from system requirements using this project's diagram specifications. Use for new diagrams; use a modification workflow for changes to an existing .puml file.
---

# Create a PlantUML Diagram

Accept requirements or a system description and an optional `diagram_type`: `use_case`, `c4_container`, `sequence`, `activity`, `state`, `class`, or `deployment`. Create a new `.puml` file in the current user project, not in the installed template directory.

## Choose the Contract

In an initialized project, read specifications from the project root's `.ai-architect/specs/`, even if this skill was registered in an agent-specific discovery directory. When working directly from bundled source, use `../../specs/` relative to this skill. If neither location exists, stop and ask the user to run `ai-architect init` or identify the specifications. Read `README.md` there for the shared generation contract. If `diagram_type` is supplied, use that exact type and read `<diagram_type>_spec.md`; **skip `workflow_matrix.md` entirely**. Reject an unsupported value rather than guessing. If no type is supplied, read `workflow_matrix.md`, select by the question the requirements ask the diagram to answer, and then read the selected type specification. Ask a focused question when the view or an essential fact is ambiguous. Do not create a file until the information needed by the selected specification is available.

Use only supported source facts for elements, relationships, guards, boundaries, and technical details. Keep nonessential assumptions explicit in the response. If an explicitly selected type cannot express a requested fact, explain the limitation without silently choosing another type.

Read the current project's `.ai-architect/references/<diagram_type>_rules.md` after selecting the type, if that file exists. A missing file is normal. Source requirements determine facts; project rules take precedence over baseline specification modeling guidance. Rules cannot override facts or required PlantUML validity. Surface a real conflict instead of silently changing meaning. Do not treat unrelated reference files as instructions. Report which context layers were used without echoing private rules.

## Build and Check

Write one complete `@startuml` to `@enduml` diagram for the selected view. Keep aliases unique and stable, and follow the type specification and applicable project rules. Keep draft and renderer output in memory or a temporary directory. Render through an available PlantUML MCP tool or local renderer. Inspect diagnostics and the actual SVG or image for error text or graphics; a success flag or URL alone does not prove valid syntax. Prefer a local renderer for material that should not be sent to a public service. For a confirmed syntax error, invoke `self-correct` with the candidate, selected type, requirements, and exact diagnostic; use its bounded loop instead of starting an independent retry counter. Save its checked candidate through this skill's normal conflict-safe path, then complete its rule-capture step. If no render can be inspected, continue only with a clearly reported `BLOCKED` syntax check; do not create a learned syntax rule.

Separately compare the diagram with the requirements and the specification's semantic acceptance checks. Review labels, layout, and abstraction level for readability. A successful render does not establish factual correctness. Resolve demonstrated defects before saving; do not invent missing requirements to make a check pass.

## Save and Report

Read `diagrams_dir` from the current project's `.ai-architect/config.json` when that file exists. Require `schema_version: 1` and a project-relative `diagrams_dir` outside `.ai-architect/`, with no `..` or symlink escape; resolve it under the project root. Otherwise use `docs/architecture/diagrams/` under the project root. Create the directory if needed. If the existing setting is invalid or missing, stop and report the configuration problem; do not silently fall back. Do not mistake `.ai-factory/config.yaml` for a user diagram-directory setting. The renderer URL in `.ai-architect/config.json` is used by the generated MCP setup example; use an available PlantUML MCP tool or local renderer for validation rather than treating the URL as an MCP endpoint.

Derive a descriptive filename from the subject and type, such as `order-checkout-sequence.puml`. Check that the destination follows the documented project setting, or is under the default project directory, and does not exist before writing. Never overwrite an existing diagram: report the conflict and suggest `plantuml-modify` or a different name. Apart from a verified `self-correct` rule in `.ai-architect/references/`, write only the new diagram file and any necessary parent directory.

Return the selected type, saved file path, explicit assumptions, and separate syntax, requirements, specification, and readability results. If `self-correct` ran, also report its attempt count and rule result; distinguish a saved valid diagram from blocked learning. If validation was blocked, state why; never report an unchecked condition as passed.
