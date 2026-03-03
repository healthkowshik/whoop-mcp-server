"""WHOOP OAuth token manager with automatic refresh and concurrent safety."""

from __future__ import annotations

import asyncio
import time

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from whoop_mcp_server.auth.errors import AuthenticationError, TransientError
from whoop_mcp_server.auth.models import TokenPair, TokenResponse, WhoopCredentials
from whoop_mcp_server.auth.token_store import MemoryTokenStore, TokenStore

WHOOP_TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"


def _is_retryable_status(exc: BaseException) -> bool:
    """Check if an httpx.HTTPStatusError has a retryable (5xx) status code."""
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    return False


class _RetryableHTTPError(Exception):
    """Wrapper to signal a retryable HTTP error to tenacity."""

    def __init__(self, response: httpx.Response) -> None:
        self.response = response
        super().__init__(f"HTTP {response.status_code}")


class TokenManager:
    """Manages WHOOP OAuth tokens with automatic refresh and concurrent safety.

    The manager exchanges authorization codes for tokens, transparently
    refreshes expired tokens, and ensures only one refresh happens at a
    time under concurrent access.
    """

    def __init__(
        self,
        credentials: WhoopCredentials,
        *,
        store: TokenStore | None = None,
        client: httpx.AsyncClient | None = None,
        refresh_buffer_seconds: int = 300,
    ) -> None:
        self._credentials = credentials
        self._store: TokenStore = store if store is not None else MemoryTokenStore()
        self._refresh_buffer_seconds = refresh_buffer_seconds
        self._token_pair: TokenPair | None = None

        # httpx client lifecycle
        if client is not None:
            self._client = client
            self._owns_client = False
        else:
            self._client = httpx.AsyncClient()
            self._owns_client = True

        # Concurrency safety
        self._refresh_lock = asyncio.Lock()

        # Lazy store loading flag (for US4)
        self._store_loaded = False

    @classmethod
    def from_tokens(
        cls,
        credentials: WhoopCredentials,
        *,
        access_token: str,
        refresh_token: str,
        expires_in: int,
        scope: str = "offline",
        token_type: str = "bearer",
        **kwargs,
    ) -> TokenManager:
        """Create a TokenManager pre-loaded with existing tokens."""
        manager = cls(credentials=credentials, **kwargs)
        manager._token_pair = TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=time.monotonic() + expires_in,
            scope=scope,
            token_type=token_type,
        )
        manager._store_loaded = True  # No need to load from store
        return manager

    async def get_valid_token(self) -> str:
        """Return a valid access token, refreshing transparently if needed.

        Uses a double-check locking pattern to ensure exactly one refresh
        under concurrent access.

        Raises:
            AuthenticationError: If no tokens are loaded or refresh fails
                due to revoked tokens.
            TransientError: If refresh fails after retries due to
                transient errors.
        """
        # Lazy-load from store on first call (US4)
        if not self._store_loaded:
            self._store_loaded = True
            await self._load_from_store()

        if self._token_pair is None:
            raise AuthenticationError("Not authenticated: no tokens loaded")

        # First check (without lock) — fast path for valid tokens
        if not self._token_pair.is_expired(
            buffer_seconds=self._refresh_buffer_seconds
        ):
            return self._token_pair.access_token

        # Token needs refresh — acquire lock
        async with self._refresh_lock:
            # Second check (with lock) — another coroutine may have refreshed
            if not self._token_pair.is_expired(
                buffer_seconds=self._refresh_buffer_seconds
            ):
                return self._token_pair.access_token

            await self._refresh_token()

        return self._token_pair.access_token

    async def _refresh_token(self) -> None:
        """Refresh the access token using the current refresh token."""
        if self._token_pair is None:
            raise AuthenticationError("Not authenticated: no tokens to refresh")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self._token_pair.refresh_token,
            "client_id": self._credentials.client_id,
            "client_secret": self._credentials.client_secret,
            "scope": "offline",
        }
        response = await self._post_token_request(data)
        token_data = response.json()

        # Validate that refresh_token is present (WHOOP contract with offline scope)
        if "refresh_token" not in token_data or not token_data["refresh_token"]:
            raise AuthenticationError(
                "Refresh response missing refresh_token — "
                "re-authentication required",
            )

        self._token_pair = self._parse_token_response(token_data)
        await self._save_to_store()

    async def _load_from_store(self) -> None:
        """Load tokens from the store, if available."""
        data = await self._store.load()
        if data is None:
            return

        try:
            self._token_pair = TokenPair.from_store_dict(data)
        except (KeyError, ValueError):
            # Corrupted store data — start unauthenticated
            self._token_pair = None

    async def exchange_code(self, code: str, redirect_uri: str) -> None:
        """Exchange an authorization code for tokens.

        Raises:
            AuthenticationError: If the code is invalid (4xx response).
            TransientError: If the request fails after retries.
        """
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self._credentials.client_id,
            "client_secret": self._credentials.client_secret,
        }
        response = await self._post_token_request(data)
        token_data = response.json()
        self._token_pair = self._parse_token_response(token_data)
        await self._save_to_store()

    async def _post_token_request(self, data: dict) -> httpx.Response:
        """POST to the WHOOP token endpoint with retry logic.

        Retries on TransportError and 5xx responses (3 attempts, 1s/2s/4s backoff).
        Fails immediately on 4xx (non-retryable).
        """
        try:
            return await self._post_with_retry(data)
        except _RetryableHTTPError as exc:
            raise TransientError(
                f"Token endpoint returned {exc.response.status_code}",
                status_code=exc.response.status_code,
                attempts=3,
            ) from exc
        except httpx.TransportError as exc:
            raise TransientError(
                f"Token endpoint unreachable: {type(exc).__name__}",
                attempts=3,
            ) from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type((httpx.TransportError, _RetryableHTTPError)),
        reraise=True,
    )
    async def _post_with_retry(self, data: dict) -> httpx.Response:
        """Execute the POST request with tenacity retry."""
        response = await self._client.post(
            WHOOP_TOKEN_URL,
            data=data,
        )
        if response.status_code >= 500:
            raise _RetryableHTTPError(response)
        if response.status_code >= 400:
            raise AuthenticationError(
                f"Token request failed: {response.status_code}",
                status_code=response.status_code,
            )
        return response

    def _parse_token_response(self, data: dict) -> TokenPair:
        """Parse a WHOOP token endpoint response into a TokenPair."""
        return TokenResponse.model_validate(data).to_token_pair()

    async def _save_to_store(self) -> None:
        """Persist the current token pair to the store."""
        if self._token_pair is None:
            return
        await self._store.save(self._token_pair.to_store_dict())

    async def aclose(self) -> None:
        """Close the internally-managed httpx client.

        No-op if the client was injected externally.
        """
        if self._owns_client:
            await self._client.aclose()
