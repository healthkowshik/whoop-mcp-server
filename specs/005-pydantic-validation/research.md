# Research: Pydantic Validation for Auth Models

**Feature**: 005-pydantic-validation
**Date**: 2026-03-03

## Decision 1: SecretStr vs Plain String with Custom Repr

**Decision**: Use plain `str` fields with custom `__repr__` masking — do NOT use `SecretStr`.

**Rationale**: `SecretStr` changes the type of the field. Existing tests assert `creds.client_secret == "my-client-secret"` and integration code accesses `self._token_pair.access_token` as a raw string. Using `SecretStr` would break these comparisons (`SecretStr != str`) and require `.get_secret_value()` calls throughout, violating FR-008 (backward compatibility) and SC-001 (existing tests pass without assertion changes).

**Alternatives considered**:
- `SecretStr` with `.get_secret_value()` everywhere — too invasive, breaks backward compat
- `SecretStr` with custom `__eq__` override — fragile hack
- Plain `str` with `Field(repr=False)` — excludes field entirely from repr instead of masking

**Pattern chosen**: Retain `_mask()` helper, override `__repr__` on models using `__repr_args__` or direct `__repr__` method.

## Decision 2: Non-Empty String Validation

**Decision**: Use `Annotated[str, Field(min_length=1)]` — the idiomatic Pydantic v2 declarative pattern.

**Rationale**: Declarative, composable as a type alias (`NonEmptyStr = Annotated[str, Field(min_length=1)]`), and more readable than `@field_validator` for simple constraints. `constr()` is deprecated in v2.

**Alternatives considered**:
- `@field_validator` with manual check — overkill for simple min_length
- `constr(min_length=1)` — deprecated in Pydantic v2

## Decision 3: Forward Compatibility (Unknown Fields)

**Decision**: Use `ConfigDict(extra='ignore')` explicitly.

**Rationale**: This is already the Pydantic v2 default, but setting it explicitly documents the intent (FR-007) and prevents breakage if a future Pydantic version changes the default.

## Decision 4: Type Coercion (String-to-Int)

**Decision**: Rely on Pydantic v2's default lax mode — `"3600"` is automatically coerced to `int`.

**Rationale**: Pydantic v2 coerces compatible types by default (FR-006). No configuration needed. To disable coercion per-field, use `Field(strict=True)` or `StrictInt`.

## Decision 5: Serialization — Monotonic-to-UTC Conversion

**Decision**: Use explicit `to_store_dict()` instance method and `from_store_dict()` classmethod on `TokenPair`, rather than `@field_serializer`/`@field_validator`.

**Rationale**: The monotonic↔UTC conversion depends on `time.monotonic()` and `datetime.now(timezone.utc)` at call time — these are runtime-dependent computations, not simple type transformations. `@field_serializer` operates on field values only and cannot inject external state (current wall-clock time). Explicit methods make the time dependency visible and testable.

**Alternatives considered**:
- `@field_serializer('expires_at')` + `@field_validator('expires_at', mode='before')` — cannot handle the monotonic↔UTC conversion cleanly since it requires knowing the current monotonic time at deserialization
- `@model_serializer` — replaces entire dict output, too coarse for one field transformation
- `model_dump()` override — not idiomatic, breaks Pydantic's serialization contract

## Decision 6: ValidationError Compatibility

**Decision**: Pydantic v2's `ValidationError` IS a `ValueError` subclass. Existing `pytest.raises(ValueError, match="access_token")` tests will continue to work.

**Rationale**: Pydantic v2 inherits `ValueError`. The `match=` regex tests match against `str(exc)`, which includes field names. Tests like `match="access_token"` will match because Pydantic's error format includes the field name. Message format is different (`"String should have at least 1 character"` vs our manual `"access_token must be a non-empty string"`) but the field name still appears.

**Caveat**: If any test matches on the exact manual error message text, it will break. Current tests only match on field names, so they're safe.

## Decision 7: Frozen Model Mutation in Tests

**Decision**: Use `model_copy(update={...})` to create modified copies instead of direct field mutation.

**Rationale**: `model_copy(update={"expires_at": new_value})` creates a new instance without modifying the original — compatible with `frozen=True`. This replaces `manager._token_pair.expires_at = time.monotonic() + 60` in integration tests.

## Decision 8: Pydantic Version Pin

**Decision**: Pin `pydantic>=2.10.0`.

**Rationale**: v2.10.0 (November 2024) is widely deployed, stable, and includes all needed v2 features (ConfigDict, field_serializer, model_copy, frozen). Conservative floor avoids early v2.x bugs. Latest stable is v2.12.5 (November 2025).

## Decision 9: TokenResponse Model

**Decision**: Create a separate `TokenResponse` model (not a classmethod on `TokenPair`) for parsing WHOOP API responses.

**Rationale**: `TokenResponse` has `expires_in: int` while `TokenPair` has `expires_at: float` — fundamentally different fields. A `to_token_pair()` method on `TokenResponse` handles the conversion with `time.monotonic() + self.expires_in`. This keeps each model's validation rules independent and makes the API response parsing a single `TokenResponse.model_validate(data)` call (FR-005).
