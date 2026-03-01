---
description: "Task list for Fix WHOOP OpenAPI Version Field"
---

# Tasks: Fix WHOOP OpenAPI Version Field

**Input**: Design documents from `/specs/001-fix-openapi-version/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/cli-interface.md

**Tests**: Included — constitution principle IV (Test-First Development) requires TDD.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize the Python project with uv, dependencies, and package structure

- [ ] T001 Create pyproject.toml at repository root with: project name `whoop-mcp-server`, Python >=3.11, dependency `httpx`, dev dependencies `pytest`, `openapi-spec-validator`, `ruff`, and `ty`, CLI entry point `whoop-fetch-openapi = "whoop_mcp_server.fetch_openapi:main"`, pytest config `testpaths = ["tests"]`, ruff config (line-length 88, target Python 3.11), and ty config (strict mode)
- [ ] T002 [P] Create src/whoop_mcp_server/__init__.py with package docstring
- [ ] T003 [P] Create .python-version containing `3.11`
- [ ] T004 Run `uv sync` to install dependencies and generate uv.lock

**Checkpoint**: `uv run python -c "import whoop_mcp_server"` succeeds and `uv run pytest --co` runs without import errors.

---

## Phase 2: User Story 1 - Generate Corrected Spec via CLI (Priority: P1) MVP

**Goal**: A developer runs `uv run whoop-fetch-openapi` to fetch the upstream WHOOP OpenAPI spec, patch the missing `info.version` field, and write a corrected JSON file.

**Independent Test**: Run `uv run whoop-fetch-openapi --output /tmp/test.json` and verify the output contains `info.version`, all 13 endpoints, and imports into Postman without errors.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T005 [US1] Write tests in tests/test_fetch_openapi.py covering: (a) when `info.version` is missing, patched spec contains `"version": "2.0.0"` in `info` (FR-002, FR-004), (b) when `info.version` is already present, existing value is preserved (FR-003), (c) all non-info fields are preserved without modification (FR-005), (d) output is written to the path specified by `--output` flag (FR-006), (e) default output path is `openapi.json` when `--output` is omitted. Use httpx mock/transport to avoid real network calls. Use sample OpenAPI JSON fixtures inline.
- [ ] T006 [US1] Write error handling tests in tests/test_fetch_openapi.py covering: (a) fetch error (non-200 response) exits with code 1 and prints error to stderr (FR-008), (b) malformed JSON response exits with code 2 and prints error to stderr (FR-008). Use httpx mock/transport to simulate failures.
- [ ] T007 [US1] Run `uv run pytest tests/test_fetch_openapi.py` and verify all tests FAIL (no implementation yet)

### Implementation for User Story 1

- [ ] T008 [US1] Implement core logic in src/whoop_mcp_server/fetch_openapi.py: `fetch_openapi_spec(url: str) -> dict` that fetches JSON via httpx with error handling (exit 1 for fetch errors, exit 2 for JSON parse errors), `patch_version(spec: dict, default: str = "2.0.0") -> dict` that adds `info.version` only if missing, and `write_spec(spec: dict, output_path: str) -> None` that writes JSON to file
- [ ] T009 [US1] Implement CLI entry point `main()` in src/whoop_mcp_server/fetch_openapi.py using argparse with `--output` flag (default `openapi.json`), wiring fetch → patch → write, printing output path to stdout on success, printing errors to stderr on failure
- [ ] T010 [US1] Run `uv run pytest tests/test_fetch_openapi.py` and verify all tests PASS

**Checkpoint**: `uv run whoop-fetch-openapi --output /tmp/test.json` produces a valid patched OpenAPI spec. All 7 test cases pass.

---

## Phase 3: User Story 2 - Programmatic Spec Consumption (Priority: P2)

**Goal**: The static spec file produced by US1 passes standard OpenAPI 3.0 validators and works with code generation toolchains.

**Independent Test**: Run openapi-spec-validator against the output file and confirm zero errors.

### Tests for User Story 2

- [ ] T011 [US2] Write OpenAPI validation test in tests/test_fetch_openapi.py: given a patched spec (using the same mock fixture from US1 tests), validate it with `openapi_spec_validator.validate` and assert no exceptions (SC-003). Also assert all 13 endpoint paths from the upstream spec are present in the output (SC-004).
- [ ] T012 [US2] Run `uv run pytest tests/test_fetch_openapi.py` and verify all tests PASS (including new validation tests)

**Checkpoint**: openapi-spec-validator confirms the patched spec is fully compliant OpenAPI 3.0.x with all 13 endpoints intact.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Generate the actual output file and validate the quickstart workflow

- [ ] T013 [P] Run `uv run ruff check src/ tests/` and `uv run ty src/` to verify linting and type checking pass with zero errors
- [ ] T014 Run `uv run whoop-fetch-openapi` to generate openapi.json at repository root
- [ ] T015 Validate quickstart.md by following its steps: verify `uv sync` works, `uv run whoop-fetch-openapi` produces output, and `uv run pytest` passes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **User Story 1 (Phase 2)**: Depends on Setup completion
- **User Story 2 (Phase 3)**: Depends on User Story 1 tests and implementation (uses same fixtures)
- **Polish (Phase 4)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Setup (Phase 1). No dependencies on other stories.
- **User Story 2 (P2)**: Can start after User Story 1 implementation. Adds validation tests that build on US1 fixtures.

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Core logic before CLI wiring
- Run tests after implementation to confirm pass

### Parallel Opportunities

- T002 and T003 can run in parallel (different files, no dependencies)
- T005 and T006 are sequential (same file `tests/test_fetch_openapi.py`)

---

## Parallel Example: User Story 1

```bash
# Write both test files in parallel:
Task: "Write core logic tests in tests/test_fetch_openapi.py" (T005)
Task: "Write error handling tests in tests/test_fetch_openapi.py" (T006)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: User Story 1 (tests → implementation → verify)
3. **STOP and VALIDATE**: Run `uv run whoop-fetch-openapi` and import output into Postman
4. The CLI tool is fully functional at this point

### Incremental Delivery

1. Complete Setup → Project ready
2. Add User Story 1 → CLI works → Test with Postman/Swagger Editor (MVP!)
3. Add User Story 2 → Validation confirmed → Ready for CI integration
4. Polish → openapi.json committed, quickstart validated

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- All tests mock HTTP calls via httpx mock transport — no real network calls in tests
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
