# WHOOP MCP Server

> A Model Context Protocol (MCP) server that lets AI agents securely query WHOOP sleep, recovery, strain, and workout data.

## Quick Start

```bash
# Install dependencies
uv sync

# Fetch and patch the WHOOP OpenAPI spec (adds missing info.version)
uv run whoop-fetch-openapi

# Run tests
uv run pytest
```

The upstream WHOOP OpenAPI spec at `https://api.prod.whoop.com/developer/doc/openapi.json` is missing the required `info.version` field, which causes import failures in Postman and validation errors in Swagger Editor. The `whoop-fetch-openapi` CLI fetches the spec, patches in the version, and writes a corrected `openapi.json`.

## Links

- [WHOOP Developer Platform](https://developer.whoop.com/)
- [WHOOP API (OpenAPI spec)](https://developer.whoop.com/api)
- [WHOOP Developer Dashboard](https://developer-dashboard.whoop.com/)
