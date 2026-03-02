# Feature Specification: WHOOP API Setup Guide

**Feature Branch**: `003-api-setup-guide`
**Created**: 2026-03-02
**Status**: Draft
**Input**: User description: "Document the steps and common pitfalls when setting up WHOOP API integration, covering OAuth2 configuration, authentication headers, pagination, and date formatting — written in a tool-agnostic way so it's useful regardless of the HTTP client."

## Clarifications

### Session 2026-03-02

- Q: Should the guide cover token refresh/expiration handling, or only initial token acquisition? → A: Include a brief token refresh section covering how to use the refresh token to get a new access token.
- Q: What format should the concrete HTTP request/response examples use? → A: curl commands — widely recognized and directly copy-pasteable into a terminal.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - First-Time API Setup (Priority: P1)

A developer wants to make their first successful WHOOP API call. They have registered an application in the WHOOP Developer Portal and have their client ID and client secret, but they are unsure how to correctly configure OAuth2 authentication. The guide walks them through the complete OAuth2 flow, highlighting the non-obvious configuration choices that differ from typical OAuth2 defaults (authorization in headers, state parameter length, client credentials in body).

**Why this priority**: Without successful authentication, no API calls are possible. This is the #1 blocker for every new developer and the area with the most non-obvious requirements.

**Independent Test**: Can be fully tested by following the guide from scratch with a new WHOOP developer account and successfully obtaining an access token on the first attempt.

**Acceptance Scenarios**:

1. **Given** a developer with WHOOP client credentials and no prior setup, **When** they follow the OAuth2 setup section of the guide, **Then** they successfully obtain an access token without encountering authentication errors.
2. **Given** a developer configuring OAuth2 for the first time, **When** they read the state parameter guidance, **Then** they provide a state value that meets WHOOP's minimum length requirement (more than 8 characters) and the authorization request succeeds.
3. **Given** a developer sending client credentials, **When** they follow the guide's instructions to send credentials in the request body (not as a Basic Auth header), **Then** the token exchange completes successfully.
4. **Given** a developer whose access token has expired, **When** they follow the token refresh section, **Then** they obtain a new access token using their refresh token without repeating the full authorization flow.

---

### User Story 2 - Making API Requests Successfully (Priority: P2)

A developer has obtained an access token and wants to query WHOOP endpoints (e.g., cycles, sleep, recovery). They need to know how to attach the token to requests, how to format date parameters, and how to avoid sending placeholder query parameters that cause errors.

**Why this priority**: After authentication, this is the next step every developer needs. The date format and placeholder parameter issues are common sources of confusing 400 errors.

**Independent Test**: Can be fully tested by making a successful API request to any WHOOP data endpoint (e.g., list cycles) with correct authorization header, proper date formatting, and no placeholder parameters.

**Acceptance Scenarios**:

1. **Given** a developer with a valid access token, **When** they follow the guide to attach the token as a Bearer token in the Authorization request header, **Then** the API returns data instead of a 401 error.
2. **Given** a developer querying a date-filtered endpoint, **When** they use the full ISO 8601 format documented in the guide (e.g., `2026-01-01T00:00:00.000Z`), **Then** the API returns filtered results without date parsing errors.
3. **Given** a developer using an API reference that shows `nextToken=string` as a parameter, **When** they read the guide's note about placeholder parameters, **Then** they omit `nextToken` from their initial request and only use it with actual pagination tokens returned by the API.

---

### User Story 3 - Troubleshooting Failed Requests (Priority: P3)

A developer has attempted to set up the WHOOP API but is getting errors. They use the guide as a troubleshooting reference to identify which of the common pitfalls they've hit and how to fix it.

**Why this priority**: Serves as an ongoing reference after initial setup. Reduces time spent debugging common misconfigurations.

**Independent Test**: Can be tested by a developer with a known misconfiguration (e.g., credentials in Basic Auth header instead of body) finding the relevant troubleshooting entry and resolving the issue.

**Acceptance Scenarios**:

