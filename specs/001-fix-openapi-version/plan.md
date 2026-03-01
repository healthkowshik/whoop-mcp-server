# Implementation Plan: Fix WHOOP OpenAPI Version Field

**Branch**: `001-fix-openapi-version` | **Date**: 2026-03-01 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-fix-openapi-version/spec.md`

## Summary

The upstream WHOOP OpenAPI spec at
`https://api.prod.whoop.com/developer/doc/openapi.json`
intermittently omits the required `info.version` field,
causing Postman import failures and Swagger Editor validation
error 3030501. This feature implements a Python CLI command
that fetches the upstream spec, patches in the missing
`version` field (defaulting to `"2.0.0"`), and writes the
corrected spec as a static JSON file in the repository.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: httpx (HTTP client)
**Storage**: Local file system (static JSON file)
**Testing**: pytest, openapi-spec-validator (dev dependency)
**Target Platform**: macOS / Linux (developer workstation)
**Project Type**: CLI tool (developer utility)
**Performance Goals**: <5 seconds per invocation (SC-005)
**Constraints**: None significant — single JSON document ~50KB
**Scale/Scope**: Single-file output, single upstream URL

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol Compliance | N/A | This feature is a CLI tool, not an MCP tool |
| II. Health Data Privacy | N/A | OpenAPI spec contains no user health data |
| III. API Contract Fidelity | PASS | FR-005 preserves all upstream fields without modification; only `info.version` is added when absent |
| IV. Test-First Development | PASS | Tests will be written before implementation per task ordering |
| V. Simplicity | PASS | Single-purpose CLI, stdlib argparse, one dependency (httpx) |
| Security: HTTPS | PASS | Upstream URL uses HTTPS; TLS verification enabled by default |
| Security: uv toolchain | PASS | Project managed with uv |

All gates pass. No violations.

## Project Structure

### Documentation (this feature)

```text
specs/001-fix-openapi-version/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli-interface.md
└── tasks.md
```

### Source Code (repository root)

```text
src/
└── whoop_mcp_server/
    ├── __init__.py
    └── fetch_openapi.py

tests/
└── test_fetch_openapi.py

pyproject.toml
```

**Structure Decision**: Single project layout with `src/` directory.
The package `whoop_mcp_server` will host both this CLI utility
and future MCP server code. The CLI entry point is defined in
`pyproject.toml` under `[project.scripts]` so it can be invoked
via `uv run whoop-fetch-openapi`.

## Complexity Tracking

No constitution violations to justify. All principles pass or are N/A.
