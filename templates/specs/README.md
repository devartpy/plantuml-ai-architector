# Diagram Specifications

These English templates are the package's read-only defaults. Start with the [workflow matrix](workflow_matrix.md) to choose the view that answers the user's question, then apply the matching specification. A request may need several complementary diagrams; keep each diagram's scope explicit.

| Question to answer | Specification |
| --- | --- |
| Who uses which capability? | [Use case](use_case_spec.md) |
| Which logical applications and data stores interact? | [C4 container](c4_container_spec.md) |
| In what order do participants exchange messages? | [Sequence](sequence_spec.md) |
| Which actions, decisions, and parallel steps form a process? | [Activity](activity_spec.md) |
| Which states can one entity enter? | [State](state_spec.md) |
| What static types and relationships exist? | [Class](class_spec.md) |
| Where are artifacts and runtimes deployed? | [Deployment](deployment_spec.md) |

## Shared Generation Contract

1. Identify the question, system boundary, intended audience, and source facts. Ask for a missing fact when it changes the diagram type or a required relationship. Label nonessential assumptions; do not invent protocols, addresses, permissions, or implementation details.
2. Follow the selected specification's required inputs and modeling rules. Use stable, unique aliases and trace every element and relationship to an input fact. Keep separate abstraction levels in separate diagrams.
3. Emit one complete PlantUML source block (`@startuml` through `@enduml`) per requested diagram. When returning source in chat, use a `plantuml` fenced block; explanations or open questions belong outside that block.
4. Validate syntax with a renderer and then review semantics against the specification's acceptance checklist. A successful render cannot prove that a diagram is factually correct.

## Validation

From the repository root, run `python scripts/validate_specs.py` to check local links, catalog coverage, sections, and complete examples. Set `LOG_LEVEL=DEBUG` for per-file diagnostics. During authoring, pass every complete example to the PlantUML MCP `generate_plantuml_diagram` tool and inspect its SVG output for error text or an error graphic. This uses the configured public PlantUML server, so examples must contain synthetic data. A local renderer can be used when privacy or offline operation is required; C4 rendering needs a PlantUML distribution with the `<C4/C4_Container>` standard library entry.
