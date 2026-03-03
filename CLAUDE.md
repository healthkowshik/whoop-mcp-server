# whoop-mcp-server Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-01

## Active Technologies
- N/A (Markdown + Mermaid syntax only) + None (Mermaid rendering handled by GitHub/viewers) (002-openapi-er-docs)
- Markdown (GitHub-Flavored Markdown for rendering) + None (documentation only; curl for examples) (003-api-setup-guide)
- Python 3.11+ + httpx (HTTP client), tenacity (retry with backoff) (004-oauth-token-manager)
- Pluggable `TokenStore` protocol — default in-memory; persistent implementations provided by deployment layer (004-oauth-token-manager)
- Python 3.11+ + pydantic>=2.10.0 (new), httpx, tenacity>=9.1.4 (005-pydantic-validation)
- N/A (dict-based TokenStore protocol unchanged) (005-pydantic-validation)

- Python 3.11+ + httpx (HTTP client) (001-fix-openapi-version)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes
- 005-pydantic-validation: Added Python 3.11+ + pydantic>=2.10.0 (new), httpx, tenacity>=9.1.4
- 004-oauth-token-manager: Added Python 3.11+ + httpx (HTTP client), tenacity (retry with backoff)
- 003-api-setup-guide: Added Markdown (GitHub-Flavored Markdown for rendering) + None (documentation only; curl for examples)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
