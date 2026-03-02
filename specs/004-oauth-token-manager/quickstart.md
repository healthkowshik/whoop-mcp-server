# Quickstart: WHOOP OAuth Token Manager

**Feature**: 004-oauth-token-manager | **Date**: 2026-03-02

## Setup

```bash
# From repo root
uv sync                    # Install dependencies (httpx, tenacity)
uv run pytest tests/       # Run tests
uv run ruff check src/     # Lint
```

## Usage: Initialize with Existing Tokens

```python
from whoop_mcp_server.auth import TokenManager, WhoopCredentials

credentials = WhoopCredentials(
    client_id="your-client-id",
    client_secret="your-client-secret",
)

manager = TokenManager.from_tokens(
    credentials=credentials,
    access_token="your-access-token",
    refresh_token="your-refresh-token",
    expires_in=3600,
)

# Get a valid token (refreshes automatically if needed)
token = await manager.get_valid_token()
```

## Usage: Exchange Authorization Code

```python
manager = TokenManager(credentials=credentials)
await manager.exchange_code(
    code="authorization-code-from-callback",
    redirect_uri="https://your-app.com/callback",
)

token = await manager.get_valid_token()
```

## Usage: With Persistent Storage

```python
from whoop_mcp_server.auth import TokenManager, WhoopCredentials

# Any object with async save(data: dict) and load() -> dict | None works
class FileTokenStore:
    async def save(self, data: dict) -> None:
        # write to encrypted file
        ...
    async def load(self) -> dict | None:
        # read from encrypted file, or None if not found
        ...

manager = TokenManager(
    credentials=credentials,
    store=FileTokenStore(),
)
# On init, loads tokens from store if available
# On refresh, saves new tokens to store automatically
```

## File Layout

```
src/whoop_mcp_server/
├── __init__.py
└── auth/
    ├── __init__.py          # Public exports: TokenManager, WhoopCredentials, TokenStore, errors
    ├── token_manager.py     # TokenManager class
    ├── token_store.py       # TokenStore protocol + MemoryTokenStore
    ├── models.py            # TokenPair, WhoopCredentials
    └── errors.py            # AuthenticationError, TransientError

tests/
├── unit/
│   ├── test_token_manager.py       # Core logic: exchange, refresh, get_valid_token
│   ├── test_token_store.py         # MemoryTokenStore behavior
│   ├── test_models.py              # TokenPair, WhoopCredentials validation + repr
│   └── test_errors.py              # Error message redaction
└── integration/
    └── test_token_refresh_flow.py  # Full exchange → refresh → concurrent refresh with mocked WHOOP
```

## Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run only unit tests
uv run pytest tests/unit/ -v

# Run only integration tests
uv run pytest tests/integration/ -v

# Run with coverage
uv run pytest tests/ --cov=whoop_mcp_server.auth
```

All tests use mocked WHOOP responses (httpx mock transport). No real WHOOP account needed.
