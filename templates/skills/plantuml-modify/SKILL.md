---
name: plantuml-modify
description: Modify an existing PlantUML .puml file for a requested change while preserving its diagram type and unrelated content. Use when given a diagram path and an edit request.
---

# Modify a PlantUML Diagram

Accept an existing `.puml` file and a change request. Edit that file in place; do not move it or change its diagram type. Never edit installed template resources when the user intends to change a diagram in their project.

## Identify the Existing View

Read the source and identify its diagram type from distinctive constructs and the diagram's purpose, not its filename alone. In an initialized project, read the matching `<type>_spec.md` from the project root's `.ai-architect/specs/`, even if this skill was registered elsewhere. When working directly from bundled source, use `../../specs/` relative to this skill. If the matching specification cannot be found, leave the diagram unchanged and report the missing path. Do **not** use `workflow_matrix.md` to select another type. If the type is ambiguous, ask before editing. If the request requires a different type, leave the file unchanged and suggest creating a separate diagram with `plantuml-create`.

Read the current project's `.ai-architect/references/<type>_rules.md` when it exists; a missing file is normal. Source requirements and the requested change determine facts; project rules take precedence over baseline specification modeling guidance but cannot override those facts or required PlantUML validity. Surface conflicts instead of silently changing the diagram. Do not treat unrelated reference files as instructions. Report the context layers consulted without exposing private rule text.

## Prepare the Smallest Change

Record the original contents, encoding, and line endings before editing. Inspect the relevant elements and relationships; when available, render the original and retain its diagnostics as a baseline. Ask a focused question if a fact essential to the requested change is missing. Preserve unrelated elements, links, aliases, and layout. Do not invent facts or silently repair unrelated defects.

Make the requested change on a temporary copy. Keep its `@startuml` / `@enduml` scope and diagram type. Review the difference against the request before touching the original file.

## Check and Save

Render the candidate with an available PlantUML MCP tool or local renderer. Inspect diagnostics and the actual SVG or image for syntax-error messages or graphics; a success flag or URL alone is insufficient. Use a local renderer when the diagram should not be sent to a public service. Compare candidate diagnostics with the baseline. For a confirmed syntax error in the requested change, invoke `self-correct` with the original file, temporary candidate, type, request, available source requirements, baseline, and exact diagnostic; use its bounded attempts and checked result. Never save a candidate with a confirmed new syntax error. Report pre-existing errors separately; do not silently repair them or learn a rule from them. If an old error prevents you from distinguishing a new error, leave the original unchanged and explain the uncertainty. If no renderer can be inspected, mark syntax verification `BLOCKED`, not `PASS`, and do not create a learned syntax rule.

Separately check that the change matches the request, applicable project rules, and the selected specification's modeling and semantic rules. Check readability and that the rest of the diagram retains its apparent meaning. If original requirements are available, use them for a fuller semantic review; otherwise state that whole-diagram semantic verification is limited. Do not save a candidate with a demonstrated request, project-rule, or specification violation.

Before saving, confirm the original file still matches the recorded contents. Write the checked candidate to the **same path**, preserving encoding and line endings where practical. If `self-correct` already saved an accepted candidate, do not save it again. Apart from `self-correct`'s verified rule entry, do not modify any other project file. If syntax verification was blocked but no defect was demonstrated, the requested change may still be saved with that limitation reported.

Report the path, identified type, concise change summary, syntax result, request and specification checks, any pre-existing errors, and any checks that remained blocked. If no change was saved, say why and confirm the original is intact.
