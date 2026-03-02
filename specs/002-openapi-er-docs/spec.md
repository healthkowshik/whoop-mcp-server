# Feature Specification: OpenAPI ER Diagram Documentation

**Feature Branch**: `002-openapi-er-docs`
**Created**: 2026-03-02
**Status**: Draft
**Input**: User description: "Create a documentation page with a ER diagram of OpenAPI.json using mermaid"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Entity Relationships (Priority: P1)

As a developer working with the WHOOP API, I want to view a visual ER diagram that shows all data entities defined in the OpenAPI specification and their relationships, so I can quickly understand the data model without reading raw JSON.

**Why this priority**: The core value of this feature is the visual diagram itself. Without it, the documentation page has no purpose.

**Independent Test**: Can be fully tested by opening the documentation page and verifying the Mermaid ER diagram renders correctly, showing all entities from `openapi.json` with their attributes and relationships.

**Acceptance Scenarios**:

1. **Given** the documentation page exists, **When** a developer opens it, **Then** they see a rendered Mermaid ER diagram displaying all schema entities from `openapi.json`
2. **Given** the ER diagram is rendered, **When** a developer examines the diagram, **Then** all entity relationships (e.g., Sleep belongs to Cycle, Recovery links to both Cycle and Sleep) are accurately represented with correct cardinality
3. **Given** the ER diagram is rendered, **When** a developer examines an entity, **Then** each entity shows all of its attributes (as defined in the OpenAPI schema) with data types

---

### User Story 2 - Browse Entity Details (Priority: P2)

As a developer, I want the documentation page to include contextual descriptions alongside the ER diagram, so I can understand what each entity represents in the WHOOP domain without switching to other documentation.

**Why this priority**: Supporting context enhances the diagram's usefulness but the diagram alone delivers the core value.

**Independent Test**: Can be tested by verifying that entity descriptions from the OpenAPI spec are present on the documentation page alongside or near the diagram.

**Acceptance Scenarios**:

1. **Given** the documentation page is open, **When** a developer reads the page, **Then** they find a summary of the WHOOP API data model covering the major entity groups (User, Cycle, Sleep, Recovery, Workout)
2. **Given** the documentation page is open, **When** a developer looks for entity details, **Then** each entity group has a brief description explaining its role in the WHOOP health tracking domain

---

### Edge Cases

- What happens when the OpenAPI spec is updated with new entities? The documentation page must be manually regenerated or updated to reflect changes.
- What happens if a Mermaid rendering environment does not support ER diagrams? The page should use standard Mermaid ER syntax compatible with GitHub-flavored markdown rendering and common Mermaid viewers.
- What happens if an entity has no relationships to other entities (e.g., `ActivityIdMappingResponse`)? Standalone entities should still appear in the diagram without relationship lines.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The documentation page MUST be a markdown file that includes a Mermaid ER diagram code block
- **FR-002**: The ER diagram MUST represent all domain schema entities defined in `openapi.json`, including: UserBasicProfile, UserBodyMeasurement, Cycle, CycleScore, Sleep, SleepScore, SleepStageSummary, SleepNeeded, Recovery, RecoveryScore, WorkoutV2, WorkoutScore, ZoneDurations, and ActivityIdMappingResponse
- **FR-003**: The ER diagram MUST show relationships between entities with correct cardinality notation (e.g., one-to-many, one-to-one)
- **FR-004**: Each entity in the diagram MUST display ALL attributes defined in the OpenAPI schema with their data types (not just required or key fields)
- **FR-005**: The ER diagram MUST use standard Mermaid `erDiagram` syntax that renders in GitHub markdown and common Mermaid viewers
- **FR-006**: The documentation page MUST include a brief textual overview of the WHOOP API data model organized by domain groups (User, Cycle, Sleep, Recovery, Workout)
- **FR-007**: The documentation page MUST be placed in the `docs/` directory of the project
- **FR-008**: Paginated collection wrappers (PaginatedCycleResponse, PaginatedSleepResponse, RecoveryCollection, WorkoutCollection) MUST be excluded from the ER diagram to keep it focused on domain entities

### Key Entities

- **User**: Central entity representing a WHOOP user; has a profile (name, email) and body measurements (height, weight, max heart rate)
- **Cycle**: A physiological cycle representing a day-level period; belongs to a User and contains a CycleScore with strain, kilojoule, and heart rate metrics
- **Sleep**: A sleep activity within a Cycle; belongs to both a User and a Cycle; contains a SleepScore with stage summaries and sleep need breakdowns
- **Recovery**: A recovery measurement linked to a Cycle and a Sleep; belongs to a User; contains a RecoveryScore with HRV, resting heart rate, SpO2, and skin temperature
- **Workout**: A workout activity; belongs to a User; contains a WorkoutScore with strain, heart rate zones, distance, and altitude metrics

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The Mermaid ER diagram renders correctly in GitHub markdown preview without errors
- **SC-002**: All 14 domain schema entities from `openapi.json` are represented in the diagram (excluding pagination wrappers)
- **SC-003**: All foreign-key relationships between entities are accurately depicted (User-to-Cycle, Cycle-to-Sleep, Cycle-to-Recovery, Sleep-to-Recovery, and all score/sub-entity compositions)
- **SC-004**: A developer unfamiliar with the WHOOP API can identify the core data model and entity relationships within 2 minutes of viewing the page

## Clarifications

### Session 2026-03-02

- Q: What level of attribute detail should each entity display — all attributes, required only, IDs/FKs only, or required + relationships? → A: All attributes — show every field defined on every entity in the OpenAPI schema.
