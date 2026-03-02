# Research: WHOOP API Setup Guide

**Feature**: 003-api-setup-guide | **Date**: 2026-03-02

## R1: WHOOP OAuth2 Flow Details

**Decision**: Document the standard OAuth2 Authorization Code flow with WHOOP-specific deviations.

**Rationale**: The WHOOP API uses OAuth2 Authorization Code flow but with several non-obvious configuration requirements that deviate from typical OAuth2 defaults. These deviations are the primary source of developer friction.

**Findings**:

| Parameter | Value | Source |
|-----------|-------|--------|
| Authorization URL | `https://api.prod.whoop.com/oauth/oauth2/auth` | WHOOP Developer Docs |
| Token Endpoint | `https://api.prod.whoop.com/oauth/oauth2/token` | WHOOP Developer Docs |
| API Base URL | `https://api.prod.whoop.com/developer` | OpenAPI spec in repo |
| Token Expiry | 3600 seconds (1 hour) | WHOOP Developer Docs |
| Token Type | `bearer` | WHOOP Developer Docs |

**Alternatives considered**: None — must use WHOOP's endpoints as documented.

## R2: State Parameter Minimum Length

**Decision**: Document the state parameter minimum as **8 characters** (per official docs), while recommending longer values for security.

**Rationale**: The official WHOOP developer documentation states "Minimum length is 8 characters if manually generated." The original user report said "Should be longer than 8 characters" — this likely reflects that values of exactly 8 characters were rejected in practice, but the official documentation states 8 as the minimum. The guide should state the official minimum (8) and recommend using longer values (16+ characters) as a security best practice.

**Spec update needed**: The Assumptions section currently states ">8 (9+)". This should be corrected to "minimum 8 characters per official documentation" with a recommendation for longer values.

**Alternatives considered**: Using the user-reported ">8" threshold — rejected because it contradicts official documentation.

## R3: Client Credentials Placement

**Decision**: Document that `client_id` and `client_secret` must be sent as POST body parameters in the token exchange request.

**Rationale**: Many OAuth2 libraries default to Basic Authentication (base64-encoded `client_id:client_secret` in the `Authorization` header). The WHOOP token endpoint expects credentials in the request body instead. This is a common source of token exchange failures.

**Alternatives considered**: Basic Auth header — does not work with WHOOP's token endpoint.

## R4: Token Refresh Flow

**Decision**: Document the refresh token flow including the `offline` scope requirement.

**Rationale**: To receive a refresh token, the initial authorization request must include the `offline` scope. Key behavior: existing access tokens are invalidated once the refresh token is used, and the refresh response contains a new refresh token that replaces the old one.

**Key details for the guide**:
- Must request `offline` scope during initial authorization to receive a refresh token
- Refresh request body: `grant_type=refresh_token`, `refresh_token`, `client_id`, `client_secret`, `scope=offline`
- Old access token invalidated after refresh
- New refresh token issued with each refresh (old one invalidated)

**Alternatives considered**: None — this is the only supported refresh mechanism.

## R5: Available Scopes

**Decision**: Document all available scopes with their data access descriptions.

**Rationale**: Developers need to know which scopes to request for which data endpoints.

**Findings**:

| Scope | Data Access |
|-------|-------------|
| `read:recovery` | Recovery data (score, HRV, resting heart rate) |
| `read:cycles` | Cycle data (strain, average heart rate) |
| `read:workout` | Workout data (strain, heart rate) |
| `read:sleep` | Sleep data (performance %, duration per stage) |
| `read:profile` | Profile data (name, email) |
| `read:body_measurement` | Body measurements (height, weight, max HR) |
| `offline` | Required to receive a refresh token |

## R6: Date Format Requirements

**Decision**: Document that date-filtered endpoints require full ISO 8601 format with time and timezone.

**Rationale**: The WHOOP API rejects date-only formats like `2026-01-01`. The required format is `2026-01-01T00:00:00.000Z` (full ISO 8601 with milliseconds and Z timezone designator).

**Usage**: Applied to `start` and `end` query parameters on paginated list endpoints (cycles, recovery, sleep, workouts).

**Alternatives considered**: Date-only (`YYYY-MM-DD`) — rejected by the API.

## R7: Pagination Mechanism

**Decision**: Document cursor-based pagination with `nextToken` and clarify the placeholder issue.

**Rationale**: The WHOOP API OpenAPI documentation shows `nextToken=string` as a query parameter, which developers may include literally. The `nextToken` should be omitted from initial requests and only populated with actual cursor values returned in API responses.

**Key details**:
- `limit`: Maximum results per request (default: 10, max: 25)
- `start`: Filter after this date-time (inclusive), full ISO 8601
- `end`: Filter before this date-time (exclusive), full ISO 8601
- `nextToken`: Cursor from previous response; omit on first request

## R8: Guide Placement in Repository

**Decision**: Place the guide at `docs/api-setup-guide.md`.

**Rationale**: The `docs/` directory already exists with `data-model.md` from feature 002. Placing the guide here keeps documentation co-located and discoverable. A link from `README.md` will improve discoverability.

**Alternatives considered**:
- In-README section — rejected because the guide is substantial (~200-400 lines) and would bloat the README
- Wiki — rejected because it's less discoverable and not version-controlled with the code
