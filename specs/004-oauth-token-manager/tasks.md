# Tasks: WHOOP OAuth Token Manager

**Input**: Design documents from `/specs/004-oauth-token-manager/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/token-manager-api.md, quickstart.md

**Tests**: Included. The constitution mandates test-first development (SC-005). All tests use httpx mock transport — no real WHOOP account needed.

**Toolchain**: uv (package management), ruff (linting), ty (type checking), pytest (testing)

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Exact file paths included in all descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the `auth/` subpackage structure, add dependencies, and prepare test directories

- [ ] T001 Create auth subpackage directory with `__init__.py` at `src/whoop_mcp_server/auth/__init__.py`
- [ ] T002 Add `tenacity` as a runtime dependency in `pyproject.toml` via `uv add tenacity`
- [ ] T003 [P] Create test subdirectories `tests/unit/` and `tests/integration/` with `__init__.py` files
- [ ] T004 [P] Add `pytest-asyncio` as a dev dependency in `pyproject.toml` via `uv add --group dev pytest-asyncio`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data types, error classes, and storage protocol that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundational

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T005 [P] Write unit tests for WhoopCredentials (init, repr redaction of client_secret) and TokenPair (init, validation, repr redaction of tokens, expiry check) in `tests/unit/test_models.py`
- [ ] T006 [P] Write unit tests for AuthenticationError (message, status_code, no secrets in str) and TransientError (message, status_code, attempts, no secrets in str) in `tests/unit/test_errors.py`
- [ ] T007 [P] Write unit tests for MemoryTokenStore (save/load round-trip, load returns None when empty) in `tests/unit/test_token_store.py`

### Implementation for Foundational

- [ ] T008 [P] Implement WhoopCredentials and TokenPair dataclasses in `src/whoop_mcp_server/auth/models.py` — WhoopCredentials(client_id, client_secret) with masked `__repr__`; TokenPair(access_token, refresh_token, expires_at, scope, token_type) with validation rules and masked `__repr__` per data-model.md
- [ ] T009 [P] Implement AuthenticationError and TransientError in `src/whoop_mcp_server/auth/errors.py` — AuthenticationError(message, status_code); TransientError(message, status_code, attempts); both with `__str__` that never exposes secrets per contracts/token-manager-api.md
- [ ] T010 [P] Implement TokenStore protocol (`@runtime_checkable`) and MemoryTokenStore in `src/whoop_mcp_server/auth/token_store.py` — Protocol with `async save(data: dict)` and `async load() -> dict | None`; MemoryTokenStore stores in `_data` attribute per data-model.md
- [ ] T011 Wire up public exports in `src/whoop_mcp_server/auth/__init__.py` — export TokenManager, WhoopCredentials, TokenPair, TokenStore, MemoryTokenStore, AuthenticationError, TransientError (TokenManager will be a lazy/forward reference until Phase 3)
- [ ] T012 Verify foundational tests pass: `uv run pytest tests/unit/test_models.py tests/unit/test_errors.py tests/unit/test_token_store.py -v`

**Checkpoint**: Models, errors, and store protocol are complete and tested. User story implementation can begin.

---

## Phase 3: User Story 1 — Exchange Authorization Code for Tokens (Priority: P1) MVP

**Goal**: Exchange a WHOOP authorization code for access + refresh tokens via `exchange_code()`

**Independent Test**: Mock WHOOP's token endpoint, call `exchange_code()` with a valid code, verify tokens are stored and `store.save()` is called. Call with an invalid code, verify `AuthenticationError` is raised with no state change.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T013 [US1] Write unit tests for `exchange_code()` in `tests/unit/test_token_manager.py` — test cases: (1) valid code stores tokens and calls store.save(), (2) invalid code (4xx) raises AuthenticationError with no state change, (3) network error after 3 retries raises TransientError, (4) credentials sent as POST body not Basic Auth, (5) content type is application/x-www-form-urlencoded. Use httpx mock transport.

### Implementation for User Story 1

- [ ] T014 [US1] Implement TokenManager constructor and `exchange_code()` in `src/whoop_mcp_server/auth/token_manager.py` — constructor accepts (credentials: WhoopCredentials, store: TokenStore | None, client: httpx.AsyncClient | None, refresh_buffer_seconds: int = 300); tracks `_owns_client` flag for lifecycle; `exchange_code(code, redirect_uri)` POSTs to `https://api.prod.whoop.com/oauth/oauth2/token` with grant_type=authorization_code, parses response into TokenPair, calls store.save(); uses tenacity retry (3 attempts, 1s/2s/4s backoff, retry on TransportError and 5xx only) per research.md R3/R6
- [ ] T015 [US1] Verify US1 tests pass: `uv run pytest tests/unit/test_token_manager.py -k exchange -v`

