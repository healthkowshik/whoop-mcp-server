# Data Model: Pydantic Validation for Auth Models

**Feature**: 005-pydantic-validation
**Date**: 2026-03-03

## Entities

### WhoopCredentials

OAuth client credentials. Immutable (frozen). Secret values masked in all string output.

| Field           | Type  | Constraints       | Notes                              |
|-----------------|-------|-------------------|------------------------------------|
| `client_id`     | `str` | min_length=1      | WHOOP OAuth client identifier      |
| `client_secret` | `str` | min_length=1      | WHOOP OAuth client secret (masked) |

**Config**: `frozen=True`, `extra='ignore'`

**Validation**:
- Both fields reject empty strings via `Field(min_length=1)`
- No type coercion needed (both are always strings)

**Repr**: `WhoopCredentials(client_id='my-id', client_secret='***')`
- `client_secret` is always fully masked in `__repr__` and `__str__`
- `client_id` is shown in full

**Equality**: Field-by-field comparison (default Pydantic behavior). `client_secret` participates in equality as a plain string.

---

### TokenPair

Current authentication state. Immutable (frozen). Token values masked in string output.

| Field           | Type    | Constraints              | Notes                                       |
|-----------------|---------|--------------------------|---------------------------------------------|
| `access_token`  | `str`   | min_length=1             | Bearer token for WHOOP API requests         |
| `refresh_token` | `str`   | min_length=1             | Token for obtaining a new access token      |
| `expires_at`    | `float` | gt=0 (strictly positive) | `time.monotonic()` timestamp of expiry      |
| `scope`         | `str`   | (no constraint)          | Space-delimited scope string                |
| `token_type`    | `str`   | (no constraint)          | Always "bearer" for WHOOP                   |

**Config**: `frozen=True`, `extra='ignore'`

**Validation**:
- `access_token`, `refresh_token`: Reject empty strings via `Field(min_length=1)`
- `expires_at`: Must be > 0 via `Field(gt=0)`
- `scope`, `token_type`: Accept any string (including empty)

**Repr**: `TokenPair(access_token='eyJhbG***', refresh_token='dGhpcy***', expires_at=123456.78, scope='offline', token_type='bearer')`
- `access_token` and `refresh_token` masked via `_mask()` (first 6 chars + `***`)
- All other fields shown in full

**Methods**:

| Method                            | Signature                                    | Description                                                                                   |
|-----------------------------------|----------------------------------------------|-----------------------------------------------------------------------------------------------|
| `is_expired`                      | `(buffer_seconds: float = 0) -> bool`        | Returns `True` if `time.monotonic() >= (self.expires_at - buffer_seconds)`                    |
| `to_store_dict`                   | `() -> dict`                                 | Serializes to store format: monotonic `expires_at` → ISO 8601 UTC `expires_at_utc`           |
| `from_store_dict` *(classmethod)* | `(data: dict) -> TokenPair`                  | Deserializes from store dict: ISO 8601 UTC `expires_at_utc` → monotonic `expires_at`         |

**Store dict format** (output of `to_store_dict()`):
```json
{
  "access_token": "eyJhbG...",
  "refresh_token": "dGhpcy...",
  "expires_at_utc": "2026-03-03T12:00:00+00:00",
  "scope": "offline read:recovery",
  "token_type": "bearer"
}
```

---

### TokenResponse (NEW)

Intermediate representation of a WHOOP token endpoint response. Validates the raw API response and converts to a `TokenPair`.

| Field           | Type  | Constraints  | Default    | Notes                                            |
|-----------------|-------|--------------|------------|--------------------------------------------------|
| `access_token`  | `str` | min_length=1 | (required) | Bearer token from WHOOP                          |
| `refresh_token` | `str` | min_length=1 | (required) | Refresh token from WHOOP                         |
| `expires_in`    | `int` | gt=0         | (required) | Seconds until access token expires               |
| `scope`         | `str` | (none)       | `""`       | Space-delimited scope string (may be absent)     |
| `token_type`    | `str` | (none)       | `"bearer"` | Token type (always "bearer" for WHOOP)           |

**Config**: `extra='ignore'` (forward compatibility with new API response fields)

**Validation**:
- `expires_in`: Pydantic's default lax mode coerces `"3600"` (string) to `3600` (int). Must be > 0.
- `access_token`, `refresh_token`: Reject empty strings.

**Methods**:

| Method         | Signature             | Description                                                            |
|----------------|-----------------------|------------------------------------------------------------------------|
| `to_token_pair` | `() -> TokenPair`    | Creates a `TokenPair` with `expires_at = time.monotonic() + expires_in` |

---

## Relationships

```
WhoopCredentials ─── used by ──→ TokenManager
TokenResponse ─── to_token_pair() ──→ TokenPair
TokenPair ─── to_store_dict() ──→ dict (store format)
dict (store format) ─── TokenPair.from_store_dict() ──→ TokenPair
dict (API response) ─── TokenResponse.model_validate() ──→ TokenResponse
```

## Type Alias

```python
NonEmptyStr = Annotated[str, Field(min_length=1)]
```

Used for `client_id`, `client_secret`, `access_token`, `refresh_token` across all models to reduce repetition.
