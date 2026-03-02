# Feature Specification: WHOOP OAuth Token Manager

**Feature Branch**: `004-oauth-token-manager`
**Created**: 2026-03-02
**Status**: Draft
**Input**: User description: "WHOOP OAuth Token Manager — Build an httpx-based client that exchanges authorization codes for tokens, auto-refreshes on 401 or before expiry, handles refresh token rotation with locking to prevent concurrent refresh races, and sends client credentials in the POST body (not Basic Auth). In scope: Token exchange, refresh with rotation, async mutex for concurrent refresh safety, token expiry tracking, secure credential handling. Expose a simple get_valid_token() interface that the API client can call. Out of scope: Initiating the OAuth browser flow, persistent token storage backends, MCP-specific auth concerns."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Exchange Authorization Code for Tokens (Priority: P1)

A developer (or upstream system) has obtained a WHOOP authorization code through the browser-based OAuth consent flow. They pass this code to the token manager, which exchanges it for an access token and refresh token by calling WHOOP's token endpoint. The developer receives confirmation that tokens are available and can immediately begin making API calls.

**Why this priority**: Without the initial token exchange, no WHOOP API calls are possible. This is the foundational capability everything else depends on.

**Independent Test**: Can be fully tested by providing a valid authorization code (or mocking WHOOP's token endpoint) and verifying that the manager stores both access and refresh tokens with correct expiry tracking.

**Acceptance Scenarios**:

1. **Given** a valid authorization code, redirect URI, client ID, and client secret, **When** the token exchange is requested, **Then** the manager calls WHOOP's token endpoint with credentials in the POST body (not Basic Auth header) and stores the returned access token, refresh token, and expiry timestamp.
2. **Given** an invalid or expired authorization code, **When** the token exchange is requested, **Then** the manager raises a clear error indicating the code was rejected, without storing any partial token state.
3. **Given** a valid authorization code, **When** the token exchange is requested, **Then** the client credentials (client_id and client_secret) are sent as POST body parameters, never as a Basic Auth header.

---

### User Story 2 - Get a Valid Token for API Calls (Priority: P1)

A WHOOP API client (the next layer up) needs a valid access token to make an API request. It calls `get_valid_token()` on the token manager. If the current token is still valid, it is returned immediately. If it has expired or is about to expire, the manager transparently refreshes it before returning the new token. The caller never needs to know whether a refresh happened.

**Why this priority**: This is the primary interface other components will use. The entire value of the token manager is providing a single call that always returns a usable token.

**Independent Test**: Can be tested by initializing the manager with tokens at various expiry states (valid, about to expire, expired) and verifying `get_valid_token()` returns a working token in every case.

**Acceptance Scenarios**:

1. **Given** a stored access token that has not expired and is not within the refresh buffer window, **When** `get_valid_token()` is called, **Then** the current access token is returned without any network call.
2. **Given** a stored access token that is within the proactive refresh buffer (less than 5 minutes before expiry), **When** `get_valid_token()` is called, **Then** the manager refreshes the token first, stores the new tokens, and returns the new access token.
3. **Given** a stored access token that has already expired, **When** `get_valid_token()` is called, **Then** the manager uses the refresh token to obtain a new access token and returns it.

---

### User Story 3 - Handle Refresh Token Rotation Safely (Priority: P1)

When the token manager refreshes an access token, WHOOP invalidates both the old access token and the old refresh token, returning new ones. The manager must atomically update both tokens so that no concurrent caller uses a stale refresh token. If two callers trigger a refresh simultaneously, only one refresh request is sent; the other waits and receives the same result.

**Why this priority**: WHOOP's refresh token rotation with invalidation means a single failed concurrent refresh can permanently lock out the user (both tokens become invalid). This is a correctness requirement, not an optimization.

**Independent Test**: Can be tested by simulating concurrent `get_valid_token()` calls with an expired token and verifying that exactly one refresh request is made to WHOOP's token endpoint, and both callers receive the same new access token.

**Acceptance Scenarios**:

1. **Given** an expired access token, **When** two concurrent callers invoke `get_valid_token()` at the same time, **Then** only one refresh request is sent to WHOOP, and both callers receive the new access token.
2. **Given** a successful refresh response, **When** new tokens are received, **Then** both the access token and refresh token are updated atomically — no intermediate state where the old refresh token is still stored with the new access token.
3. **Given** a refresh request that fails (e.g., network error, revoked refresh token), **When** the failure occurs, **Then** the manager raises a clear error indicating re-authentication is required, and does not corrupt the stored token state.

---

### User Story 4 - Initialize from Pre-Existing Tokens (Priority: P2)

A developer or upstream system already has a valid access token and refresh token (obtained previously, or passed via environment variables for local development). They initialize the token manager with these tokens directly, skipping the authorization code exchange. The manager tracks their expiry and handles subsequent refreshes normally.

**Why this priority**: Enables testing and local development workflows where tokens are obtained out-of-band (e.g., from Postman or a helper script). Also supports the scenario where an upstream system passes tokens to the manager at startup.

**Independent Test**: Can be tested by initializing the manager with known tokens and an expiry timestamp, then verifying `get_valid_token()` returns the provided token without any network calls until expiry.

**Acceptance Scenarios**:

1. **Given** a valid access token, refresh token, and expiry timestamp, **When** the manager is initialized with these values, **Then** it accepts them and `get_valid_token()` returns the access token without calling WHOOP.
2. **Given** a pre-existing access token that is already expired, **When** the manager is initialized and `get_valid_token()` is called, **Then** the manager uses the provided refresh token to obtain a new access token.

---

### Edge Cases

- What happens when the refresh token itself has been revoked by the user (e.g., via WHOOP's dashboard)? The manager should raise a specific "re-authentication required" error, not a generic network error.
- What happens when WHOOP's token endpoint is temporarily unreachable during a refresh? The manager should retry with backoff (up to a bounded number of attempts) and raise an error if all retries fail, without corrupting token state.
- What happens when the system clock is significantly skewed, making expiry calculations unreliable? The manager should treat unexpected 401 responses as a signal to refresh, regardless of the local expiry calculation.
- What happens when the manager has no tokens at all (neither from initialization nor from a code exchange)? Calling `get_valid_token()` should raise a clear "not authenticated" error.
- What happens when a refresh response returns a valid access token but omits the refresh token? The manager should raise an error (WHOOP's contract guarantees both are returned when `offline` scope is used).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST exchange an authorization code for an access token and refresh token by calling WHOOP's token endpoint at `https://api.prod.whoop.com/oauth/oauth2/token`.
- **FR-002**: System MUST send client credentials (`client_id` and `client_secret`) as POST body parameters in `application/x-www-form-urlencoded` format, never as a Basic Auth header.
- **FR-003**: System MUST store the access token, refresh token, and token expiry timestamp in memory after a successful token exchange or refresh.
- **FR-004**: System MUST expose a `get_valid_token()` method that returns a currently-valid access token, refreshing transparently if needed.
- **FR-005**: System MUST proactively refresh the access token when it is within a configurable buffer period before expiry (default: 5 minutes), rather than waiting for it to expire.
- **FR-006**: System MUST use an async mutex (or equivalent locking mechanism) to ensure only one refresh request is in-flight at a time, with concurrent callers waiting for the result.
- **FR-007**: System MUST update both the access token and refresh token atomically after a successful refresh, since WHOOP invalidates the old refresh token on each refresh (token rotation).
- **FR-008**: System MUST accept pre-existing tokens (access token, refresh token, expiry) for initialization, supporting scenarios where tokens are obtained out-of-band.
- **FR-009**: System MUST raise a distinct "re-authentication required" error when a refresh fails due to an invalid or revoked refresh token, distinguishing this from transient network errors.
- **FR-010**: System MUST use an async HTTP client for all communication with WHOOP's token endpoint.
- **FR-011**: System MUST include the `offline` scope in refresh requests to ensure a new refresh token is returned.

### Key Entities

- **TokenPair**: Represents the current authentication state — access token, refresh token, and the timestamp at which the access token expires. This is the core data the manager holds in memory.
- **TokenExchangeRequest**: The parameters needed to exchange an authorization code — authorization code, redirect URI, client ID, client secret.
- **TokenRefreshRequest**: The parameters needed to refresh — refresh token, client ID, client secret, scope.
- **AuthenticationError**: Represents a permanent authentication failure (revoked tokens, invalid credentials) that requires the user to re-authenticate through the browser flow.
- **TransientError**: Represents a temporary failure (network timeout, server error) that may succeed on retry.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Callers obtain a valid access token via `get_valid_token()` in under 50 milliseconds when no refresh is needed (in-memory lookup only).
- **SC-002**: Under concurrent load (10+ simultaneous `get_valid_token()` calls with an expired token), exactly one refresh request is sent — no duplicate refreshes occur.
- **SC-003**: After a successful refresh, the old access token and old refresh token are never used in subsequent requests — token rotation is handled correctly 100% of the time.
- **SC-004**: When WHOOP's token endpoint is unreachable, the system fails gracefully within a bounded time (no indefinite hangs) and provides a clear, actionable error to the caller.
- **SC-005**: All test scenarios (token exchange, refresh, concurrent refresh, error cases) pass with mocked responses — no real WHOOP account required for automated testing.
- **SC-006**: A developer can initialize the token manager and retrieve a valid token in under 5 lines of calling code.

## Assumptions

- WHOOP's token endpoint uses `application/x-www-form-urlencoded` POST body for credentials (not Basic Auth). This is documented in WHOOP's developer docs and confirmed through research.
- Access tokens expire in 3600 seconds (1 hour) as currently documented. The manager uses the `expires_in` value from the response rather than hardcoding this.
- WHOOP always returns a new refresh token alongside a new access token when the `offline` scope is included. If this changes, the manager will detect and surface the error.
- The proactive refresh buffer defaults to 5 minutes before expiry, balancing between avoiding expired-token API failures and minimizing unnecessary refreshes.
- Token storage is in-memory only for this feature. Persistent storage (surviving process restarts) is a separate feature concern for the deployment layer.
- The async mutex assumes a single-process deployment. Multi-process or distributed locking is a deployment-layer concern.
