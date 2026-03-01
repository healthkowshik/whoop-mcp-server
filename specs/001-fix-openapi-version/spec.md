# Feature Specification: Fix WHOOP OpenAPI Version Field

**Feature Branch**: `001-fix-openapi-version`
**Created**: 2026-03-01
**Status**: Draft
**Input**: User description: "the OpenAPI specification here: https://api.prod.whoop.com/developer/doc/openapi.json sometimes does not have version because of which import on Postman fails as seen with the error 'Swagger says: Error 3 3030501 should always have a version' as seen on https://editor.swagger.io/"

## Clarifications

### Session 2026-03-01

- Q: How should the corrected spec be delivered to the user? → A: A CLI command fetches, patches, and saves the spec as a static file in the repository. This is a developer-facing artifact (for Postman, Swagger Editor, code generators), not an MCP tool — MCP clients discover server capabilities via the MCP protocol, not via raw API specs.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Corrected Spec via CLI (Priority: P1)

A developer runs a CLI command to fetch the WHOOP OpenAPI spec
from the upstream URL, patch in the missing `version` field,
and save the corrected spec as a static file in the repository.
This static file becomes the single source of truth for all
downstream consumers (Postman, Swagger Editor, code generators).

**Why this priority**: The static file is the foundation —
every other user story depends on it existing and being valid.

**Independent Test**: Run the CLI command and verify the output
file is valid OpenAPI 3.0.x with `info.version` present.

**Acceptance Scenarios**:

1. **Given** the upstream WHOOP OpenAPI spec is missing the
   `version` field in the `info` object, **When** the developer
   runs the CLI command, **Then** the output file contains a
   valid `info.version` string value.
2. **Given** the upstream WHOOP OpenAPI spec already includes a
   `version` field, **When** the developer runs the CLI command,
   **Then** the existing `version` value is preserved as-is
   (no overwrite).
3. **Given** the CLI command completes successfully, **When**
   the output file is imported into Postman, **Then** all 13
   endpoints are available as a collection without validation
   errors.
4. **Given** the CLI command completes successfully, **When**
   the output file is loaded into Swagger Editor, **Then**
   error 3030501 does NOT appear.

---

### User Story 2 - Programmatic Spec Consumption (Priority: P2)

A developer or CI pipeline needs to programmatically consume
the WHOOP OpenAPI spec for code generation (e.g., client SDK
generation), linting, or diffing. The static file produced by
the CLI command serves as the input. The corrected spec MUST
work with standard OpenAPI toolchains.

**Why this priority**: Enables automation and downstream
tooling beyond manual import workflows.

**Independent Test**: Run an OpenAPI validator or code generator
against the static spec file and confirm it completes without
version-related errors.

**Acceptance Scenarios**:

1. **Given** the static spec file, **When** an OpenAPI 3.0
   validator checks it, **Then** no errors are reported for
   missing required fields in the `info` object.
2. **Given** the static spec file, **When** a code generation
   tool processes it, **Then** it produces output without
   aborting due to spec validation failures.

---

### Edge Cases

- What happens when the upstream WHOOP API endpoint is
  unreachable or returns a non-200 response? The CLI command
  MUST report the error clearly rather than producing a
  corrupt file.
- What happens when the upstream spec changes its structure
  (e.g., adds a `version` field in the future)? The CLI
  command MUST preserve the upstream value and not overwrite it.
- What happens when the upstream spec returns malformed JSON?
  The CLI command MUST fail with a clear error message rather
  than silently producing invalid output.

## Requirements *(mandatory)*

### Functional Requirements

**CLI Command (spec producer):**

- **FR-001**: The CLI command MUST fetch the OpenAPI spec from
  `https://api.prod.whoop.com/developer/doc/openapi.json`.
- **FR-002**: The CLI command MUST add an `info.version` field
  if one is not present in the upstream spec.
- **FR-003**: The CLI command MUST NOT overwrite an existing
  `info.version` field if the upstream spec already provides
  one.
- **FR-004**: The default version value MUST be a valid
  semantic version string. The value `"2.0.0"` SHOULD be used
  as the default when the upstream spec omits it, reflecting
  the current v2 API generation.
- **FR-005**: The CLI command MUST preserve all other fields
  from the upstream spec without modification.
- **FR-006**: The CLI command MUST write the corrected spec to
  a static file in the repository.
- **FR-007**: The output file MUST be a valid OpenAPI 3.0.x
  document that passes standard OpenAPI validators.
- **FR-008**: The CLI command MUST report clear error messages
  when the upstream spec cannot be fetched or is malformed.

### Key Entities

- **OpenAPI Specification**: The JSON document conforming to
  OpenAPI 3.0.x format, containing API metadata (`info`),
  endpoint definitions (`paths`), and data schemas
  (`components`).
- **Info Object**: The top-level `info` field in the OpenAPI
  spec, which per the standard MUST contain `title` (string)
  and `version` (string).

## Assumptions

- The upstream WHOOP API spec URL
  (`https://api.prod.whoop.com/developer/doc/openapi.json`)
  is publicly accessible and does not require authentication
  to fetch.
- The upstream spec conforms to OpenAPI 3.0.x format aside
  from the missing `version` field.
- The default version `"2.0.0"` is appropriate when the
  upstream spec omits the field, since the current API
  endpoints are v2 (e.g., `/v2/cycle`, `/v2/recovery`) and
  WHOOP provides a v1-to-v2 migration guide.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The corrected spec imports into Postman without
  any validation errors on the first attempt.
- **SC-002**: The corrected spec produces zero errors in
  Swagger Editor related to the `info` object.
- **SC-003**: The corrected spec passes validation by at least
  one standard OpenAPI 3.0 validator without errors.
- **SC-004**: All 13 upstream endpoints are present and
  unmodified in the corrected spec output.
- **SC-005**: Processing completes in under 5 seconds under
  normal network conditions.
