# Quickstart: WHOOP API Setup Guide

**Feature**: 003-api-setup-guide | **Date**: 2026-03-02

## What to Build

A single Markdown file at `docs/api-setup-guide.md` containing a developer guide for WHOOP API integration.

## Implementation Steps

1. **Create `docs/api-setup-guide.md`** with the section structure from `data-model.md`
2. **Write the Quick Reference table** (pitfall # | symptom | fix) — scannable overview per FR-009
3. **Write the Prerequisites section** — what developers need before starting
4. **Write the OAuth2 Authorization Flow section** with curl examples for:
   - Authorization request (with state and scopes)
   - Token exchange (credentials in body, not Basic Auth)
   - Token refresh (offline scope, refresh token rotation)
5. **Write the Making API Requests section** with curl examples for:
   - Attaching Bearer token in Authorization header
   - Date formatting for filtered endpoints
   - Pagination with nextToken
6. **Write the Troubleshooting section** — symptom/cause/fix for each of the 7 pitfalls
7. **Add a link to the guide from `README.md`** in the documentation section

## Key Constraints

- All examples must use curl commands (per clarification)
- All examples must use placeholder values (`<your-client-id>`, `<your-access-token>`) — never real credentials
- No tool-specific terminology (no Postman, Insomnia, etc.)
- Include a credential security warning (never commit secrets to source control)

## Validation

- Manually walk through the guide with a real WHOOP developer account
- Verify each curl command is syntactically correct
- Verify the quick-reference table covers all 7 pitfalls
- Verify no tool-specific language slipped in
