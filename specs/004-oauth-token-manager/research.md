# Research: WHOOP OAuth Token Manager

**Feature**: 004-oauth-token-manager | **Date**: 2026-03-02

## R1: Concurrent Refresh Protection

**Decision**: Use `asyncio.Lock` with a double-check pattern.

**Rationale**: When multiple coroutines call `get_valid_token()` concurrently with an expired token, only one should refresh. The double-check pattern (check expiry → acquire lock → re-check expiry → refresh if still expired) ensures exactly one refresh while letting subsequent waiters return the freshly-refreshed token immediately after acquiring the lock.

**Alternatives considered**:
- `asyncio.Event` — requires pairing with a Lock anyway; more complex for no gain.
- `asyncio.Condition` — more powerful than needed; `notify_all()` adds cognitive overhead without benefit.
- Lock + Event combo — slightly more efficient for hundreds of concurrent waiters, but overkill for single-digit concurrency in an MCP server.

## R2: httpx.AsyncClient Lifecycle

**Decision**: Dependency injection with optional internal fallback. Accept `httpx.AsyncClient` at init; create one internally if none provided. Track ownership via `_owns_client` flag to manage cleanup.

**Rationale**: Testable (inject mock client), composable (caller controls timeouts, connection limits), and the token manager stays focused on token logic. The httpx docs recommend reusing clients for connection pooling.

**Alternatives considered**:
- New client per request — kills connection pooling, new TLS handshake every time. Rejected.
- Long-lived internal client only — harder to test, couples token manager to httpx configuration. Rejected.

## R3: Exponential Backoff / Retry

**Decision**: Use `tenacity` for application-level retry on the token refresh call. Set `AsyncHTTPTransport(retries=1)` for basic connection resilience.

**Rationale**: httpx's built-in transport retry only handles `ConnectError`/`ConnectTimeout`, not HTTP status codes (429, 503). `tenacity` is the library recommended by httpx's own docs for application-level retry. It natively supports async/await and has a clean decorator API.

**Configuration**: 3 attempts, exponential backoff (1s, 2s, 4s), retry only on `httpx.TransportError` and 5xx `httpx.HTTPStatusError`. 4xx errors (invalid credentials, revoked tokens) fail immediately.

**Alternatives considered**:
- Manual retry loop — error-prone for edge cases (backoff calculation, exception filtering). Rejected for a core infrastructure component.
- `stamina` — opinionated tenacity wrapper with observability hooks. Overkill for this use case. Rejected.
- `httpx-retries` — transport-level retry with status code awareness. Less general than tenacity. Rejected.

**New dependency**: `tenacity` (well-maintained, 6,800+ GitHub stars, pure Python, no transitive dependencies).

## R4: Token Expiry Tracking

**Decision**: Use `time.monotonic()` for in-process expiry checks. Use `datetime.now(datetime.UTC)` only for persisted/logged absolute timestamps.

**Rationale**: `time.monotonic()` is immune to system clock adjustments (NTP, DST, manual changes). Token expiry is fundamentally "has N seconds elapsed?" — exactly what monotonic time is designed for. This is the pattern used by `cachetools` and `redis-py`.

**Persistence caveat**: `time.monotonic()` values are meaningless across process restarts. When saving to TokenStore, convert to absolute UTC. On load, compute remaining seconds and convert back to monotonic-relative.

**Alternatives considered**:
- `datetime.datetime.utcnow()` — deprecated in Python 3.12, returns naive datetime. Rejected.
- `datetime.datetime.now(datetime.UTC)` — correct but susceptible to clock jumps for expiry checks. Used only for persistence.
- `time.time()` — susceptible to clock adjustments. Rejected.

## R5: TokenStore Interface Design

**Decision**: Use `typing.Protocol` with `@runtime_checkable`.

**Rationale**: Structural subtyping (duck typing with type safety). Any class implementing `save()` and `load()` is a valid TokenStore — no inheritance required. Third-party implementations don't need to import our base class. Type checkers (mypy, pyright) fully support Protocol. `@runtime_checkable` enables `isinstance()` validation at plugin registration time.

**Alternatives considered**:
- `abc.ABC` — requires explicit subclassing, creates coupling. Overkill for a 2-method interface with no shared logic. Rejected.
- Hybrid (Protocol as interface + ABC as convenience base) — useful if we add shared serialization logic later, but premature now. Deferred.

## R6: WHOOP Token Endpoint Behavior

**Decision**: Document known WHOOP token endpoint behaviors that impact implementation.

**Findings**:

| Behavior | Detail |
|----------|--------|
| Token endpoint URL | `https://api.prod.whoop.com/oauth/oauth2/token` |
| Content type | `application/x-www-form-urlencoded` |
| Credential placement | POST body (not Basic Auth) |
| Access token TTL | 3600 seconds (1 hour), reported via `expires_in` |
| Refresh token rotation | Old refresh token invalidated on each refresh |
| Required scope for refresh | `offline` must be included to receive new refresh token |
| Concurrent refresh behavior | First request succeeds; second fails (stale refresh token) |
| Error on invalid refresh token | HTTP 400 or 401 (treat as non-retryable AuthenticationError) |
| Error on server issues | HTTP 5xx (treat as retryable TransientError) |

**Source**: WHOOP Developer Docs, confirmed via earlier OAuth research.

## R7: New Dependencies

**Decision**: Add `tenacity` as a runtime dependency.

| Dependency | Purpose | License | Maintenance |
|------------|---------|---------|-------------|
| `tenacity` | Retry with exponential backoff | Apache 2.0 | Active (6,800+ stars, maintained by Julien Danjou) |

No other new dependencies required. `asyncio.Lock`, `time.monotonic()`, `typing.Protocol`, and `datetime` are all stdlib.
