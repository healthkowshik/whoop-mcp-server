# Research: OpenAPI ER Diagram Documentation

## R1: Mermaid ER Diagram Syntax

**Decision**: Use Mermaid `erDiagram` syntax with entity blocks and relationship lines.

**Rationale**: Mermaid erDiagram is the standard diagram type for entity-relationship modeling. It supports:
- Entity definitions with typed attributes
- Relationship lines with cardinality notation (`||`, `o{`, `}o`, `|{`, etc.)
- Labels on relationship lines
- Renders natively in GitHub markdown (via ```mermaid code fences)

**Alternatives considered**:
- Mermaid classDiagram: Supports attributes but relationship semantics are OOP-oriented, not ER-oriented
- PlantUML: Requires external rendering; not natively supported in GitHub markdown
- dbdiagram.io: Requires external service; not embeddable in markdown

**Syntax reference**:
```
erDiagram
    ENTITY {
        type attribute_name
    }
    ENTITY1 ||--o{ ENTITY2 : "relationship_label"
```

Cardinality notation:
- `||` exactly one
- `o|` zero or one
- `}o` zero or more
- `}|` one or more

## R2: GitHub Mermaid Rendering Support

**Decision**: Use standard ```mermaid code fences in markdown.

**Rationale**: GitHub has supported Mermaid diagram rendering in markdown files since February 2022, including erDiagram types. No external tooling required.

**Constraints**:
- Entity names must not contain spaces or special characters (use PascalCase)
- Attribute types in Mermaid erDiagram are free-text strings (no validation)
- Very large diagrams may render slowly but will still display
- Mermaid attribute names cannot contain underscores in some renderers; will use camelCase for attribute names in the diagram

## R3: Attribute Type Mapping

**Decision**: Map OpenAPI types to concise Mermaid-friendly type labels.

| OpenAPI Type + Format | Mermaid Label |
|----------------------|---------------|
| integer + int32      | int           |
| integer + int64      | long          |
| number + float       | float         |
| string               | string        |
| string + date-time   | datetime      |
| string + uuid        | uuid          |
| boolean              | boolean       |
| enum                 | enum          |
| $ref (object)        | (relationship)|

**Rationale**: Keeps the diagram concise while preserving type information. References to other schemas become relationship lines rather than attributes.
