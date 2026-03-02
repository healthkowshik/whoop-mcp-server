# Implementation Plan: WHOOP API Setup Guide

**Branch**: `003-api-setup-guide` | **Date**: 2026-03-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-api-setup-guide/spec.md`

## Summary

Create a tool-agnostic developer guide documenting the 7 non-obvious requirements for setting up the WHOOP API — covering the complete OAuth2 authorization code flow, token refresh, authentication headers, date formatting, and pagination — with curl examples and a quick-reference troubleshooting table. The deliverable is a single Markdown file (`docs/api-setup-guide.md`) in the repository root `docs/` directory.

## Technical Context

**Language/Version**: Markdown (GitHub-Flavored Markdown for rendering)
**Primary Dependencies**: None (documentation only; curl for examples)
**Storage**: N/A
**Testing**: Manual walkthrough against live WHOOP API
**Target Platform**: GitHub repository (rendered by GitHub Markdown viewer)
**Project Type**: Documentation artifact
**Performance Goals**: N/A
**Constraints**: Must be tool-agnostic (FR-008); curl examples only (clarification)
**Scale/Scope**: Single Markdown file, ~200-400 lines

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol Compliance | N/A | No MCP tools affected; documentation only |
| II. Health Data Privacy | PASS | Guide will use placeholder values in curl examples (no real tokens/data). Will include a warning about not committing real credentials. |
| III. API Contract Fidelity | PASS | Guide documents WHOOP API behavior as-is; no data transformation involved |
| IV. Test-First Development | N/A | No code to test; manual walkthrough validates guide accuracy |
| V. Simplicity | PASS | Single Markdown file; no abstractions or tooling |
| Security & Data Handling | PASS | Guide will remind developers not to store client secrets in source code; OAuth2 flow documented per WHOOP Developer Platform docs |
| Development Workflow | PASS | Feature branch `003-api-setup-guide`; will merge via PR |
| Commit Discipline | PASS | Will use `docs:` conventional commit prefix |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/003-api-setup-guide/
├── plan.md              # This file
├── research.md          # Phase 0: WHOOP API OAuth2 details
├── data-model.md        # Phase 1: Guide content structure
├── quickstart.md        # Phase 1: Quick implementation guide
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
docs/
└── api-setup-guide.md   # The deliverable guide
```

**Structure Decision**: Single file in existing `docs/` directory. The guide is a standalone reference document — no code, no tests, no build steps. The `docs/` directory already exists with `data-model.md` from the previous feature.

## Constitution Re-Check (Post Phase 1)

| Principle | Status | Notes |
|-----------|--------|-------|
| II. Health Data Privacy | PASS | Data model confirms all curl examples use placeholders (`<your-client-id>`, `<your-access-token>`). No real health data in guide. |
| III. API Contract Fidelity | PASS | Research verified all URLs, scopes, and parameter formats against official WHOOP docs and OpenAPI spec in repo. |
| V. Simplicity | PASS | Single deliverable file. No tooling, no build steps, no abstractions. |
| Security & Data Handling | PASS | Quickstart includes credential security warning constraint. |

**Post-design gate result**: PASS — no violations.

## Complexity Tracking

No violations to justify — this is a minimal documentation feature.
