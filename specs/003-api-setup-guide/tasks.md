# Tasks: WHOOP API Setup Guide

**Input**: Design documents from `/specs/003-api-setup-guide/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Tests**: No tests requested — this is a documentation-only feature. Validation is manual.

**Organization**: Tasks are grouped by user story. All content tasks target a single file (`docs/api-setup-guide.md`) so they are sequential within and across phases. The README update (T011) targets a different file.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Create the guide file with section skeleton

- [x] T001 Create `docs/api-setup-guide.md` with the full heading structure (title, Quick Reference, Prerequisites, OAuth2 Authorization Flow with subsections for Authorization Request / Token Exchange / Token Refresh, Making API Requests with subsections for Authentication Header / Date Formatting / Pagination, Troubleshooting) and a one-paragraph introduction explaining the guide's purpose. Use the section hierarchy from `specs/003-api-setup-guide/data-model.md`. Leave section bodies empty (placeholder comments) for subsequent tasks to fill.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared content that all user stories reference — must be complete before story-specific sections

**⚠️ CRITICAL**: The quick reference table and prerequisites are referenced by all subsequent sections

- [x] T002 Write the Quick Reference table in `docs/api-setup-guide.md` listing all 7 pitfalls in a Markdown table with columns: #, Pitfall, Symptom, Fix. Use the pitfall reference from `specs/003-api-setup-guide/data-model.md` (Pitfall Reference table). This fulfills FR-009.
- [x] T003 Write the Prerequisites section in `docs/api-setup-guide.md` covering: (1) WHOOP Developer Portal registration and app creation, (2) obtaining Client ID and Client Secret, (3) configuring a Redirect URI in the portal (localhost for local testing — no server needed, copy code from browser address bar), (4) a security warning to never commit client secrets to source control or logs, (5) shell variable setup block (`export CLIENT_ID`, `CLIENT_SECRET`, `REDIRECT_URI`) so all curl examples are copy-pasteable.

**Checkpoint**: Guide skeleton with quick reference and prerequisites ready — story sections can now be written sequentially

---

## Phase 3: User Story 1 — First-Time API Setup (Priority: P1) 🎯 MVP

**Goal**: A developer with WHOOP client credentials can complete the full OAuth2 flow and obtain an access token by following this section alone.

**Independent Test**: Follow the guide from scratch with a new WHOOP developer account; successfully obtain an access token on the first attempt without consulting other resources.

### Implementation for User Story 1

- [x] T004 [US1] Write the Authorization Request subsection in `docs/api-setup-guide.md` under "OAuth2 Authorization Flow". Include: (1) the authorization URL `https://api.prod.whoop.com/oauth/oauth2/auth`, (2) required query parameters (`response_type=code`, `client_id`, `redirect_uri`, `scope`, `state`), (3) state parameter requirement (minimum 8 characters, recommend 16+, auto-generated via `openssl rand -hex 12`), (4) available scopes table from `specs/003-api-setup-guide/research.md` R5 (include `offline` scope note for refresh tokens), (5) an `open` command (macOS) that opens the authorization URL in the browser for login and consent, (6) instruction to copy the `code` from the browser address bar after redirect. This fulfills FR-001, FR-004.
- [x] T005 [US1] Write the Token Exchange subsection in `docs/api-setup-guide.md` under "OAuth2 Authorization Flow". Include: (1) the token endpoint `https://api.prod.whoop.com/oauth/oauth2/token`, (2) that `client_id` and `client_secret` MUST be sent as POST body parameters (not Basic Auth header), (3) required body parameters (`grant_type=authorization_code`, `code`, `redirect_uri`, `client_id`, `client_secret`), (4) curl example showing the POST request with `-d` body parameters, (5) expected JSON response format (access_token, refresh_token, expires_in: 3600, scope, token_type: bearer). This fulfills FR-005.
- [x] T006 [US1] Write the Token Refresh subsection in `docs/api-setup-guide.md` under "OAuth2 Authorization Flow". Include: (1) that `offline` scope must have been requested during initial authorization, (2) refresh request body parameters (`grant_type=refresh_token`, `refresh_token`, `client_id`, `client_secret`, `scope=offline`), (3) critical behavior: old access token and refresh token are both invalidated after refresh — always store the new refresh token from the response, (4) curl example showing the refresh POST request, (5) note that tokens expire after 1 hour (3600 seconds). This fulfills FR-002.

**Checkpoint**: User Story 1 complete — a developer can authenticate and get tokens by following these sections

---

## Phase 4: User Story 2 — Making API Requests Successfully (Priority: P2)

**Goal**: A developer with an access token can successfully query WHOOP data endpoints with correct headers, date formatting, and pagination handling.

**Independent Test**: Make a successful API request to the cycles endpoint (`GET https://api.prod.whoop.com/developer/v2/cycle`) with correct Bearer token, proper ISO 8601 date parameters, and no placeholder query parameters.

### Implementation for User Story 2

