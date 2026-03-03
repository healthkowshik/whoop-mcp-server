# Tasks: Pydantic Validation for Auth Models

**Input**: Design documents from `/specs/005-pydantic-validation/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/models-api.md, quickstart.md

**Tests**: Included per Constitution Principle IV (Test-First Development).

**Organization**: Tasks grouped by user story. US1 is foundational — US2 and US3 depend on US1 completion.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Add pydantic dependency and establish test baseline

- [x] T001 Add pydantic>=2.10.0 as runtime dependency via `uv add "pydantic>=2.10.0"` in pyproject.toml
- [x] T002 Run existing test suite (`uv run pytest tests/ -v`) to establish baseline — all 63 tests must pass

**Checkpoint**: Pydantic installed, all existing tests green

---

## Phase 2: User Story 1 — Validate Token Data at Construction (Priority: P1) MVP

**Goal**: Replace manual dataclass validation with Pydantic BaseModel for WhoopCredentials and TokenPair. Both models frozen (immutable). Custom `__repr__` masks secrets. `is_expired()` preserved.

**Independent Test**: Construct credential and token objects with valid and invalid data. Verify validation catches missing fields, empty strings, wrong types, and zero/negative expiry. Verify immutability prevents field mutation. Verify secrets are masked in repr/str.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T003 [P] [US1] Write new WhoopCredentials validation tests in tests/unit/test_models.py — add tests for: empty client_id raises ValueError, empty client_secret raises ValueError, immutability (setting client_id raises error), type preserved (client_id and client_secret remain str not SecretStr)
- [x] T004 [P] [US1] Write new TokenPair validation tests in tests/unit/test_models.py — add tests for: expires_at=0 raises ValueError (must be strictly > 0, not just positive), immutability (setting expires_at raises error), model_copy creates valid new instance with updated field, unknown extra kwargs are silently ignored (forward compat)

### Implementation for User Story 1

- [x] T005 [US1] Rewrite WhoopCredentials as frozen Pydantic BaseModel in src/whoop_mcp_server/auth/models.py — define `NonEmptyStr = Annotated[str, Field(min_length=1)]` type alias, use `model_config = ConfigDict(frozen=True, extra='ignore')`, keep `_mask()` helper, override `__repr__` and `__str__` to mask client_secret
- [x] T006 [US1] Rewrite TokenPair as frozen Pydantic BaseModel in src/whoop_mcp_server/auth/models.py — use NonEmptyStr for access_token and refresh_token, use `Field(gt=0)` for expires_at, use `model_config = ConfigDict(frozen=True, extra='ignore')`, override `__repr__` to mask access_token and refresh_token via `_mask()`, preserve `is_expired(buffer_seconds: float = 0) -> bool` method with identical behavior
- [x] T007 [US1] Update tests/unit/test_token_manager.py — find all direct mutations of `_token_pair.expires_at` and replace with `manager._token_pair = manager._token_pair.model_copy(update={"expires_at": new_value})` pattern
- [x] T008 [US1] Update tests/integration/test_token_refresh_flow.py — replace `manager._token_pair.expires_at = time.monotonic() + 60` and `manager._token_pair.expires_at = time.monotonic() - 10` with `model_copy(update={...})` pattern
- [x] T009 [US1] Run full test suite (`uv run pytest tests/ -v`) — verify all existing tests (with adapted mutation patterns) + new validation tests pass

**Checkpoint**: WhoopCredentials and TokenPair are Pydantic models with validation, immutability, and masking. All tests green.

---

## Phase 3: User Story 2 — Serialize and Deserialize Token Data for Storage (Priority: P1)

**Goal**: Add `to_store_dict()` and `from_store_dict()` methods to TokenPair. Refactor TokenManager to use these methods instead of manual dict construction. Monotonic↔UTC conversion handled declaratively in the model.

**Independent Test**: Serialize a TokenPair to store dict, deserialize back. Verify round trip preserves all values. Test 5+ distinct states. Verify forward compatibility (extra fields ignored on deserialize).

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T010 [US2] Write serialization round-trip tests in tests/unit/test_models.py — test cases: (1) valid token round-trip preserves access_token/refresh_token/scope/token_type exactly and expires_at within 1s tolerance, (2) near-expiry token (1s remaining), (3) far-future token (30 days), (4) minimal scope (empty string), (5) full scope ("offline read:recovery read:sleep"), (6) from_store_dict ignores unknown extra fields, (7) from_store_dict with missing expires_at_utc treats as expired, (8) from_store_dict with corrupted data raises ValueError or KeyError, (9) to_store_dict output has keys: access_token, refresh_token, expires_at_utc, scope, token_type

### Implementation for User Story 2

- [x] T011 [US2] Add `to_store_dict() -> dict` instance method to TokenPair in src/whoop_mcp_server/auth/models.py — convert monotonic expires_at to UTC ISO 8601 `expires_at_utc` string, include all fields as strings matching existing store format
- [x] T012 [US2] Add `from_store_dict(data: dict) -> TokenPair` classmethod to TokenPair in src/whoop_mcp_server/auth/models.py — parse `expires_at_utc` ISO 8601 string back to monotonic-relative float, handle missing expires_at_utc (treat as expired), use `max(expires_at, 0.01)` to ensure positive, use `.get()` with defaults for scope ("") and token_type ("bearer")
- [x] T013 [US2] Refactor `_save_to_store()` in src/whoop_mcp_server/auth/token_manager.py — replace manual dict construction with `self._token_pair.to_store_dict()`
- [x] T014 [US2] Refactor `_load_from_store()` in src/whoop_mcp_server/auth/token_manager.py — replace manual UTC→monotonic conversion and TokenPair construction with `TokenPair.from_store_dict(data)`, keep try/except for corrupted store data
- [x] T015 [US2] Run full test suite (`uv run pytest tests/ -v`) — verify all tests pass including new serialization tests

**Checkpoint**: Serialization logic lives in TokenPair model. TokenManager uses model methods. Round-trip tests pass for 5+ states.

---

## Phase 4: User Story 3 — Parse Token Endpoint Responses Directly (Priority: P2)

**Goal**: Create TokenResponse Pydantic model that validates WHOOP API responses and converts to TokenPair via `to_token_pair()`. Refactor `_parse_token_response()` to use it.

**Independent Test**: Pass valid/invalid WHOOP response dicts through TokenResponse. Verify valid responses produce correct TokenPair. Verify missing fields raise ValidationError. Verify string "3600" coerced to int 3600.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T016 [US3] Write TokenResponse validation tests in tests/unit/test_models.py — test cases: (1) valid response creates TokenResponse with correct fields, (2) missing access_token raises ValueError, (3) missing refresh_token raises ValueError, (4) expires_in as string "3600" coerced to int 3600, (5) extra unknown fields silently ignored, (6) to_token_pair() returns TokenPair with expires_at = monotonic + expires_in, (7) to_token_pair() TokenPair has matching access_token/refresh_token/scope/token_type, (8) default scope is empty string when not provided, (9) default token_type is "bearer" when not provided

### Implementation for User Story 3

- [x] T017 [US3] Create TokenResponse Pydantic model in src/whoop_mcp_server/auth/models.py — fields: access_token (NonEmptyStr), refresh_token (NonEmptyStr), expires_in (int, gt=0), scope (str, default=""), token_type (str, default="bearer"); config: `extra='ignore'`; method: `to_token_pair() -> TokenPair` that creates TokenPair with `expires_at=time.monotonic() + self.expires_in`
- [x] T018 [US3] Add TokenResponse to exports in src/whoop_mcp_server/auth/__init__.py — add to imports and __all__ list (8 symbols total)
- [x] T019 [US3] Refactor `_parse_token_response()` in src/whoop_mcp_server/auth/token_manager.py — replace manual dict access with `TokenResponse.model_validate(data).to_token_pair()`
- [x] T020 [US3] Run full test suite (`uv run pytest tests/ -v`) — verify all tests pass including new TokenResponse tests

**Checkpoint**: TokenResponse parses and validates API responses. _parse_token_response() is a one-liner. All tests green.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Lint, type check, verify exports, and validate quickstart scenarios

- [x] T021 [P] Run `uv run ruff check .` and fix any lint issues (unused imports, line length, sort order)
- [x] T022 [P] Run `uv run ty check src/` and fix any type errors
- [x] T023 Verify __init__.py exports match contract — 8 symbols: AuthenticationError, MemoryTokenStore, TokenManager, TokenPair, TokenResponse, TokenStore, TransientError, WhoopCredentials
- [x] T024 Run quickstart.md validation scenarios — verify all 5 scenarios work as documented

**Checkpoint**: All quality gates pass. Feature complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **US1 (Phase 2)**: Depends on Setup — FOUNDATIONAL for US2 and US3
- **US2 (Phase 3)**: Depends on US1 (needs TokenPair Pydantic model with working validation)
- **US3 (Phase 4)**: Depends on US1 (TokenResponse.to_token_pair() creates a TokenPair)
- **Polish (Phase 5)**: Depends on all user stories complete

### User Story Dependencies

```
Setup (Phase 1)
  └─→ US1: Validate at Construction (Phase 2) ← FOUNDATIONAL
        ├─→ US2: Serialize/Deserialize (Phase 3)
        └─→ US3: Parse Responses (Phase 4)  ← can run parallel with US2
              └─→ Polish (Phase 5)
