# Data Model: WHOOP OAuth Token Manager

**Feature**: 004-oauth-token-manager | **Date**: 2026-03-02

## Entities

### TokenPair

Core data representing the current authentication state.

| Field | Type | Description |
|-------|------|-------------|
| access_token | string | Bearer token for WHOOP API requests |
| refresh_token | string | Token used to obtain a new access token |
| expires_at | float (monotonic) | `time.monotonic()` timestamp after which the access token is expired |
| scope | string | Space-delimited scope string from the token response |
| token_type | string | Always `"bearer"` for WHOOP |

**Validation rules**:
- `access_token` and `refresh_token` must be non-empty strings.
- `expires_at` must be a positive float.
- `scope` must contain `"offline"` for refresh to be possible.

**State transitions**:

```
[No Tokens] ──exchange_code()──► [Has Tokens (valid)]
[No Tokens] ──load_from_store()──► [Has Tokens (valid or expired)]
[Has Tokens (valid)] ──time passes──► [Has Tokens (expiring soon)]
[Has Tokens (expiring soon)] ──get_valid_token()──► [Has Tokens (refreshed)]
[Has Tokens (expired)] ──get_valid_token()──► [Has Tokens (refreshed)]
[Has Tokens (any)] ──refresh fails (revoked)──► [Auth Error (no tokens)]
[Has Tokens (any)] ──refresh fails (transient)──► [Has Tokens (unchanged, error raised)]
```

### TokenStore (Protocol)

Interface for pluggable token persistence.

| Method | Signature | Description |
|--------|-----------|-------------|
| save | `async def save(self, data: dict) -> None` | Persist token data. Called after every successful exchange or refresh. |
| load | `async def load(self) -> dict | None` | Load previously persisted token data. Returns `None` if no tokens stored. |

**Serialization format** (dict passed to save/load):

| Key | Type | Description |
|-----|------|-------------|
| access_token | string | The access token |
| refresh_token | string | The refresh token |
| expires_at_utc | string (ISO 8601) | Absolute UTC expiry timestamp for cross-process portability |
| scope | string | Scope string |
| token_type | string | Token type |

Note: The in-memory `expires_at` (monotonic) is converted to absolute UTC for persistence. On load, the remaining seconds are computed and converted back to monotonic-relative.

### MemoryTokenStore (Default Implementation)

In-memory implementation of TokenStore. Tokens are lost on process restart.

| Field | Type | Description |
|-------|------|-------------|
| _data | dict or None | Stored token data, or None if empty |

### WhoopCredentials

Client credentials for WHOOP OAuth. Passed to the token manager at initialization.

| Field | Type | Description |
|-------|------|-------------|
| client_id | string | WHOOP App Client ID |
| client_secret | string | WHOOP App Client Secret |

**Security**: `client_secret` must never appear in `__repr__`, `__str__`, error messages, or logs.

### AuthenticationError

Permanent failure requiring re-authentication.

| Field | Type | Description |
|-------|------|-------------|
| message | string | Human-readable description (no secrets) |
| status_code | int or None | HTTP status code from WHOOP, if applicable |

### TransientError

Temporary failure that may succeed on retry.

| Field | Type | Description |
|-------|------|-------------|
| message | string | Human-readable description (no secrets) |
| status_code | int or None | HTTP status code from WHOOP, if applicable |
| attempts | int | Number of retry attempts made before raising |

## Relationships

```
TokenManager
├── has one ─── WhoopCredentials (immutable, set at init)
├── has one ─── TokenPair (mutable, updated on exchange/refresh)
├── has one ─── TokenStore (pluggable, called on every token change)
├── has one ─── asyncio.Lock (protects concurrent refresh)
└── has one ─── httpx.AsyncClient (injected or internally managed)
```
