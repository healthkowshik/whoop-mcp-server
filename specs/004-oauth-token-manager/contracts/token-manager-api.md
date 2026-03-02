# Contract: Token Manager Public API

**Feature**: 004-oauth-token-manager | **Date**: 2026-03-02

This is a Python library consumed by other modules in the whoop-mcp-server project. The public API surface is:

## TokenManager

### Constructor

```
TokenManager(
    credentials: WhoopCredentials,
    store: TokenStore | None = None,     # Default: MemoryTokenStore
    client: httpx.AsyncClient | None = None,  # Default: internally managed
    refresh_buffer_seconds: int = 300,   # Default: 5 minutes
)
```

**Behavior on init**:
- If pre-existing tokens passed explicitly (via `from_tokens()` classmethod), use those immediately.
- If `store` is provided (but no pre-existing tokens), the store is **not** loaded eagerly — the constructor is synchronous. Instead, `store.load()` is called lazily on the first `get_valid_token()` invocation (guarded by an internal `_store_loaded` flag so it runs at most once).
- If neither tokens nor store are provided, the manager starts in an unauthenticated state.

### Primary Interface

#### `get_valid_token() -> str`

Returns a valid access token. Refreshes transparently if expired or expiring soon.

| Scenario | Behavior |
|----------|----------|
| Token is valid | Return immediately (no network call) |
| Token is within refresh buffer | Refresh, then return new token |
| Token is expired | Refresh, then return new token |
| No tokens loaded | Raise `AuthenticationError` |
| Refresh fails (revoked) | Raise `AuthenticationError` |
| Refresh fails (transient, after 3 retries) | Raise `TransientError` |

#### `exchange_code(code: str, redirect_uri: str) -> None`

Exchange an authorization code for tokens. Stores the result via TokenStore.

| Scenario | Behavior |
|----------|----------|
| Valid code | Stores TokenPair, calls `store.save()` |
| Invalid code (4xx) | Raises `AuthenticationError`, no state change |
| Network error (after 3 retries) | Raises `TransientError`, no state change |

### Factory

#### `TokenManager.from_tokens(credentials, access_token, refresh_token, expires_in, **kwargs) -> TokenManager`

Create a manager pre-loaded with existing tokens. Convenience for testing and env-var initialization.

### Lifecycle

#### `aclose() -> None`

Close the internally-managed httpx client (if the manager created it). No-op if the client was injected.

## TokenStore Protocol

```
class TokenStore(Protocol):
    async def save(self, data: dict) -> None: ...
    async def load(self) -> dict | None: ...
```

## Error Types

### AuthenticationError(Exception)

- Permanent failure. Caller must re-authenticate via browser flow.
- `.message: str` — human-readable, no secrets.
- `.status_code: int | None` — HTTP status if available.

### TransientError(Exception)

- Temporary failure. May succeed if retried later.
- `.message: str` — human-readable, no secrets.
- `.status_code: int | None` — HTTP status if available.
- `.attempts: int` — number of retry attempts made.

## Security Contract

- `WhoopCredentials.__repr__` returns `WhoopCredentials(client_id='...', client_secret='***')` — secret is always masked.
- `TokenPair.__repr__` returns masked token values (e.g., `access_token='eyJ...***'`).
- `AuthenticationError` and `TransientError` message fields never contain token values or client_secret.
