# Data Model: WHOOP API Setup Guide

**Feature**: 003-api-setup-guide | **Date**: 2026-03-02

This feature is a documentation artifact (Markdown file), not a code feature. The "data model" here describes the guide's content structure and the domain entities it documents.

## Guide Content Structure

The guide (`docs/api-setup-guide.md`) follows this section hierarchy:

```
1. Quick Reference (table of all pitfalls — FR-009)
2. Prerequisites
   - WHOOP Developer Portal registration
   - Client ID and Client Secret
   - Redirect URI (localhost for local testing — no server needed)
   - Shell variable setup (CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
3. OAuth2 Authorization Flow
   3.1 Authorization Request (authorization URL, state, scopes, redirect URI)
   3.2 Token Exchange (token endpoint, client credentials in body)
   3.3 Token Refresh (offline scope, refresh token rotation)
4. Making API Requests
   4.1 Authentication Header (Bearer token in Authorization header)
   4.2 Date Formatting (full ISO 8601)
   4.3 Pagination (nextToken usage, omit placeholder)
5. Troubleshooting
   - Symptom → Cause → Fix format for each pitfall
```

## Domain Entities Documented

### OAuth2 Configuration

| Attribute | Example Value | Notes |
|-----------|---------------|-------|
| Authorization URL | `https://api.prod.whoop.com/oauth/oauth2/auth` | Fixed endpoint |
| Token Endpoint | `https://api.prod.whoop.com/oauth/oauth2/token` | Fixed endpoint |
| Client ID | `$CLIENT_ID` | From Developer Portal; set as shell variable |
| Client Secret | `$CLIENT_SECRET` | From Developer Portal; set as shell variable |
| Redirect URI | `http://localhost:8080/callback` | Must match portal registration; for local testing no server needed — copy `code` from browser address bar |
| State | `whoop-csrf-random-abc123` | Minimum 8 chars; recommend 16+ |
| Scopes | `read:cycles read:recovery offline` | Space-separated; `offline` required for refresh |

### Token Response

| Field | Type | Description |
|-------|------|-------------|
| access_token | string | Bearer token for API requests |
| refresh_token | string | Used to obtain new access token (only if `offline` scope requested) |
| expires_in | integer | Token lifetime in seconds (3600 = 1 hour) |
| scope | string | Granted scopes |
| token_type | string | Always `bearer` |

### API Request Parameters (Paginated Endpoints)

| Parameter | Format | Required | Notes |
|-----------|--------|----------|-------|
| start | `YYYY-MM-DDTHH:MM:SS.000Z` | No | Inclusive; full ISO 8601 |
| end | `YYYY-MM-DDTHH:MM:SS.000Z` | No | Exclusive; full ISO 8601 |
| limit | integer (1-25) | No | Default: 10 |
| nextToken | string | No | Omit on first request; use value from previous response |

### Pitfall Reference

| # | Pitfall | Symptom | Cause | Fix |
|---|---------|---------|-------|-----|
| 1 | Auth in headers | 401 Unauthorized | Token sent as query param or missing | Use `Authorization: Bearer <token>` header |
| 2 | Bearer token format | 401 Unauthorized | Token not prefixed with "Bearer " | Include `Bearer ` prefix in header value |
| 3 | State parameter length | Authorization fails | State < 8 characters | Use 8+ characters (recommend 16+) |
| 4 | Client credentials in body | Token exchange fails | Credentials sent as Basic Auth header | Send `client_id` and `client_secret` as POST body params |
| 5 | Placeholder parameter | 400 Bad Request | `nextToken=string` sent literally | Omit `nextToken` from first request |
| 6 | Date format | 400 Bad Request | Date-only format like `2026-01-01` | Use `2026-01-01T00:00:00.000Z` |
| 7 | Token refresh | 401 after ~1 hour | Access token expired | Use refresh token with `offline` scope |

## Relationships

- OAuth2 Configuration → produces → Token Response
- Token Response (access_token) → used in → API Request (Authorization header)
- Token Response (refresh_token) → used in → Token Refresh Request → produces → new Token Response
- API Response (nextToken) → used in → next API Request (nextToken parameter)