1. **Given** a developer receiving a 401 error, **When** they consult the troubleshooting section, **Then** they find guidance on verifying that authorization data is sent in request headers (not query parameters) and that the token is a valid Bearer token.
2. **Given** a developer receiving a 400 error on a date-filtered request, **When** they consult the troubleshooting section, **Then** they find the correct ISO 8601 date format with a concrete example.
3. **Given** a developer whose OAuth2 token exchange is failing, **When** they consult the troubleshooting section, **Then** they find guidance on both the state parameter length requirement and the client credentials placement.

---

### Edge Cases

- What happens when a developer uses a date format like `2026-01-01` (date-only, no time component)? The guide should explicitly call out that this format is insufficient and show the full format required.
- What happens when a developer uses a state parameter of exactly 8 characters? The guide should clarify whether the minimum is "more than 8" (i.e., 9+) or "at least 8".
- What happens when a developer includes `nextToken=string` literally in the URL? The guide should explain this is a documentation placeholder and not a required parameter.
- What happens when a developer sends client credentials via Basic Auth (base64-encoded header) instead of in the request body? The guide should note this is a common OAuth2 default that does not work with the WHOOP API.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The guide MUST document the complete OAuth2 authorization flow for the WHOOP API, including the authorization URL, token exchange URL, required scopes, and redirect URI setup.
- **FR-002**: The guide MUST include a brief token refresh section explaining how to use a refresh token to obtain a new access token when the current one expires, without repeating the full authorization flow.
- **FR-003**: The guide MUST explicitly state that authorization data (Bearer token) must be sent in the HTTP `Authorization` request header, not as a query parameter or other mechanism.
- **FR-004**: The guide MUST document that the OAuth2 `state` parameter must be at least 8 characters (per official WHOOP documentation), with a recommendation to use 16+ characters and a concrete example of a valid value.
- **FR-005**: The guide MUST document that client credentials (client ID and client secret) must be sent in the token request body, not as a Basic Authentication header.
- **FR-006**: The guide MUST document the required date format for date-filtered endpoints as full ISO 8601 with time and timezone (e.g., `2026-01-01T00:00:00.000Z`), with both valid and invalid examples.
- **FR-007**: The guide MUST explain that `nextToken=string` shown in API documentation is a placeholder and should be omitted from initial requests; actual pagination tokens are returned in API responses.
- **FR-008**: The guide MUST be written in a tool-agnostic manner, using generic HTTP concepts (headers, request body, query parameters) rather than tool-specific terminology (e.g., no "Postman tab" or "Insomnia dropdown" references).
- **FR-009**: The guide MUST include a quick-reference summary (checklist or table) of all common pitfalls for developers who want a scannable overview.
- **FR-010**: The guide MUST include concrete examples as curl commands showing correct configuration for each pitfall documented, so developers can copy-paste and adapt them to any HTTP client.

### Key Entities

- **OAuth2 Configuration**: The set of parameters needed to complete the authorization flow — client credentials, state, redirect URI, scopes, and token endpoint configuration.
- **API Request**: An HTTP request to a WHOOP data endpoint, characterized by its authorization header, query parameters (including date filters and pagination tokens), and expected response format.
- **Common Pitfall**: A non-obvious configuration requirement that differs from typical OAuth2/REST API defaults, documented with the symptom (error), cause, and correct configuration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer with WHOOP client credentials can go from zero to a successful API data response by following the guide alone, without needing to consult external resources or contact support.
- **SC-002**: The guide covers all 7 documented topics: (1) auth in headers, (2) Bearer token format, (3) state parameter length, (4) client credentials in body, (5) placeholder parameter removal, (6) ISO 8601 date format, (7) token refresh using refresh tokens.
- **SC-003**: Each pitfall entry includes the symptom (what error the developer sees), the cause, and the fix — enabling troubleshooting use in under 2 minutes per issue.
- **SC-004**: The guide is usable with any HTTP client (curl, httpx, Postman, Insomnia, browser fetch, etc.) without modification.

## Assumptions

- Developers have already registered an application in the WHOOP Developer Portal and have their client ID and client secret before starting this guide.
- The WHOOP API uses standard OAuth2 Authorization Code flow (the guide documents deviations from standard defaults, not the entire OAuth2 spec).
- The official WHOOP documentation states the state parameter minimum is 8 characters. The guide will state this minimum and recommend 16+ characters as a security best practice.
- The WHOOP API pagination uses a cursor-based approach where `nextToken` values are returned in responses and should only be included in subsequent requests.
