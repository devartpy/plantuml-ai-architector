# Diagram Selection and Workflow Matrix

Use this file to select the diagram view before reading a type specification. Select by the **question to answer**, not by a keyword in isolation. A diagram is one view of the supplied facts; several views can coexist.

## Selection Matrix

| User's primary question | Choose | Key evidence to request |
| --- | --- | --- |
| Who can achieve which goal inside the system? | [Use case](use_case_spec.md) | Actors, goals, system boundary, known include or extension conditions |
| Which applications, services, stores, and external systems collaborate? | [C4 container](c4_container_spec.md) | Software-system boundary, logical containers, responsibilities, known interactions |
| What message does each participant send, and when? | [Sequence](sequence_spec.md) | Participants, ordered messages, alternatives, replies, timeouts |
| Which actions and decisions make up a process? | [Activity](activity_spec.md) | Steps, guards, loops, parallel work, owners |
| Which states can one entity enter, and what triggers movement? | [State](state_spec.md) | Entity, states, events, guards, terminal or continuing behavior |
| What types, attributes, operations, and static relationships exist? | [Class](class_spec.md) | Types, ownership, inheritance, multiplicities, attribute types |
| On which runtime or infrastructure node does an artifact run? | [Deployment](deployment_spec.md) | Environments, nodes, deployed artifacts, known network links |

## Resolve Close Calls

- **C4 container or deployment:** Logical runtime responsibilities and interactions call for C4. Hosts, pods, execution environments, or artifact placement call for deployment. Request both when logical and physical mapping are needed.
- **Sequence or activity:** Ordered messages between named participants call for sequence. Decision paths, task ownership, loops, or concurrent activities call for activity. A workflow may need both views.
- **Activity or state:** Actions performed by a process call for activity. Valid statuses and transitions of one entity call for state.
- **Class or database model:** Class diagrams represent static types and relationships; they can show a conceptual data model. Physical tables, keys, and database constraints require an explicit data-model scope before choosing this notation or an extension to the catalog.
- **Use case or sequence:** Actor goals and software scope call for use case. A concrete interaction scenario calls for sequence.

If the question, boundary, or decisive facts are missing, ask a short clarification before choosing. Do not default an ambiguous request to C4 or sequence. When multiple views are requested, state the question answered by each, reuse consistent names, and avoid placing physical nodes into a logical C4 diagram or message chronology into a use-case diagram.

## Optional Architecture Walkthrough

For a broad system-design request, a useful order is actor goals → logical containers → key interactions and activities → type and lifecycle models → deployment. Skip views that do not answer a stated question. Keep unknown technical details open until the source material supports them.

## Delivery Checks

- Confirm that the chosen file's selection criteria match the user's question.
- Keep diagrams as text (`.puml`) for review and version control.
- Verify renderability, then inspect names, relationships, guards, and boundaries against the supplied facts. Rendering alone does not validate meaning.
- The C4 example uses PlantUML's bundled `<C4/C4_Container>` library. Offline rendering requires that library in the local PlantUML distribution; the project MCP currently points to a public renderer.
