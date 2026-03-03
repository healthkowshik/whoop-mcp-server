# Contract: Auth Models Public API

**Feature**: 005-pydantic-validation
**Date**: 2026-03-03

## Module: `whoop_mcp_server.auth.models`

### Exports

| Symbol            | Type      | New? | Notes                                    |
|-------------------|-----------|------|------------------------------------------|
| `WhoopCredentials`| class     | No   | Replaces dataclass with Pydantic model   |
| `TokenPair`       | class     | No   | Replaces dataclass with Pydantic model   |
| `TokenResponse`   | class     | Yes  | New model for API response parsing       |

### WhoopCredentials

**Construction** (unchanged):
```python
creds = WhoopCredentials(client_id="abc", client_secret="xyz")
```

**Field access** (unchanged):
```python
creds.client_id     # str
creds.client_secret # str
```

**Immutability** (strengthened — was frozen dataclass, now frozen Pydantic):
```python
creds.client_id = "new"  # raises ValidationError (was FrozenInstanceError)
```

**Repr** (unchanged behavior):
```python
repr(creds)  # "WhoopCredentials(client_id='abc', client_secret='***')"
str(creds)   # same as repr
```

**Validation** (new — was not validated):
```python
WhoopCredentials(client_id="", client_secret="x")   # raises ValueError (empty client_id)
WhoopCredentials(client_id="x", client_secret="")   # raises ValueError (empty client_secret)
```

### TokenPair

**Construction** (unchanged):
```python
tp = TokenPair(
    access_token="eyJ...",
    refresh_token="dGh...",
    expires_at=time.monotonic() + 3600,
    scope="offline",
    token_type="bearer",
)
```

**Field access** (unchanged):
```python
tp.access_token   # str
tp.refresh_token  # str
tp.expires_at     # float
tp.scope          # str
tp.token_type     # str
```

**Immutability** (NEW — was mutable dataclass):
```python
tp.expires_at = 0.0  # raises ValidationError (was allowed before)
# Use model_copy for new instances:
new_tp = tp.model_copy(update={"expires_at": time.monotonic() + 60})
```

**Repr** (unchanged behavior):
```python
repr(tp)  # "TokenPair(access_token='eyJhbG***', ...)"
```

**Validation** (unchanged behavior — was manual __post_init__, now Pydantic):
```python
TokenPair(access_token="", ...)     # raises ValueError (match="access_token")
TokenPair(refresh_token="", ...)    # raises ValueError (match="refresh_token")
TokenPair(expires_at=-1.0, ...)     # raises ValueError (match="expires_at")
TokenPair(expires_at=0.0, ...)      # raises ValueError (must be > 0)
```

**Methods** (is_expired unchanged, to_store_dict/from_store_dict NEW):
```python
tp.is_expired()                 # bool — unchanged
tp.is_expired(buffer_seconds=300)  # bool — unchanged
tp.to_store_dict()              # dict — NEW (replaces manual serialization in token_manager)
TokenPair.from_store_dict(data) # TokenPair — NEW (replaces manual deserialization in token_manager)
```

### TokenResponse (NEW)

**Construction** (from API response dict):
```python
resp = TokenResponse(
    access_token="eyJ...",
    refresh_token="dGh...",
    expires_in=3600,
    scope="offline",
    token_type="bearer",
)
# Or from dict:
resp = TokenResponse.model_validate(api_response_dict)
```

**Type coercion**:
```python
resp = TokenResponse(expires_in="3600", ...)  # coerced to int 3600
```

**Forward compatibility**:
```python
resp = TokenResponse(extra_field="ignored", ...)  # extra fields silently ignored
```

**Conversion to TokenPair**:
```python
tp = resp.to_token_pair()  # TokenPair with expires_at = monotonic() + expires_in
```

## Module: `whoop_mcp_server.auth`

### Updated `__init__.py` Exports

```python
__all__ = [
    "AuthenticationError",
    "MemoryTokenStore",
    "TokenManager",
    "TokenPair",
    "TokenResponse",    # NEW
    "TokenStore",
    "TransientError",
    "WhoopCredentials",
]
```

## Module: `whoop_mcp_server.auth.token_manager`

### Changes to TokenManager Internals

No public API changes. Internal methods refactored:

| Method                 | Before                              | After                                        |
|------------------------|-------------------------------------|----------------------------------------------|
| `_parse_token_response`| Manual dict access + TokenPair()    | `TokenResponse.model_validate(data).to_token_pair()` |
| `_save_to_store`       | Manual monotonic→UTC + dict build   | `self._token_pair.to_store_dict()`           |
| `_load_from_store`     | Manual UTC→monotonic + TokenPair()  | `TokenPair.from_store_dict(data)`            |

## Backward Compatibility Matrix

| Operation                                   | Before (dataclass) | After (Pydantic) | Compatible? |
|---------------------------------------------|--------------------|-------------------|-------------|
| `WhoopCredentials(client_id=..., ...)`      | keyword args       | keyword args      | Yes         |
| `creds.client_secret == "my-secret"`        | str == str         | str == str        | Yes         |
| `creds.client_id = "new"`                   | FrozenInstanceError| ValidationError   | ~Yes*       |
| `TokenPair(access_token=..., ...)`          | keyword args       | keyword args      | Yes         |
| `tp.access_token`                           | str                | str               | Yes         |
| `tp.is_expired(buffer_seconds=300)`         | bool               | bool              | Yes         |
| `tp.expires_at = new_value`                 | allowed            | ValidationError   | No**        |
| `pytest.raises(ValueError, match="field")`  | catches ValueError | catches ValidationError (subclass) | Yes |
| `repr(creds)` contains `***`               | yes                | yes               | Yes         |

\* Exception type changes from `FrozenInstanceError` (dataclass) to `ValidationError` (Pydantic), but both prevent mutation.
\** Breaking change per FR-009 clarification — test code must use `model_copy(update=...)` instead.
