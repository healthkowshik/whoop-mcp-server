# Feature Specification: Fix WHOOP OpenAPI Version Field

**Feature Branch**: `001-fix-openapi-version`
**Created**: 2026-03-01
**Status**: Draft
**Input**: User description: "the OpenAPI specification here: https://api.prod.whoop.com/developer/doc/openapi.json sometimes does not have version because of which import on Postman fails as seen with the error 'Swagger says: Error 3 3030501 should always have a version' as seen on https://editor.swagger.io/"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Import WHOOP API into Postman (Priority: P1)

A developer wants to import the WHOOP API specification into
Postman to explore and test endpoints. They paste the WHOOP
OpenAPI URL into Postman's import dialog, but the import fails
because the upstream spec is missing the required `version`
field in the `info` object. The developer needs a corrected
version of the spec that Postman accepts without manual editing.

**Why this priority**: This is the core problem — without a
valid spec, developers cannot use standard API tooling at all.

**Independent Test**: Fetch the corrected spec and import it
into Postman; the import completes without errors.

**Acceptance Scenarios**:

1. **Given** the upstream WHOOP OpenAPI spec is missing the
   `version` field in the `info` object, **When** the system
   fetches and patches the spec, **Then** the output spec
   contains a valid `info.version` string value.
2. **Given** the upstream WHOOP OpenAPI spec already includes a
   `version` field, **When** the system fetches and patches the
   spec, **Then** the existing `version` value is preserved
   as-is (no overwrite).
3. **Given** the patched spec is imported into Postman,
   **When** the import completes, **Then** all 13 endpoints
   are available as a collection without validation errors.

---

### User Story 2 - Validate WHOOP API in Swagger Editor (Priority: P2)

A developer pastes or loads the WHOOP OpenAPI spec into Swagger
Editor to review endpoint schemas and try out requests. The
editor displays error 3030501 ("should always have a 'version'")
because the spec violates the OpenAPI 3.0.x requirement that
`info.version` is a mandatory field. The developer needs a
spec that passes Swagger Editor validation cleanly.

**Why this priority**: Swagger Editor is the standard validation
tool; passing validation builds confidence that the spec is
correct for any downstream consumer, not just Postman.

**Independent Test**: Load the corrected spec in Swagger Editor
and confirm zero validation errors related to the `info.version`
field.

**Acceptance Scenarios**:

1. **Given** the corrected spec is loaded into Swagger Editor,
   **When** validation runs, **Then** error 3030501 ("should
   always have a 'version'") does NOT appear.
2. **Given** the corrected spec is loaded into Swagger Editor,
   **When** the developer browses endpoints, **Then** all
   endpoints render correctly with their schemas.

---

### User Story 3 - Programmatic Spec Consumption (Priority: P3)

A developer or CI pipeline needs to programmatically consume
the WHOOP OpenAPI spec for code generation (e.g., client SDK
generation), linting, or diffing. The missing `version` field
causes these tools to reject the spec. The corrected spec MUST
work with standard OpenAPI toolchains.

**Why this priority**: Enables automation and downstream
tooling beyond manual import workflows.

**Independent Test**: Run an OpenAPI validator or code generator
against the corrected spec and confirm it completes without
version-related errors.

**Acceptance Scenarios**:

1. **Given** the corrected spec, **When** an OpenAPI 3.0
   validator checks it, **Then** no errors are reported for
   missing required fields in the `info` object.
2. **Given** the corrected spec, **When** a code generation
   tool processes it, **Then** it produces output without
   aborting due to spec validation failures.

---

### Edge Cases

- What happens when the upstream WHOOP API endpoint is
  unreachable or returns a non-200 response? The system MUST
  report the error clearly rather than producing a corrupt spec.
- What happens when the upstream spec changes its structure
  (e.g., adds a `version` field in the future)? The system
  MUST preserve the upstream value and not overwrite it.
- What happens when the upstream spec returns malformed JSON?
  The system MUST fail with a clear error message rather than
  silently producing invalid output.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST fetch the OpenAPI spec from
  `https://api.prod.whoop.com/developer/doc/openapi.json`.
- **FR-002**: The system MUST add an `info.version` field if
  one is not present in the upstream spec.
- **FR-003**: The system MUST NOT overwrite an existing
  `info.version` field if the upstream spec already provides
  one.
- **FR-004**: The default version value MUST be a valid
  semantic version string. The value `"2.0.0"` SHOULD be used
  as the default when the upstream spec omits it, reflecting
  the current v2 API generation.
- **FR-005**: The system MUST preserve all other fields from
  the upstream spec without modification.
- **FR-006**: The output MUST be a valid OpenAPI 3.0.x
  document that passes standard OpenAPI validators.
- **FR-007**: The system MUST report clear error messages when
  the upstream spec cannot be fetched or is malformed.

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
