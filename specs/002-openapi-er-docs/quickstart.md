# Quickstart: OpenAPI ER Diagram Documentation

## What This Feature Produces

A single markdown file (`docs/data-model.md`) containing:
1. A Mermaid ER diagram showing all 14 domain entities from `openapi.json`
2. A textual overview of the WHOOP API data model organized by domain groups

## How to View

1. **GitHub**: Push the branch and view `docs/data-model.md` in the GitHub web UI. GitHub renders Mermaid diagrams natively.
2. **VS Code**: Install the "Markdown Preview Mermaid Support" extension, then open the file and press `Cmd+Shift+V` to preview.
3. **CLI**: Use `mmdc` (Mermaid CLI) to render to PNG/SVG: `npx @mermaid-js/mermaid-cli -i docs/data-model.md -o output.png`

## How to Update

When `openapi.json` changes:
1. Compare the `components.schemas` section for added/removed/modified entities
2. Update the corresponding entity block and relationships in the Mermaid diagram
3. Update the textual descriptions if entity purposes changed
4. Verify rendering in GitHub markdown preview

## File Location

```
docs/
└── data-model.md    # The documentation page with ER diagram
```