```

- **US2 and US3 can run in parallel** after US1 completes — they modify different methods in token_manager.py (_save_to_store/_load_from_store vs _parse_token_response)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Model changes before token_manager refactoring
- Run full test suite at end of each story

### Parallel Opportunities

- T003 + T004: Both write to test_models.py but different test classes — can run in parallel
- T007 + T008: Different test files — can run in parallel
- US2 + US3: Different token_manager methods — can run in parallel after US1
- T021 + T022: Lint and type check — can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch tests in parallel (different test classes in same file):
Task T003: "Write WhoopCredentials validation tests in tests/unit/test_models.py"
Task T004: "Write TokenPair validation tests in tests/unit/test_models.py"

# Launch test file updates in parallel (different files):
Task T007: "Update tests/unit/test_token_manager.py — model_copy pattern"
Task T008: "Update tests/integration/test_token_refresh_flow.py — model_copy pattern"
```

## Parallel Example: US2 + US3 After US1

```bash
# After US1 is complete, launch both stories in parallel:
# Stream 1 (US2): T010 → T011 → T012 → T013 → T014 → T015
# Stream 2 (US3): T016 → T017 → T018 → T019 → T020
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: US1 — Validate at Construction (T003-T009)
3. **STOP and VALIDATE**: All existing tests pass, validation works, models are frozen
4. This alone delivers FR-001, FR-002, FR-006, FR-007, FR-008, FR-009, FR-010

### Incremental Delivery

1. Setup → US1 → **MVP: Pydantic models with validation** (SC-001, SC-002, SC-004 met)
2. Add US2 → **Declarative serialization** (SC-003 met)
3. Add US3 → **Single-step API response parsing** (FR-005 met)
4. Polish → **All quality gates pass** (SC-005 verified)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- US1 is foundational — must complete before US2 or US3
- US2 and US3 are independent of each other
- Each story ends with a full test suite run
- Commit after each completed story phase
