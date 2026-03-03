# Feature Specification: Pydantic Validation for Auth Models

**Feature Branch**: `005-pydantic-validation`
**Created**: 2026-03-03
**Status**: Draft
**Input**: User description: "Use Pydantic Validation"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Validate Token Data at Construction (Priority: P1)

When the token manager receives data from WHOOP's token endpoint or from a persistent store, the system validates all fields (types, non-empty strings, positive expiry values) automatically upon construction. If any field is invalid, the system raises a clear, structured error describing which field failed and why — rather than allowing corrupt data to silently enter the system. This protects downstream consumers from operating with malformed tokens.

**Why this priority**: Invalid token data is the root cause of silent authentication failures. Catching it at the boundary (construction time) prevents cascading bugs in refresh logic, API calls, and store persistence.

**Independent Test**: Construct credential and token objects with both valid and invalid data. Verify valid data succeeds, and each type of invalid data (wrong type, empty string, negative number, missing field) produces a specific, human-readable validation error.

**Acceptance Scenarios**:

1. **Given** a dictionary from WHOOP's token endpoint containing all required fields with correct types, **When** the data is used to construct a token object, **Then** the object is created successfully with all fields accessible.
2. **Given** a dictionary with a missing required field (e.g., no `access_token`), **When** the data is used to construct a token object, **Then** the system raises a validation error that names the missing field.
3. **Given** a dictionary with a field of the wrong type (e.g., `expires_in` as a string instead of an integer), **When** the data is used to construct a token object, **Then** the system either coerces the value to the correct type or raises a clear error.
4. **Given** a token object with a client secret, **When** the object is printed, logged, or converted to a string, **Then** the client secret value is never visible — it is always masked.

---

### User Story 2 - Serialize and Deserialize Token Data for Storage (Priority: P1)

When the token manager persists tokens to a store or loads tokens from a store, the system converts between token objects and dictionaries using a consistent, declarative serialization format. Field names, types, and the monotonic-to-UTC time conversion are handled by the model's serialization layer rather than manual dictionary construction — reducing the risk of serialization bugs and making the format self-documenting.

**Why this priority**: The current manual `dict → TokenPair` and `TokenPair → dict` conversions are the most error-prone code in the token manager. Declarative serialization eliminates a class of bugs where a field is missed or a key is misspelled.

**Independent Test**: Serialize a token object to a dictionary, then deserialize it back. Verify the round trip preserves all field values exactly. Test with edge-case expiry values (near-zero remaining time, far-future expiry).

**Acceptance Scenarios**:

1. **Given** a valid token object, **When** it is serialized to a dictionary for storage, **Then** the dictionary contains all required fields with the correct keys and types as defined in the data model.
2. **Given** a dictionary loaded from a store, **When** it is deserialized into a token object, **Then** all fields are correctly populated, including the monotonic expiry conversion from UTC.
3. **Given** a dictionary with an unexpected extra field, **When** it is deserialized, **Then** the extra field is ignored without error (forward compatibility).

---

### User Story 3 - Parse Token Endpoint Responses Directly (Priority: P2)

When the token manager receives a JSON response from WHOOP's token endpoint, the system parses and validates the response in a single step — constructing a validated token object directly from the response dictionary. If the response is malformed (e.g., missing `refresh_token` when `offline` scope was requested), the system raises a structured error identifying exactly what is wrong.

**Why this priority**: This simplifies `_parse_token_response()` and `_refresh_token()` from manual dict-key-access with fallbacks into a single validated construction call. Valuable but lower priority because the current parsing code already works correctly.

**Independent Test**: Pass sample WHOOP token response dictionaries (valid, missing fields, extra fields, wrong types) through the parsing layer and verify the correct object is returned or a validation error is raised.

**Acceptance Scenarios**:

1. **Given** a valid WHOOP token response dict with `access_token`, `refresh_token`, `expires_in`, `scope`, and `token_type`, **When** it is parsed, **Then** a valid token object is returned with the `expires_at` field computed from `expires_in` and the current monotonic time.
2. **Given** a WHOOP token response missing the `refresh_token` field, **When** it is parsed, **Then** a validation error is raised identifying the missing field.
3. **Given** a WHOOP token response with `expires_in` as a string "3600", **When** it is parsed, **Then** the system coerces it to an integer and creates the token object successfully.