**Checkpoint**: Token exchange works. A developer can obtain tokens from an authorization code.

---

## Phase 4: User Story 2 — Get a Valid Token for API Calls (Priority: P1)

**Goal**: `get_valid_token()` returns a valid access token, transparently refreshing if expired or expiring soon

**Independent Test**: Initialize manager with tokens at various expiry states (valid, within buffer, expired), call `get_valid_token()`, verify correct token returned and refresh only happens when needed.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T016 [US2] Write unit tests for `get_valid_token()` in `tests/unit/test_token_manager.py` — test cases: (1) valid token returned immediately without network call, (2) token within refresh buffer triggers refresh then returns new token, (3) expired token triggers refresh then returns new token, (4) no tokens loaded raises AuthenticationError, (5) refresh fails with revoked token (4xx) raises AuthenticationError, (6) refresh fails after 3 retries raises TransientError with attempts count, (7) store.save() called after successful refresh, (8) refresh sends client_id/client_secret in POST body with offline scope. Use httpx mock transport.

### Implementation for User Story 2

- [ ] T017 [US2] Implement `get_valid_token()` and private `_refresh_token()` in `src/whoop_mcp_server/auth/token_manager.py` — `get_valid_token()` checks `_token_pair` existence, compares `expires_at` against `time.monotonic() + refresh_buffer_seconds`, calls `_refresh_token()` if needed; `_refresh_token()` POSTs grant_type=refresh_token to WHOOP endpoint with tenacity retry, updates `_token_pair` and calls store.save(); implement `aclose()` to close internally-managed httpx client per research.md R2/R4
- [ ] T018 [US2] Verify US2 tests pass: `uv run pytest tests/unit/test_token_manager.py -k "get_valid or refresh" -v`

**Checkpoint**: Token retrieval with transparent refresh works. The primary interface is functional.

---

## Phase 5: User Story 3 — Handle Refresh Token Rotation Safely (Priority: P1)

**Goal**: Concurrent `get_valid_token()` calls with an expired token result in exactly one refresh request

**Independent Test**: Simulate 10+ concurrent `get_valid_token()` calls with an expired token, assert exactly one HTTP request to WHOOP's token endpoint, and all callers receive the same new access token.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T019 [P] [US3] Write unit tests for concurrent refresh safety in `tests/unit/test_token_manager.py` — test cases: (1) 10 concurrent `get_valid_token()` calls with expired token produce exactly 1 refresh request, (2) all concurrent callers receive the same new access token, (3) refresh failure under concurrency raises error to all waiters without corrupting state
- [ ] T020 [P] [US3] Write integration test for full token lifecycle in `tests/integration/test_token_refresh_flow.py` — test the complete flow: exchange_code → get_valid_token (valid) → time passes → get_valid_token (triggers refresh) → concurrent get_valid_token (single refresh) → verify token rotation (old tokens never reused). Use httpx mock transport with request counting.

### Implementation for User Story 3

- [ ] T021 [US3] Add asyncio.Lock with double-check pattern to `get_valid_token()` in `src/whoop_mcp_server/auth/token_manager.py` — add `_refresh_lock: asyncio.Lock` to constructor; in `get_valid_token()`: check expiry → if needs refresh, acquire lock → re-check expiry (may have been refreshed by another waiter) → refresh if still needed → release lock. Ensure atomic update of both access_token and refresh_token per research.md R1
- [ ] T022 [US3] Verify US3 tests pass: `uv run pytest tests/unit/test_token_manager.py -k concurrent tests/integration/test_token_refresh_flow.py -v`

**Checkpoint**: Concurrent refresh safety verified. Token rotation cannot cause lockouts.

---

## Phase 6: User Story 4 — Initialize from Pre-Existing Tokens (Priority: P2)

**Goal**: `TokenManager.from_tokens()` factory creates a manager pre-loaded with existing tokens; `store.load()` restores tokens on init

**Independent Test**: Create a manager via `from_tokens()` with known tokens, verify `get_valid_token()` returns the provided token without network calls. Create a manager with a pre-populated store, verify tokens are loaded on init.

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T023 [US4] Write unit tests for `from_tokens()` and store loading in `tests/unit/test_token_manager.py` — test cases: (1) `from_tokens()` creates manager with valid tokens, `get_valid_token()` returns access_token without network call, (2) `from_tokens()` with expired token triggers refresh on first `get_valid_token()`, (3) constructor with populated store loads tokens via `store.load()`, (4) constructor with empty store starts unauthenticated, (5) monotonic-to-UTC conversion for store persistence and UTC-to-monotonic on load per data-model.md serialization format

### Implementation for User Story 4

