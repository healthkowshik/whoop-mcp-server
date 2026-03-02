# Implementation Plan: WHOOP OAuth Token Manager

**Branch**: `004-oauth-token-manager` | **Date**: 2026-03-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-oauth-token-manager/spec.md`

## Summary

Build an async Python module that manages WHOOP OAuth tokens — exchanging authorization codes, transparently refreshing expired tokens with concurrent-safe locking, and persisting token state through a pluggable store interface. The module uses httpx for HTTP, asyncio.Lock for concurrency safety, tenacity for retry, and typing.Protocol for the storage interface.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: httpx (HTTP client), tenacity (retry with backoff)
**Storage**: Pluggable `TokenStore` protocol — default in-memory; persistent implementations provided by deployment layer
**Testing**: pytest + httpx mock transport (no real WHOOP account needed)
**Target Platform**: Linux server / macOS development
**Project Type**: Library module (within the whoop-mcp-server package)
**Performance Goals**: <50ms for cached token lookup (SC-001); exactly 1 refresh under concurrent load (SC-002)
**Constraints**: Single-process async; in-memory locking; no secrets in error output
**Scale/Scope**: Single-user token management; multi-user is a deployment-layer concern

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol Compliance | N/A | This module is below the MCP layer — it provides tokens to MCP tools, not MCP interfaces directly. |
| II. Health Data Privacy | PASS | Tokens stored only in memory or user-controlled store (FR-014). Secrets never in logs/errors (FR-013). No health data handled by this module. |
| III. API Contract Fidelity | PASS | Token endpoint request/response format matches WHOOP documentation exactly (FR-001, FR-002). No lossy transformation. |
| IV. Test-First Development | PASS | All acceptance scenarios testable with mocked responses (SC-005). Tests written before implementation per constitution. |
| V. Simplicity | PASS | Minimal surface: one class (TokenManager), one protocol (TokenStore), two error types. No speculative abstractions. tenacity is the only new dependency. |
| Security & Data Handling | PASS | HTTPS enforced (WHOOP endpoint is HTTPS). Client secrets not in source (passed at init). Credential redaction in all repr/error output (FR-013). |

**Post-Phase 1 re-check**: All gates still pass. The data model adds no unnecessary complexity — 5 entities total, each with a clear single responsibility. The TokenStore protocol has exactly 2 methods. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/004-oauth-token-manager/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: technology decisions
├── data-model.md        # Phase 1: entity definitions
├── quickstart.md        # Phase 1: setup and usage guide
├── contracts/
│   └── token-manager-api.md  # Phase 1: public API contract
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/whoop_mcp_server/
├── __init__.py                  # Existing package init
├── fetch_openapi.py             # Existing (feature 001)
└── auth/                        # NEW: auth subpackage
    ├── __init__.py              # Public exports
    ├── token_manager.py         # TokenManager class (core logic)
    ├── token_store.py           # TokenStore protocol + MemoryTokenStore
    ├── models.py                # TokenPair, WhoopCredentials dataclasses
    └── errors.py                # AuthenticationError, TransientError

tests/
├── test_fetch_openapi.py        # Existing (feature 001)
├── unit/
│   ├── test_token_manager.py    # Exchange, refresh, get_valid_token, concurrent refresh
│   ├── test_token_store.py      # MemoryTokenStore save/load
│   ├── test_models.py           # Validation, repr redaction
│   └── test_errors.py           # Error message redaction
└── integration/
    └── test_token_refresh_flow.py  # Full exchange → expiry → refresh → concurrent refresh
```

**Structure Decision**: Single project with a new `auth/` subpackage under the existing `src/whoop_mcp_server/`. Tests split into `unit/` and `integration/` subdirectories alongside the existing flat test file. This follows the established package structure and avoids unnecessary nesting.