---

### Edge Cases

- What happens when a store returns a dictionary with fields from a newer schema version that the current code doesn't know about? The system should ignore unknown fields gracefully (forward compatibility).
- What happens when a token object is constructed with an `expires_at` value of exactly 0? The system should reject it (must be strictly positive).
- What happens when `client_secret` is an empty string? The system should reject it (must be non-empty).
- What happens when the token response contains `null` for a required field like `scope`? The system should use a sensible default (empty string) or reject it depending on the field.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST validate all fields of credential and token objects at construction time, rejecting invalid data with errors that identify the specific field and reason for failure.
- **FR-002**: System MUST never expose secret values (client_secret, access_token, refresh_token) in string representations, error messages, validation errors, or log output. Secrets MUST be masked in all human-readable output.
- **FR-003**: System MUST provide a declarative serialization method on token objects that converts them to dictionaries matching the existing store format (with `expires_at_utc` as ISO 8601 UTC and all other fields as strings).
- **FR-004**: System MUST provide a declarative deserialization method on token objects that constructs a validated object from a store dictionary, converting `expires_at_utc` back to a monotonic-relative timestamp.
- **FR-005**: System MUST parse WHOOP token endpoint responses into validated token objects in a single construction step, computing `expires_at` from `expires_in` and the current monotonic time.
- **FR-006**: System MUST coerce compatible types (e.g., numeric strings to integers for `expires_in`) rather than rejecting them, while still rejecting truly incompatible types (e.g., a list where a string is expected).
- **FR-007**: System MUST ignore unknown fields when deserializing from a store dictionary or API response (forward compatibility).
- **FR-008**: System MUST maintain the same public API surface as the current implementation — all existing callers of `WhoopCredentials`, `TokenPair`, and `TokenManager` MUST continue to work without modification (backward compatibility).
- **FR-009**: System MUST preserve immutability of credential objects — once constructed, credential fields cannot be modified.
- **FR-010**: System MUST maintain the `is_expired(buffer_seconds)` method on token objects with identical behavior to the current implementation.

### Key Entities

- **WhoopCredentials**: OAuth client credentials (client_id, client_secret). Immutable. Secret values always masked in string output.
- **TokenPair**: Current authentication state (access_token, refresh_token, expires_at, scope, token_type). Validated at construction. Supports serialization to/from store dictionaries with monotonic↔UTC time conversion.
- **TokenResponse**: Intermediate representation of a WHOOP token endpoint response (access_token, refresh_token, expires_in, scope, token_type). Validates the raw API response and computes `expires_at` from `expires_in`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All existing tests pass without modification to test assertions — only imports and construction patterns may change.
- **SC-002**: Invalid token data (wrong types, missing fields, empty strings) is caught at construction time with errors that identify the specific field — 100% of current manual validation cases are covered.
- **SC-003**: Token serialization round-trips (object → store dict → object) preserve all field values exactly, verified across 5+ distinct token states (valid, near-expiry, far-future, minimal scope, full scope).
- **SC-004**: Secret values (client_secret, access_token, refresh_token) never appear in any string representation, validation error, or logged output — verified by searching all string outputs for known test secret values.
- **SC-005**: No new runtime dependencies beyond the validation library itself — no transitive dependency bloat.

## Assumptions

- The validation library will be added as a new runtime dependency. This is acceptable because it is widely used, well-maintained, and provides significant value over manual validation.
- The existing `TokenStore` protocol (using `dict` for save/load) is unchanged. Models serialize *to* dicts for the store and deserialize *from* dicts from the store.
- Error classes (`AuthenticationError`, `TransientError`) are not converted — they are exception types, not data models, and do not benefit from structured validation.
- The `MemoryTokenStore` implementation is unchanged — it stores dicts, and the models handle serialization.
- The `_mask()` helper function may be replaced by the validation library's built-in secret handling, or retained if the library's masking doesn't match the current format.
