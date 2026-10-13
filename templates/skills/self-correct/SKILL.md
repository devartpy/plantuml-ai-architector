---
name: self-correct
description: Repair a confirmed PlantUML syntax error with a bounded validation loop, then capture a verified prevention rule. Use during diagram creation or modification, or for an explicit syntax-repair request; do not use for semantic-only defects or renderer outages.
---

# Correct a PlantUML Syntax Error

Accept a new `.puml` candidate or an existing file plus its proposed temporary candidate, the diagram type, available source requirements or change request, and the exact candidate renderer diagnostic. For an existing file, also accept the original-render baseline when available. Work in the current user project. Use this workflow only when a PlantUML MCP tool or local renderer has identified a concrete syntax error, or when an explicit repair request can be reproduced as one. Do not infer a syntax error from an unavailable tool, a URL alone, or a rendering failure without a PlantUML diagnostic.

## Classify and Establish a Baseline

In an initialized project, read `.ai-architect/specs/<diagram_type>_spec.md` from the project root even if this skill was registered elsewhere. When working directly from bundled source, use `../../specs/` relative to this skill; if neither exists, stop and identify the missing specification. Read `.ai-architect/references/<diagram_type>_rules.md` when present. Accept only `use_case`, `c4_container`, `sequence`, `activity`, `state`, `class`, or `deployment`; resolve an uncertain type before editing. Project rules take precedence over baseline modeling guidance, but cannot override source facts or required PlantUML validity. Report an unresolved conflict instead of silently choosing one.

Record the exact saved source, proposed candidate, encoding, line endings, relevant requirements, and renderer result. For an existing file, retain its path and preserve unrelated elements, relationships, and aliases. Compare the candidate diagnostic with the original-render baseline; do not repair or learn from an unrelated pre-existing error. If that distinction cannot be made, stop without changing the saved file. Classify connection, permission, timeout, unavailable PlantUML/Graphviz, or uninspectable output as `BLOCKED`, not a syntax failure. Inspect diagnostics and the actual image or SVG when possible; the MCP tool may return a success URL without proving a clean render.

## Repair and Verify

1. Locate the failing line or construct using the renderer diagnostic. Make the smallest justified edit to a temporary candidate; never invent requirements or change the diagram type. Do not rewrite the whole diagram when a local edit suffices.
2. Render the candidate with the available PlantUML MCP tool or local renderer. Inspect its diagnostics and output. Repeat only for a distinct, evidence-based correction, with **at most three candidate attempts total**. Count an attempt when a changed candidate is submitted; do not recurse into this skill or reset the counter.
3. After a clean render, separately compare the candidate with the original requirements or change request, the selected specification, project rules, and readability. A clean render proves no semantic claim. If requirements are unavailable, describe the limit of whole-diagram review and preserve the original diagram's apparent meaning.

Do not save a candidate with a newly confirmed syntax error or a demonstrated semantic violation. If all three attempts fail, leave the original file intact and return `FAIL` with the remaining diagnostic. If validation becomes unavailable, return `BLOCKED`; preserve the original and do not call the outage a syntax defect. For an existing file, verify that its contents have not changed since the recorded saved source before writing an accepted candidate to the same path; preserve encoding and line endings where practical. For a new diagram, hand the checked candidate back to the creating workflow for its normal conflict-safe save. Never edit package templates or managed `.ai-architect/specs/` and `.ai-architect/skills/`.

## Capture a Verified Rule

Only after the syntax repair has passed rendering and semantic review **and the diagram has been saved**, derive one reusable English guard rule from the confirmed mistake and successful fix. For a new diagram, wait until the creating workflow confirms its conflict-safe save. Never create a rule for an unverified guess, a semantic-only issue, a renderer outage, or an unsuccessful attempt.

Use only the current project root's `.ai-architect/references/<diagram_type>_rules.md`; do not follow a symlink or write outside that directory. `ai-architect init` creates `references/` and preserves it on repeat runs. If it is absent or unwritable, report learning as `BLOCKED` without undoing a saved valid diagram. Read an existing file first and compare the proposed issue and guard with its current rules. If an equivalent guard already exists, do not append a duplicate. Otherwise create the file if needed and append one focused entry:

```markdown
### <short guard title>
- **Issue:** <generalized syntax mistake and observed PlantUML diagnostic>
- **Fix Rule:** <specific check or syntax constraint for future diagrams>
- **Evidence:** <minimal sanitized before/after construct or line reference>
```

Exclude private requirements, credentials, network addresses, and full diagram source from the rule. Do not alter other entries or any managed specification or skill. Report whether the rule was added, already present, or blocked, with its path; do not claim a write succeeded unless the file can be reread with the new entry.

## Report

Return `PASS` only for a saved candidate with a clean inspected render, no demonstrated requirement, specification, project-rule, or readability defect, and a persisted or already-equivalent rule. Return `FAIL` for a confirmed unresolved syntax or semantic defect; return `BLOCKED` when an essential check or required rule write could not complete, explicitly distinguishing a valid saved diagram from incomplete learning. State the diagram path or handoff, attempt count, original and final diagnostics, exact changed location, renderer used, separate syntax and semantic results, rule result, and any validation limits. Log a concise category, line if available, action, and outcome per attempt; omit full private source and requirements.
