# WHOOP API Setup Guide

This guide walks you through configuring OAuth2 authentication, making your first API requests, and avoiding the most common integration pitfalls with the WHOOP Developer API. Each section includes curl examples you can run directly from your terminal.

## Quick Reference

| # | Pitfall | Symptom | Fix |
|---|---------|---------|-----|
| 1 | Token not in Authorization header | 401 Unauthorized | Send token via `Authorization: Bearer <token>` header |
| 2 | Missing "Bearer " prefix | 401 Unauthorized | Include the `Bearer ` prefix before the token value |
| 3 | State parameter too short | Authorization fails | Use 8+ characters (recommend 16+) |
| 4 | Credentials in Basic Auth header | Token exchange fails | Send `client_id` and `client_secret` as POST body parameters |
| 5 | Literal `nextToken=string` | 400 Bad Request | Omit `nextToken` on the first request; use the value from the previous response |
| 6 | Date-only format | 400 Bad Request | Use full ISO 8601: `2026-01-01T00:00:00.000Z` |
| 7 | Expired access token | 401 after ~1 hour | Refresh the token using your refresh token with the `offline` scope |

## Prerequisites

1. **Register on the WHOOP Developer Portal** — Create an account at the [WHOOP Developer Dashboard](https://developer-dashboard.whoop.com/) and create a new application.

2. **Obtain your Client ID and Client Secret** — After creating your application, the portal displays your `Client ID` and `Client Secret`. Copy both values; you will need them for every token request.

3. **Configure a Redirect URI** — In your application settings on the Developer Dashboard, add a Redirect URI **before** running any authorization requests. The value you register must exactly match the `redirect_uri` you send — including scheme, port, and path.

   **For local testing**, add `http://localhost:8080/callback` in the portal. You do not need a server running on that port. After you authorize, the browser will redirect to that URL with a `code` query parameter in the address bar — just copy the code value. The page itself will show a "connection refused" error, which you can ignore.

> **Security warning:** Never commit your Client Secret to source control, log it to stdout, or include it in client-side code. Treat it like a password.

4. **Set your shell variables** — Paste the following into your terminal and fill in your values. Every curl example in this guide references these variables, so you only need to set them once per session:

```bash
export CLIENT_ID="your-client-id"
export CLIENT_SECRET="your-client-secret"
export REDIRECT_URI="http://localhost:8080/callback"
```

You will set additional variables (`AUTH_CODE`, `ACCESS_TOKEN`, `REFRESH_TOKEN`) as you progress through the OAuth2 flow below.

## OAuth2 Authorization Flow

### Authorization Request

Direct the user's browser to the WHOOP authorization endpoint:

```
https://api.prod.whoop.com/oauth/oauth2/auth
```

**Required query parameters:**

| Parameter | Value | Description |
|-----------|-------|-------------|
| `response_type` | `code` | Must be `code` for the Authorization Code flow |
| `client_id` | `$CLIENT_ID` | Your application's Client ID |
| `redirect_uri` | `$REDIRECT_URI` | Must exactly match your portal configuration |
| `scope` | `read:cycles read:recovery offline` | Space-separated list of requested scopes |
| `state` | *(auto-generated)* | CSRF protection token (minimum 8 characters; recommend 16+) |

**Available scopes:**

| Scope | Data Access |
|-------|-------------|
| `read:recovery` | Recovery data (score, HRV, resting heart rate) |
| `read:cycles` | Cycle data (strain, average heart rate) |
| `read:workout` | Workout data (strain, heart rate) |
| `read:sleep` | Sleep data (performance %, duration per stage) |
| `read:profile` | Profile data (name, email) |
| `read:body_measurement` | Body measurements (height, weight, max HR) |
| `offline` | Required to receive a refresh token |

> **Note:** Include the `offline` scope if you want a refresh token for long-lived access. Without it, you will only receive an access token that expires after 1 hour with no way to renew it.

**Example — open the authorization URL in your browser:**

```bash
STATE="whoop-csrf-$(openssl rand -hex 12)"

open "https://api.prod.whoop.com/oauth/oauth2/auth?\
response_type=code&\
client_id=$CLIENT_ID&\
redirect_uri=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$REDIRECT_URI', safe=''))")&\
scope=read%3Arecovery%20read%3Acycles%20read%3Aworkout%20read%3Asleep%20read%3Aprofile%20read%3Abody_measurement%20offline&\
state=$STATE"
```

This opens your browser to the WHOOP login page. After you log in and authorize, the browser redirects to your redirect URI. The page will show a "connection refused" error — **this is expected**. Look at the address bar, which will contain:

```
http://localhost:8080/callback?code=XXXXXX&state=...&scope=...
```

Copy the `code` value and save it:

```bash
export AUTH_CODE="paste-the-code-value-here"
```

### Token Exchange

Exchange the authorization code for an access token by sending a POST request to the token endpoint:

```
https://api.prod.whoop.com/oauth/oauth2/token
```

> **Important:** Send `client_id` and `client_secret` as POST body parameters. Do **not** use Basic Authentication (the base64-encoded `Authorization` header). The WHOOP token endpoint does not accept Basic Auth — this is the most common cause of token exchange failures. See [Pitfall #4](#4-client-credentials-in-basic-auth-header).

**Required body parameters:**

| Parameter | Value |
|-----------|-------|
| `grant_type` | `authorization_code` |
| `code` | `$AUTH_CODE` |
| `redirect_uri` | `$REDIRECT_URI` |
| `client_id` | `$CLIENT_ID` |
| `client_secret` | `$CLIENT_SECRET` |

**Example — exchange code for tokens:**

```bash
curl -X POST "https://api.prod.whoop.com/oauth/oauth2/token" \
  -d "grant_type=authorization_code" \
  -d "code=$AUTH_CODE" \
  -d "redirect_uri=$REDIRECT_URI" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET"
```

**Expected response:**

```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "r1a2b3c4...",
  "expires_in": 3600,
  "scope": "read:cycles read:recovery offline",
  "token_type": "bearer"
}
```

Save the tokens from the response:

```bash
export ACCESS_TOKEN="eyJhbGci..."
export REFRESH_TOKEN="r1a2b3c4..."
```

The `access_token` expires after 3600 seconds (1 hour). If you requested the `offline` scope, the response also includes a `refresh_token` you can use to obtain new tokens without re-authorizing.

### Token Refresh

Access tokens expire after 1 hour (3600 seconds). If you requested the `offline` scope during authorization, you can use your refresh token to obtain a new access token without requiring the user to re-authorize.

> **Critical:** When you use a refresh token, both the old access token **and** the old refresh token are invalidated. The response contains a new refresh token — always store it, because the previous one will no longer work.

**Refresh request body parameters:**

| Parameter | Value |
|-----------|-------|
| `grant_type` | `refresh_token` |
| `refresh_token` | `$REFRESH_TOKEN` |
| `client_id` | `$CLIENT_ID` |
| `client_secret` | `$CLIENT_SECRET` |
| `scope` | `offline` |

**Example — refresh an expired token:**

```bash
curl -X POST "https://api.prod.whoop.com/oauth/oauth2/token" \
  -d "grant_type=refresh_token" \
  -d "refresh_token=$REFRESH_TOKEN" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET" \
  -d "scope=offline"
```

The response format is identical to the token exchange response — it includes a new `access_token`, a new `refresh_token`, and `expires_in: 3600`. Update your variables with the new values:

```bash
export ACCESS_TOKEN="new-access-token-from-response"
export REFRESH_TOKEN="new-refresh-token-from-response"
```

## Making API Requests

### Authentication Header

All WHOOP API requests require a Bearer token in the HTTP `Authorization` header. Do **not** send the token as a query parameter.

**Required header format:**

```
Authorization: Bearer $ACCESS_TOKEN
```

**Example — fetch cycle data:**

```bash
curl "https://api.prod.whoop.com/developer/v2/cycle" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

If you receive a `401 Unauthorized` response, your access token is either expired or invalid. See [Token Refresh](#token-refresh) to obtain a new one.

### Date Formatting

The `start` and `end` query parameters on paginated endpoints (cycles, recovery, sleep, workouts) require **full ISO 8601 format** with time and timezone. The API rejects date-only strings.

**Valid format:**

```
2026-01-01T00:00:00.000Z
```

**Common mistakes:**

| Format | Example | Result |
|--------|---------|--------|
| Full ISO 8601 | `2026-01-01T00:00:00.000Z` | Accepted |
| Missing milliseconds | `2026-01-01T00:00:00Z` | May be accepted |
| Missing timezone | `2026-01-01T00:00:00` | Rejected |
| Date only | `2026-01-01` | Rejected |

> **Note:** `start` is inclusive and `end` is exclusive. A request with `start=2026-01-01T00:00:00.000Z` and `end=2026-01-02T00:00:00.000Z` returns data for January 1 only.

**Example — fetch cycles for a specific date range:**

```bash
curl -G "https://api.prod.whoop.com/developer/v2/cycle" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  --data-urlencode "start=2026-01-01T00:00:00.000Z" \
  --data-urlencode "end=2026-01-08T00:00:00.000Z"
```

### Pagination

WHOOP uses cursor-based pagination. The API documentation shows `nextToken=string` as a query parameter — this is a placeholder. Do **not** include `nextToken=string` literally in your requests.

**Pagination parameters:**

| Parameter | Description |
|-----------|-------------|
| `limit` | Results per page (1–25, default 10) |
| `nextToken` | Cursor from the previous response; **omit on the first request** |

**Example — first request (no nextToken):**

```bash
curl -G "https://api.prod.whoop.com/developer/v2/cycle" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  --data-urlencode "limit=25"
```

If more results are available, the response includes a `next_token` field:

```json
{
  "records": [...],
  "next_token": "abc123xyz"
}
```

**Example — subsequent request using the cursor:**

```bash
curl -G "https://api.prod.whoop.com/developer/v2/cycle" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  --data-urlencode "limit=25" \
  --data-urlencode "nextToken=abc123xyz"
```

**Detecting the last page:** When the response does not include a `next_token` field (or it is `null`), you have reached the last page of results.

## Troubleshooting

### 1. Token not in Authorization header

**Symptom:** `401 Unauthorized` on every API request.

**Cause:** The access token is being sent as a query parameter or is missing entirely.

**Fix:** Send the token in the HTTP `Authorization` header:

```bash
curl "https://api.prod.whoop.com/developer/v2/cycle" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 2. Missing "Bearer " prefix

**Symptom:** `401 Unauthorized` even though the token is in the `Authorization` header.

**Cause:** The header value is missing the `Bearer ` prefix (note the trailing space).

**Fix:** Include the prefix — the header must be `Authorization: Bearer $ACCESS_TOKEN`, not `Authorization: $ACCESS_TOKEN`.

### 3. State parameter too short

**Symptom:** The authorization request fails or is rejected.

**Cause:** The `state` parameter is shorter than 8 characters.

**Fix:** Use a `state` value of at least 8 characters. We recommend 16+ characters for security:

```
state=whoop-csrf-random-abc123
```

### 4. Client credentials in Basic Auth header

**Symptom:** Token exchange returns an error despite correct credentials.

**Cause:** `client_id` and `client_secret` are being sent as a base64-encoded Basic Authentication header. Many OAuth2 libraries default to this behavior.

**Fix:** Send credentials as POST body parameters instead:

```bash
curl -X POST "https://api.prod.whoop.com/oauth/oauth2/token" \
  -d "grant_type=authorization_code" \
  -d "code=$AUTH_CODE" \
  -d "redirect_uri=$REDIRECT_URI" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET"
```

### 5. Literal `nextToken=string` in request

**Symptom:** `400 Bad Request` on a paginated endpoint.

**Cause:** The literal string `nextToken=string` from the API documentation was included in the request.

**Fix:** Omit `nextToken` entirely on the first request. Only include it on subsequent requests using the actual cursor value from the previous response. See [Pagination](#pagination).

### 6. Date format not full ISO 8601

**Symptom:** `400 Bad Request` when using `start` or `end` query parameters.

**Cause:** A date-only format like `2026-01-01` was used instead of the full ISO 8601 format.

**Fix:** Use the full format with time and timezone:

```
start=2026-01-01T00:00:00.000Z
```

See [Date Formatting](#date-formatting).

### 7. Expired access token

**Symptom:** `401 Unauthorized` after the API was working — typically occurs after about 1 hour.

**Cause:** Access tokens expire after 3600 seconds (1 hour).

**Fix:** Use your refresh token to obtain a new access token. You must have requested the `offline` scope during the initial authorization. See [Token Refresh](#token-refresh).
