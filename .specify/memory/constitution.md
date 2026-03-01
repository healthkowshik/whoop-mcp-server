<!--
  Sync Impact Report
  ==================
  Version change: 1.0.0 → 1.0.1
  Modified principles: None
  Modified sections:
    - Security & Data Handling: `pip audit` → `uv audit` (Astral toolchain)
  Added sections: None
  Removed sections: None
  Templates requiring updates:
    - .specify/templates/plan-template.md ✅ no update needed
    - .specify/templates/spec-template.md ✅ no update needed
    - .specify/templates/tasks-template.md ✅ no update needed
  Follow-up TODOs: None
-->

# WHOOP MCP Server Constitution

## Core Principles

### I. MCP Protocol Compliance

The server MUST conform to the Model Context Protocol
specification. Every tool MUST declare a well-formed JSON Schema
for its inputs and produce structured responses consumable by
AI agents. New tools MUST NOT invent ad-hoc communication
patterns outside the MCP standard.

**Rationale**: AI agents depend on predictable schemas and
deterministic behavior; deviations break downstream tool-use
reliability.

### II. Health Data Privacy

WHOOP data is personal health information. The server MUST NOT
persist user health data beyond the lifetime of a single
request-response cycle. OAuth tokens and refresh tokens MUST be
stored only in memory or in a user-controlled credential store —
never in logs, analytics, or unencrypted files. Logged output
MUST NOT contain identifiable health metrics or access tokens.

**Rationale**: Users trust this server with intimate biometric
data; mishandling it erodes trust and may violate privacy
regulations.

### III. API Contract Fidelity

All interactions with the WHOOP API MUST faithfully represent
upstream data models without lossy transformation. Field names,
units, and value ranges returned by the WHOOP API MUST be
preserved as-is in MCP tool responses. Error responses from the
WHOOP API MUST propagate to the caller with sufficient context
for the agent to reason about the failure.

**Rationale**: Health data accuracy is non-negotiable; silent
data loss or unit conversion errors can lead to incorrect
health conclusions.

### IV. Test-First Development

Tests MUST be written before implementation code. The
Red-Green-Refactor cycle is enforced: tests fail first, then
implementation makes them pass, then code is cleaned up.
Contract tests MUST validate every MCP tool schema. Integration
tests MUST cover WHOOP API request/response flows using
recorded fixtures.

**Rationale**: An MCP server is an integration boundary where
bugs manifest as silent data corruption; tests are the primary
defense.

### V. Simplicity

Start with the minimum viable set of MCP tools that cover core
WHOOP data domains (sleep, recovery, strain, workouts). No
speculative abstractions, premature caching layers, or features
without a demonstrated user need. YAGNI applies: add complexity
only when a concrete requirement demands it.

**Rationale**: A small, correct surface area is easier to
maintain, audit, and trust than a sprawling one.

## Security & Data Handling

- All network communication with the WHOOP API MUST use HTTPS.
  The server MUST NOT disable TLS certificate verification.
- OAuth 2.0 authorization code flow MUST be implemented per
  WHOOP Developer Platform documentation. The server MUST NOT
  store client secrets in source code or version control.
- Dependency supply chain: only well-maintained, audited
  dependencies SHOULD be used. `uv` (Astral) is the required
  package manager and runner. `uv pip audit` or equivalent
  MUST be run in CI before release.
- The server MUST validate and sanitize all inputs received via
  MCP tool calls before forwarding them to the WHOOP API.

## Development Workflow

- **Branching**: Feature branches follow the `NNN-feature-name`
  convention. All changes merge to `main` via pull request.
- **Code Review**: Every PR MUST be reviewed before merge.
  Reviews MUST verify constitution compliance.
- **CI Pipeline**: Linting, type checking, and the full test
  suite MUST pass before a PR can merge.
- **Commit Discipline**: Each commit SHOULD represent a single
  logical change. Commit messages MUST follow Conventional
  Commits format (e.g., `feat:`, `fix:`, `docs:`).

## Governance

This constitution is the highest-authority document for the
WHOOP MCP Server project. All design decisions, code reviews,
and architectural choices MUST be evaluated against these
principles.

**Amendment procedure**:
1. Propose the change in a pull request modifying this file.
2. Document the rationale and impact in the PR description.
3. After merge, run `/speckit.constitution` to propagate
   changes across dependent templates and artifacts.

**Versioning policy**: This constitution follows semantic
versioning — MAJOR for principle removals or incompatible
redefinitions, MINOR for new principles or material expansions,
PATCH for clarifications and wording fixes.

**Compliance review**: At each `/speckit.plan` invocation, the
Constitution Check section MUST verify the proposed design
against all active principles before proceeding.

**Version**: 1.0.1 | **Ratified**: 2026-03-01 | **Last Amended**: 2026-03-01