- [ ] T024 [US4] Implement `from_tokens()` classmethod and store loading in `src/whoop_mcp_server/auth/token_manager.py` — `from_tokens(credentials, access_token, refresh_token, expires_in, **kwargs)` computes `expires_at = time.monotonic() + expires_in` and creates TokenPair; in constructor, if store provided, call `await store.load()` (handle via an `_initialized` flag or async init pattern); implement monotonic↔UTC conversion helpers for store serialization per research.md R4 and data-model.md
- [ ] T025 [US4] Verify US4 tests pass: `uv run pytest tests/unit/test_token_manager.py -k from_tokens -v`

**Checkpoint**: All four user stories complete. Manager can be initialized from code exchange, pre-existing tokens, or persistent store.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validate the complete implementation across all stories

- [ ] T026 Run full test suite: `uv run pytest tests/ -v --tb=short`
- [ ] T027 Run linting: `uv run ruff check src/whoop_mcp_server/auth/ tests/unit/ tests/integration/`
- [ ] T028 Run type checking: `uv run ty check src/whoop_mcp_server/auth/`
- [ ] T029 Finalize `src/whoop_mcp_server/auth/__init__.py` exports — ensure all public symbols (TokenManager, WhoopCredentials, TokenPair, TokenStore, MemoryTokenStore, AuthenticationError, TransientError) are exported and match contracts/token-manager-api.md
- [ ] T030 Validate quickstart.md code examples — run setup commands (`uv sync`, `uv run pytest tests/`, `uv run ruff check src/`) and verify they work

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — creates the TokenManager class
- **US2 (Phase 4)**: Depends on US1 — extends TokenManager with `get_valid_token()` and `_refresh_token()`
- **US3 (Phase 5)**: Depends on US2 — adds concurrency safety to existing refresh logic
- **US4 (Phase 6)**: Depends on Foundational only — `from_tokens()` and store loading are independent of exchange/refresh logic, but practically depends on TokenManager class existing (Phase 3)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1: exchange_code)
                                           ↓
                                           Phase 4 (US2: get_valid_token)
                                           ↓
                                           Phase 5 (US3: concurrent safety)

Phase 2 (Foundational) ─────────────────→ Phase 6 (US4: from_tokens) *

* US4 can start after Phase 2, but since TokenManager is created in Phase 3,
  US4 practically starts after Phase 3. US4 is independent of US2/US3 logic.
```

### Within Each User Story

1. Write tests FIRST — verify they fail
2. Implement the feature
3. Verify tests pass
4. Move to next story

### Parallel Opportunities

**Phase 1**: T003 and T004 can run in parallel (different files)
**Phase 2**: T005/T006/T007 (tests) can run in parallel; T008/T009/T010 (implementation) can run in parallel
**Phase 5**: T019 and T020 (tests) can run in parallel (different files)
**Phase 7**: T027 and T028 can run in parallel

---

## Parallel Example: Phase 2 (Foundational)

```bash
# Launch all foundational tests together (different files):
Task T005: "Write unit tests for models in tests/unit/test_models.py"
Task T006: "Write unit tests for errors in tests/unit/test_errors.py"
Task T007: "Write unit tests for token store in tests/unit/test_token_store.py"

# Launch all foundational implementations together (different files):
Task T008: "Implement models in src/whoop_mcp_server/auth/models.py"
Task T009: "Implement errors in src/whoop_mcp_server/auth/errors.py"
Task T010: "Implement token store in src/whoop_mcp_server/auth/token_store.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: US1 — Exchange Code
4. Complete Phase 4: US2 — Get Valid Token
5. **STOP and VALIDATE**: The manager can exchange codes and return valid tokens with automatic refresh
6. This is a usable MVP — callers can `exchange_code()` then `get_valid_token()` repeatedly

### Incremental Delivery

1. Setup + Foundational → Core types ready
2. Add US1 (exchange) → Can obtain tokens
3. Add US2 (get_valid_token) → **MVP!** Transparent refresh works
4. Add US3 (concurrent safety) → Production-hardened
5. Add US4 (from_tokens) → Developer ergonomics for testing/local dev
6. Polish → Linting, type checking, quickstart validation

### Single Developer Strategy

Work sequentially: Phase 1 → 2 → 3 → 4 → 5 → 6 → 7. Within each phase, write tests first, then implement, then verify. All stories build on the same `token_manager.py` file, so parallel story work is not practical for a single developer.

---

## Notes

- All tests use httpx mock transport (`httpx.MockTransport`) — no real WHOOP account needed
- The `token_manager.py` file is touched by US1–US4; avoid parallel story implementation on the same file
- `time.monotonic()` used for in-process expiry; UTC ISO 8601 for persistence (store serialization)
- tenacity retry: 3 attempts, exponential backoff 1s/2s/4s, retry only on TransportError and 5xx
- Astral toolchain: `uv` for deps, `ruff` for linting, `ty` for type checking
- Total tasks: 30