- [x] T007 [US2] Write the Authentication Header subsection in `docs/api-setup-guide.md` under "Making API Requests". Include: (1) that the Bearer token MUST be sent in the HTTP `Authorization` header (not as a query parameter), (2) exact header format: `Authorization: Bearer $ACCESS_TOKEN`, (3) curl example making a GET request to `https://api.prod.whoop.com/developer/v2/cycle` with `-H "Authorization: Bearer $ACCESS_TOKEN"`, (4) note about 401 response meaning expired or invalid token. This fulfills FR-003.
- [x] T008 [US2] Write the Date Formatting subsection in `docs/api-setup-guide.md` under "Making API Requests". Include: (1) that `start` and `end` query parameters require full ISO 8601 format with time and timezone, (2) valid format: `2026-01-01T00:00:00.000Z`, (3) invalid formats table showing common mistakes (date-only `2026-01-01`, missing timezone `2026-01-01T00:00:00`, missing milliseconds `2026-01-01T00:00:00Z` — note which ones the API actually rejects vs accepts if known), (4) curl example with `start` and `end` parameters URL-encoded in the query string, (5) note that `start` is inclusive and `end` is exclusive. This fulfills FR-006.
- [x] T009 [US2] Write the Pagination subsection in `docs/api-setup-guide.md` under "Making API Requests". Include: (1) that `nextToken=string` in the API docs is a documentation placeholder — omit it from the first request, (2) pagination parameters: `limit` (1-25, default 10), `nextToken` (only from previous response), (3) curl example for first request (no nextToken), (4) curl example for subsequent request using a nextToken value from a previous response, (5) how to detect the last page (no `next_token` field in response or it is null). This fulfills FR-007.

**Checkpoint**: User Stories 1 AND 2 complete — a developer can authenticate and make successful data requests

---

## Phase 5: User Story 3 — Troubleshooting Failed Requests (Priority: P3)

**Goal**: A developer experiencing errors can look up their specific symptom and find the cause and fix within 2 minutes.

**Independent Test**: Given a developer with a known misconfiguration (e.g., credentials in Basic Auth header), they can find the matching troubleshooting entry and resolve the issue.

### Implementation for User Story 3

- [x] T010 [US3] Write the Troubleshooting section in `docs/api-setup-guide.md`. Create a subsection for each of the 7 pitfalls using a consistent format: **Symptom** (the error/behavior the developer sees), **Cause** (what's misconfigured), **Fix** (what to change, with a brief curl snippet or reference to the relevant guide section). The 7 entries are: (1) 401 — token not in Authorization header, (2) 401 — missing "Bearer " prefix, (3) authorization fails — state too short, (4) token exchange fails — credentials in Basic Auth header instead of body, (5) 400 — `nextToken=string` sent literally, (6) 400 — date format not full ISO 8601, (7) 401 after ~1 hour — access token expired, need to refresh. This fulfills SC-003.

**Checkpoint**: All user stories complete — guide covers authentication, requests, and troubleshooting

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Discoverability and final quality validation

- [x] T011 [P] Add a link to `docs/api-setup-guide.md` from `README.md` in the documentation or getting started section. Use a brief description like "API Setup Guide — common pitfalls and OAuth2 configuration for the WHOOP API".
- [x] T012 Final validation of `docs/api-setup-guide.md`: (1) verify all 7 pitfalls appear in both the Quick Reference table and the Troubleshooting section, (2) verify every curl command is syntactically valid (proper quoting, flags, URL encoding), (3) verify no tool-specific language (Postman, Insomnia, etc.) appears anywhere, (4) verify all examples use placeholder values (no real tokens or credentials), (5) verify the guide reads coherently end-to-end as a standalone document per SC-001.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T001 creates the file skeleton)
- **User Story 1 (Phase 3)**: Depends on Phase 2 (quick reference and prerequisites done)
- **User Story 2 (Phase 4)**: Depends on Phase 3 (OAuth2 flow must precede API request sections in the document)
- **User Story 3 (Phase 5)**: Depends on Phases 3 and 4 (troubleshooting references content from both)
- **Polish (Phase 6)**: T011 can run in parallel with Phase 5; T012 depends on all content being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends only on Foundational phase — delivers MVP (authentication works)
- **User Story 2 (P2)**: Depends on US1 (document flow: auth before requests) — independently testable once auth section exists
- **User Story 3 (P3)**: Depends on US1 and US2 (references content from both) — independently testable as a lookup reference

### Within Each User Story

- Tasks are sequential (all write to the same file section)
- Each task builds on the previous subsection within the same guide section

### Parallel Opportunities

- T011 (README update) can run in parallel with T010 or T012 (different file)
- All other tasks are sequential due to single-file constraint

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002, T003)
3. Complete Phase 3: User Story 1 (T004, T005, T006)
4. **STOP and VALIDATE**: A developer can follow the guide to get an access token
5. Ship if ready — authentication guide alone delivers significant value

### Incremental Delivery

1. Setup + Foundational → File skeleton with quick reference and prerequisites
2. Add User Story 1 → Authentication guide complete → **MVP ready**
3. Add User Story 2 → Request-making guide complete → Full happy-path coverage
4. Add User Story 3 → Troubleshooting reference complete → Full guide
5. Polish → README link + final validation → Ship

---

## Notes

- All tasks write to `docs/api-setup-guide.md` (single file) — limited parallelism by design
- No tests in this task list — the spec does not request automated tests; validation is manual (T012)
- Use `specs/003-api-setup-guide/research.md` for all OAuth2 URLs, scopes, and parameter details
- Use `specs/003-api-setup-guide/data-model.md` for the pitfall reference table and entity attributes
- All curl examples must use shell variables (`$CLIENT_ID`, `$CLIENT_SECRET`, `$ACCESS_TOKEN`, `$REFRESH_TOKEN`, `$AUTH_CODE`) set once in Prerequisites — never hardcoded credentials
- Commit after each phase using `docs:` conventional commit prefix
