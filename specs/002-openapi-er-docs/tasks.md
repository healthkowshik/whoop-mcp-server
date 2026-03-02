# Tasks: OpenAPI ER Diagram Documentation

**Input**: Design documents from `/specs/002-openapi-er-docs/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md

**Tests**: Not requested — no test tasks included.

**Organization**: Tasks grouped by user story for independent implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: Create the documentation directory and initialize the output file

- [x] T001 Create `docs/` directory and initialize `docs/data-model.md` with page title ("WHOOP API Data Model"), a brief introduction paragraph stating this page documents the entity-relationship model derived from `openapi.json`, and a table of contents linking to the ER Diagram section and Domain Overview section

---

## Phase 2: User Story 1 - View Entity Relationships (Priority: P1) 🎯 MVP

**Goal**: Deliver a complete Mermaid ER diagram showing all 14 domain entities with every attribute and all 15 relationships

**Independent Test**: Open `docs/data-model.md` in GitHub markdown preview and verify the Mermaid diagram renders with all entities, attributes, and relationship lines

### Implementation for User Story 1

- [x] T002 [US1] Add a Mermaid `erDiagram` code block to `docs/data-model.md` containing all 14 entity definitions with every attribute and its type. Use the entity catalog from `specs/002-openapi-er-docs/data-model.md` as the source of truth. Use camelCase for attribute names (e.g., `userId`, `createdAt`, `scoreState`). Use the type mapping from `specs/002-openapi-er-docs/research.md` (R3). Entities to include: UserBasicProfile (4 attrs), UserBodyMeasurement (3 attrs), Cycle (8 attrs), CycleScore (4 attrs), Sleep (11 attrs), SleepScore (4 attrs), SleepStageSummary (8 attrs), SleepNeeded (4 attrs), Recovery (6 attrs), RecoveryScore (6 attrs), WorkoutV2 (11 attrs), WorkoutScore (8 attrs), ZoneDurations (6 attrs), ActivityIdMappingResponse (1 attr). Exclude pagination wrappers per FR-008.
- [x] T003 [US1] Add all 15 relationship lines to the erDiagram block in `docs/data-model.md` using correct Mermaid cardinality notation. Use the relationships table from `specs/002-openapi-er-docs/data-model.md` as source. Cardinality mappings: one-to-many = `||--o{`, one-to-zero-or-one = `||--o|`, one-to-one = `||--||`. Include descriptive labels on each relationship line (e.g., "has score", "belongs to", "contains").
- [x] T004 [US1] Validate the Mermaid erDiagram syntax in `docs/data-model.md` by checking: (1) all 14 entities are present, (2) attribute count matches — total ~84 attributes across all entities, (3) all 15 relationship lines are present with valid cardinality notation, (4) no syntax errors that would prevent rendering (matching braces, valid relationship operators, no special characters in attribute names)

**Checkpoint**: User Story 1 complete — the ER diagram renders and shows all entities, attributes, and relationships

---

## Phase 3: User Story 2 - Browse Entity Details (Priority: P2)

**Goal**: Add textual descriptions alongside the ER diagram explaining each domain group

**Independent Test**: Read the page and verify each domain group (User, Cycle, Sleep, Recovery, Workout) has a description explaining its role in WHOOP health tracking

### Implementation for User Story 2

- [x] T005 [US2] Add a "Domain Overview" section after the Mermaid diagram in `docs/data-model.md` with five subsections — User, Cycle, Sleep, Recovery, Workout — each containing 2-3 sentences describing the domain group's role in WHOOP health tracking, the key entities in that group, and how they relate to other groups. Source descriptions from the entity descriptions in `openapi.json` and the Key Entities section in `specs/002-openapi-er-docs/spec.md`.

**Checkpoint**: User Story 2 complete — domain overview text is present alongside the diagram

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and cleanup

- [x] T006 Final review of `docs/data-model.md`: verify (1) page renders without errors in markdown preview, (2) all 14 entities present in diagram, (3) all 15 relationships present, (4) domain overview covers all 5 groups, (5) no typos or formatting issues, (6) attribute names and types match `openapi.json`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **User Story 1 (Phase 2)**: Depends on T001 (file must exist)
  - T002 → T003 (entities must exist before adding relationship lines)
  - T003 → T004 (validation after relationships added)
- **User Story 2 (Phase 3)**: Depends on T001 (file must exist). Independent of US1 — can be done in parallel if separate sections.
- **Polish (Phase 4)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Setup — no dependencies on other stories
- **User Story 2 (P2)**: Can start after Setup — independent of US1 (different section of same file)

### Within Each User Story

- US1: Entity definitions (T002) → relationship lines (T003) → validation (T004)
- US2: Single task (T005)

### Parallel Opportunities

- T002 and T005 could be done in parallel (different sections of the same file), but since it's a single file, sequential execution is safer to avoid merge conflicts
- Within T002, all entity definitions are independent of each other (but share a single code block)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: User Story 1 (T002 → T003 → T004)
3. **STOP and VALIDATE**: Open `docs/data-model.md` in GitHub preview, verify diagram renders
4. MVP is deliverable at this point

### Incremental Delivery

1. T001 → Create file → Foundation ready
2. T002 → T003 → T004 → ER diagram complete → MVP deliverable
3. T005 → Domain overview added → Full feature complete
4. T006 → Final review → Ready for merge

---

## Notes

- All tasks modify a single file (`docs/data-model.md`) — execute sequentially to avoid conflicts
- Use `specs/002-openapi-er-docs/data-model.md` as the authoritative source for entities, attributes, and relationships
- Use `specs/002-openapi-er-docs/research.md` (R3) for the OpenAPI-to-Mermaid type mapping
- Use camelCase for Mermaid attribute names (renderer compatibility per research.md R2)
- Commit after each phase checkpoint using `docs:` conventional commit prefix
