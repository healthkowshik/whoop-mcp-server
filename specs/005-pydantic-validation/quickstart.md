# Quickstart: Pydantic Validation for Auth Models

**Feature**: 005-pydantic-validation
**Date**: 2026-03-03

## Setup

```bash
# Add pydantic dependency
uv add "pydantic>=2.10.0"

# Verify installation
uv run python -c "import pydantic; print(pydantic.__version__)"

# Run tests
uv run pytest tests/ -v

# Lint + type check
uv run ruff check .
uv run ty check src/
```

## Test Scenarios

### Scenario 1: Construction Validation (US1)

```python
import time
from whoop_mcp_server.auth.models import WhoopCredentials, TokenPair, TokenResponse

# Valid construction — identical syntax to before
creds = WhoopCredentials(client_id="my-id", client_secret="my-secret")
assert creds.client_id == "my-id"
assert creds.client_secret == "my-secret"

tp = TokenPair(
    access_token="eyJ...",
    refresh_token="dGh...",
    expires_at=time.monotonic() + 3600,
    scope="offline",
    token_type="bearer",
)
assert tp.access_token == "eyJ..."

# Invalid data raises ValueError (Pydantic's ValidationError is a ValueError subclass)
try:
    TokenPair(access_token="", refresh_token="x", expires_at=1.0, scope="", token_type="")
except ValueError as e:
    assert "access_token" in str(e)

# Immutability enforced
try:
    tp.expires_at = 0.0
except Exception:
    pass  # ValidationError raised — field is frozen
```

### Scenario 2: Serialization Round-Trip (US2)

```python
import time
from whoop_mcp_server.auth.models import TokenPair

tp = TokenPair(
    access_token="eyJ...",
    refresh_token="dGh...",
    expires_at=time.monotonic() + 3600,
    scope="offline read:recovery",
    token_type="bearer",
)

# Serialize to store dict
store_dict = tp.to_store_dict()
assert "access_token" in store_dict
assert "expires_at_utc" in store_dict  # UTC ISO 8601, not monotonic float

# Deserialize back
restored = TokenPair.from_store_dict(store_dict)
assert restored.access_token == tp.access_token
assert restored.refresh_token == tp.refresh_token
assert restored.scope == tp.scope
# expires_at will differ slightly (monotonic conversion) but should be close
assert abs(restored.expires_at - tp.expires_at) < 1.0
```

### Scenario 3: Parse Token Response (US3)

```python
from whoop_mcp_server.auth.models import TokenResponse

# From WHOOP API response dict
api_response = {
    "access_token": "eyJ...",
    "refresh_token": "dGh...",
    "expires_in": 3600,
    "scope": "offline read:recovery",
    "token_type": "bearer",
}
resp = TokenResponse.model_validate(api_response)
tp = resp.to_token_pair()
assert tp.access_token == "eyJ..."
assert not tp.is_expired()

# String coercion works
api_response_str = {**api_response, "expires_in": "3600"}
resp2 = TokenResponse.model_validate(api_response_str)
assert resp2.expires_in == 3600  # coerced to int

# Unknown fields ignored
api_response_extra = {**api_response, "new_field": "ignored"}
resp3 = TokenResponse.model_validate(api_response_extra)
# No error — new_field silently discarded
```

### Scenario 4: Secret Masking (US1, FR-002)

```python
from whoop_mcp_server.auth.models import WhoopCredentials, TokenPair

creds = WhoopCredentials(client_id="my-id", client_secret="super-secret-value")
assert "super-secret-value" not in repr(creds)
assert "***" in repr(creds)
assert "super-secret-value" not in str(creds)

tp = TokenPair(
    access_token="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.long_token",
    refresh_token="dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4.long_refresh",
    expires_at=100000.0,
    scope="offline",
    token_type="bearer",
)
assert "long_token" not in repr(tp)
assert "long_refresh" not in repr(tp)
assert "***" in repr(tp)
```

### Scenario 5: Integration with TokenManager (FR-008)

```python
# All existing TokenManager usage patterns work unchanged
from whoop_mcp_server.auth import WhoopCredentials, TokenManager

creds = WhoopCredentials(client_id="test", client_secret="secret")
manager = TokenManager(credentials=creds)

# from_tokens works unchanged
manager2 = TokenManager.from_tokens(
    credentials=creds,
    access_token="eyJ...",
    refresh_token="dGh...",
    expires_in=3600,
)
```

## Validation Checklist

- [ ] `uv add "pydantic>=2.10.0"` succeeds
- [ ] All 63+ existing tests pass without assertion changes
- [ ] New model validation tests pass (empty string, missing field, wrong type, zero expiry)
- [ ] Serialization round-trip tests pass (5+ distinct token states)
- [ ] Secret masking verified (no secrets in repr/str/error output)
- [ ] `ruff check .` clean
- [ ] `ty check src/` clean
- [ ] No new dependencies beyond pydantic (check `uv tree`)
