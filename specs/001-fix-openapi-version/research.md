# Research: Fix WHOOP OpenAPI Version Field

## HTTP Client

**Decision**: httpx
**Rationale**: Modern Python HTTP client with a clean API,
sync and async support, and sensible defaults (TLS verification
enabled, connection pooling). Will be reused when the MCP
server needs to call the WHOOP API in future features.
**Alternatives considered**:
- `urllib.request` (stdlib): Zero dependencies but verbose
  error handling and manual content-type management.
- `requests`: Mature but no async support; httpx is the
  modern successor with the same API style.

## CLI Framework

**Decision**: argparse (stdlib)
**Rationale**: The CLI needs exactly one optional flag
(`--output` for the output file path). argparse handles this
with zero external dependencies. Adding click or typer for a
single flag violates the Simplicity principle.
**Alternatives considered**:
- `click`: Overkill for one flag.
- `typer`: Adds click as a transitive dependency for
  negligible benefit at this scale.

## OpenAPI Validation

**Decision**: openapi-spec-validator (dev dependency only)
**Rationale**: Purpose-built for validating complete OpenAPI
3.0.x documents against the specification. Used only in tests
to verify the patched output is fully compliant.
**Alternatives considered**:
- `jsonschema`: Too generic — validates JSON structure but
  not OpenAPI-specific rules (e.g., required `info.version`).
- `openapi-core`: Designed for request/response validation
  against a spec, not for validating the spec document itself.

## Output File Location

**Decision**: `openapi.json` at repository root
**Rationale**: Simple, discoverable location. Developers can
import this file directly into Postman or reference it in CI
pipelines. The file is committed to version control so it
persists across clones.
**Alternatives considered**:
- `docs/openapi.json`: Adds a directory for a single file.
- `data/openapi.json`: Non-standard for API specs.

## Python Version

**Decision**: Python 3.11+
**Rationale**: Minimum version that provides modern typing
features (PEP 604 union syntax, TypedDict improvements) and
is widely available. The `.gitignore` already targets Python.
**Alternatives considered**:
- Python 3.12+: Too restrictive for contributors on older
  systems; no 3.12-specific features needed.
- Python 3.10: Lacks some typing ergonomics used in httpx.

## Package Layout

**Decision**: `src/whoop_mcp_server/` with `uv init --package`
style layout
**Rationale**: Proper `src/` layout isolates package code from
project root, prevents accidental imports of uninstalled code,
and scales cleanly when the MCP server is added later. The
`whoop_mcp_server` package name matches the project identity.
**Alternatives considered**:
- Flat layout (`whoop_mcp_server/` at root): Works but
  doesn't isolate package from test/script imports.
- Standalone script: No test infrastructure, no entry points.
