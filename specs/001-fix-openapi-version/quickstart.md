# Quickstart: Fix WHOOP OpenAPI Version Field

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) installed

## Setup

```bash
# Clone the repository
git clone <repo-url>
cd whoop-mcp-server

# Install dependencies
uv sync
```

## Usage

### Fetch and patch the OpenAPI spec

```bash
uv run whoop-fetch-openapi
```

This fetches the WHOOP OpenAPI spec, adds the missing
`info.version` field if absent, and writes the corrected
spec to `openapi.json` in the repository root.

### Custom output path

```bash
uv run whoop-fetch-openapi --output docs/whoop-api.json
```

## Verify the output

### Import into Postman

1. Open Postman
2. Click **Import** → **File**
3. Select `openapi.json`
4. Confirm all 13 endpoints appear without errors

### Validate in Swagger Editor

1. Open https://editor.swagger.io/
2. Paste the contents of `openapi.json`
3. Confirm no error 3030501

## Run tests

```bash
uv run pytest
```

## Troubleshooting

**"Fetch error: upstream URL unreachable"**
- Check your internet connection
- Verify https://api.prod.whoop.com is accessible

**"Parse error: response is not valid JSON"**
- The upstream API may be temporarily returning invalid data
- Try again after a few minutes
