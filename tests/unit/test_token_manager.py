"""Unit tests for TokenManager."""

import asyncio
import json
import time

import httpx
import pytest

from whoop_mcp_server.auth.errors import AuthenticationError, TransientError
from whoop_mcp_server.auth.models import WhoopCredentials
from whoop_mcp_server.auth.token_store import MemoryTokenStore

CREDENTIALS = WhoopCredentials(
    client_id="test-client-id",
    client_secret="test-client-secret",
)

TOKEN_RESPONSE = {
    "access_token": "new-access-token",
    "refresh_token": "new-refresh-token",
    "expires_in": 3600,
    "scope": "offline read:recovery read:sleep",
    "token_type": "bearer",
}


def make_mock_transport(
    response_data: dict | None = None,
    status_code: int = 200,
    *,
    error: Exception | None = None,
    request_log: list | None = None,
):
    """Create an httpx mock transport that returns a fixed response."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request_log is not None:
            request_log.append(request)
        if error is not None:
            raise error
        body = json.dumps(response_data or {})
        return httpx.Response(status_code, content=body.encode())

    return httpx.MockTransport(handler)


def make_client(transport: httpx.MockTransport) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=transport)


# ---------------------------------------------------------------------------
# US1: exchange_code tests
# ---------------------------------------------------------------------------


class TestExchangeCode:
    @pytest.mark.asyncio
    async def test_valid_code_stores_tokens(self):
        from whoop_mcp_server.auth.token_manager import TokenManager

        store = MemoryTokenStore()
        transport = make_mock_transport(TOKEN_RESPONSE)
        client = make_client(transport)

        manager = TokenManager(credentials=CREDENTIALS, store=store, client=client)
        await manager.exchange_code(
            code="valid-auth-code",
            redirect_uri="https://app.example.com/callback",
        )

        # Tokens should be loaded in the manager
        assert manager._token_pair is not None
        assert manager._token_pair.access_token == "new-access-token"
        assert manager._token_pair.refresh_token == "new-refresh-token"

        # Store should have been called
        stored = await store.load()
        assert stored is not None
        assert stored["access_token"] == "new-access-token"

    @pytest.mark.asyncio
    async def test_invalid_code_raises_auth_error(self):
        from whoop_mcp_server.auth.token_manager import TokenManager

        store = MemoryTokenStore()
        transport = make_mock_transport(
            {"error": "invalid_grant"}, status_code=400
        )
        client = make_client(transport)

        manager = TokenManager(credentials=CREDENTIALS, store=store, client=client)

        with pytest.raises(AuthenticationError) as exc_info:
            await manager.exchange_code(
                code="invalid-code",
                redirect_uri="https://app.example.com/callback",
            )
        assert exc_info.value.status_code == 400

        # No state change
        assert manager._token_pair is None
        stored = await store.load()
        assert stored is None

    @pytest.mark.asyncio
    async def test_network_error_raises_transient_error(self):
        from whoop_mcp_server.auth.token_manager import TokenManager

        transport = make_mock_transport(error=httpx.ConnectError("Connection refused"))
        client = make_client(transport)

        manager = TokenManager(credentials=CREDENTIALS, client=client)

        with pytest.raises(TransientError) as exc_info:
            await manager.exchange_code(
                code="valid-code",
                redirect_uri="https://app.example.com/callback",
            )
        assert exc_info.value.attempts == 3

    @pytest.mark.asyncio
    async def test_credentials_sent_as_post_body(self):
        from whoop_mcp_server.auth.token_manager import TokenManager

        request_log: list[httpx.Request] = []
        transport = make_mock_transport(TOKEN_RESPONSE, request_log=request_log)
        client = make_client(transport)

        manager = TokenManager(credentials=CREDENTIALS, client=client)
        await manager.exchange_code(
            code="auth-code",
            redirect_uri="https://app.example.com/callback",
        )

        assert len(request_log) == 1
        req = request_log[0]
        body = req.content.decode()

        # Credentials in body, not in Authorization header
        assert "client_id=test-client-id" in body
        assert "client_secret=test-client-secret" in body
        assert req.headers.get("authorization") is None

    @pytest.mark.asyncio
    async def test_content_type_is_form_urlencoded(self):
        from whoop_mcp_server.auth.token_manager import TokenManager

        request_log: list[httpx.Request] = []
        transport = make_mock_transport(TOKEN_RESPONSE, request_log=request_log)
        client = make_client(transport)

        manager = TokenManager(credentials=CREDENTIALS, client=client)
        await manager.exchange_code(
            code="auth-code",
            redirect_uri="https://app.example.com/callback",
        )

        req = request_log[0]
        assert "application/x-www-form-urlencoded" in req.headers.get(
            "content-type", ""
        )


# ---------------------------------------------------------------------------
# US2: get_valid_token tests
# ---------------------------------------------------------------------------

REFRESH_RESPONSE = {
    "access_token": "refreshed-access-token",
    "refresh_token": "refreshed-refresh-token",
    "expires_in": 3600,
    "scope": "offline read:recovery read:sleep",
    "token_type": "bearer",
}


class TestGetValidToken:
    @pytest.mark.asyncio
    async def test_valid_token_returned_without_network_call(self):
        from whoop_mcp_server.auth.token_manager import TokenManager

        request_log: list[httpx.Request] = []
        transport = make_mock_transport(REFRESH_RESPONSE, request_log=request_log)
        client = make_client(transport)

        manager = TokenManager.from_tokens(
            CREDENTIALS,
            access_token="valid-access-token",
            refresh_token="valid-refresh-token",
            expires_in=3600,
            client=client,
        )
        token = await manager.get_valid_token()

        assert token == "valid-access-token"
        assert len(request_log) == 0  # No network call

    @pytest.mark.asyncio
    async def test_token_within_buffer_triggers_refresh(self):
        from whoop_mcp_server.auth.token_manager import TokenManager

        request_log: list[httpx.Request] = []
        transport = make_mock_transport(REFRESH_RESPONSE, request_log=request_log)
        client = make_client(transport)

        # Token expires in 60 seconds, but buffer is 300 seconds (default)
        manager = TokenManager.from_tokens(
            CREDENTIALS,
            access_token="expiring-soon-token",
            refresh_token="valid-refresh-token",
            expires_in=60,
            client=client,
        )
        token = await manager.get_valid_token()

        assert token == "refreshed-access-token"
        assert len(request_log) == 1  # One refresh request

    @pytest.mark.asyncio
    async def test_expired_token_triggers_refresh(self):
        from whoop_mcp_server.auth.token_manager import TokenManager

        transport = make_mock_transport(REFRESH_RESPONSE)
        client = make_client(transport)

        # Token already expired (expires_in = -10 means already past)
        manager = TokenManager.from_tokens(
            CREDENTIALS,
            access_token="expired-token",
            refresh_token="valid-refresh-token",
            expires_in=-10,
            client=client,
            refresh_buffer_seconds=0,
        )
        # Fix: manually set expires_at to the past
        manager._token_pair.expires_at = time.monotonic() - 10

        token = await manager.get_valid_token()
        assert token == "refreshed-access-token"

    @pytest.mark.asyncio
    async def test_no_tokens_raises_auth_error(self):
        from whoop_mcp_server.auth.token_manager import TokenManager

        transport = make_mock_transport(REFRESH_RESPONSE)
        client = make_client(transport)

        manager = TokenManager(credentials=CREDENTIALS, client=client)

        with pytest.raises(AuthenticationError, match="(?i)not authenticated"):
            await manager.get_valid_token()

    @pytest.mark.asyncio
    async def test_refresh_fails_with_revoked_token(self):
        from whoop_mcp_server.auth.token_manager import TokenManager

        transport = make_mock_transport(
            {"error": "invalid_grant"}, status_code=401
        )
        client = make_client(transport)

        manager = TokenManager.from_tokens(
            CREDENTIALS,
            access_token="expired-token",
            refresh_token="revoked-refresh-token",
            expires_in=1,
            client=client,
            refresh_buffer_seconds=0,
        )
        manager._token_pair.expires_at = time.monotonic() - 10

        with pytest.raises(AuthenticationError) as exc_info:
            await manager.get_valid_token()
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_fails_after_retries_raises_transient(self):
        from whoop_mcp_server.auth.token_manager import TokenManager

        transport = make_mock_transport(
            {"error": "server_error"}, status_code=503
        )
        client = make_client(transport)

        manager = TokenManager.from_tokens(
            CREDENTIALS,
            access_token="expired-token",
            refresh_token="valid-refresh-token",
            expires_in=1,
            client=client,
            refresh_buffer_seconds=0,
        )
        manager._token_pair.expires_at = time.monotonic() - 10

        with pytest.raises(TransientError) as exc_info:
            await manager.get_valid_token()
        assert exc_info.value.attempts == 3

    @pytest.mark.asyncio
    async def test_store_save_called_after_refresh(self):
        from whoop_mcp_server.auth.token_manager import TokenManager

        store = MemoryTokenStore()
        transport = make_mock_transport(REFRESH_RESPONSE)
        client = make_client(transport)

        manager = TokenManager.from_tokens(
            CREDENTIALS,
            access_token="expired-token",
            refresh_token="valid-refresh-token",
            expires_in=1,
            store=store,
            client=client,
            refresh_buffer_seconds=0,
        )
        manager._token_pair.expires_at = time.monotonic() - 10

        await manager.get_valid_token()

        stored = await store.load()
        assert stored is not None
        assert stored["access_token"] == "refreshed-access-token"
        assert stored["refresh_token"] == "refreshed-refresh-token"

    @pytest.mark.asyncio
    async def test_refresh_sends_credentials_in_post_body_with_offline_scope(self):
        from whoop_mcp_server.auth.token_manager import TokenManager

        request_log: list[httpx.Request] = []
        transport = make_mock_transport(REFRESH_RESPONSE, request_log=request_log)
        client = make_client(transport)

        manager = TokenManager.from_tokens(
            CREDENTIALS,
            access_token="expired-token",
            refresh_token="old-refresh-token",
            expires_in=1,
            client=client,
            refresh_buffer_seconds=0,
        )
        manager._token_pair.expires_at = time.monotonic() - 10

        await manager.get_valid_token()

        assert len(request_log) == 1
        body = request_log[0].content.decode()
        assert "grant_type=refresh_token" in body
        assert "client_id=test-client-id" in body
        assert "client_secret=test-client-secret" in body
        assert "scope=offline" in body

    @pytest.mark.asyncio
    async def test_refresh_response_missing_refresh_token_raises_error(self):
        from whoop_mcp_server.auth.token_manager import TokenManager

        # Response missing refresh_token
        bad_response = {
            "access_token": "new-access",
            "expires_in": 3600,
            "scope": "offline",
            "token_type": "bearer",
        }
        transport = make_mock_transport(bad_response)
        client = make_client(transport)

        manager = TokenManager.from_tokens(
            CREDENTIALS,
            access_token="expired-token",
            refresh_token="old-refresh-token",
            expires_in=1,
            client=client,
            refresh_buffer_seconds=0,
        )
        manager._token_pair.expires_at = time.monotonic() - 10

        with pytest.raises(AuthenticationError, match="refresh_token"):
            await manager.get_valid_token()


# ---------------------------------------------------------------------------
# US3: concurrent refresh safety tests
# ---------------------------------------------------------------------------


class TestConcurrentRefresh:
    @pytest.mark.asyncio
    async def test_concurrent_calls_produce_single_refresh(self):
        from whoop_mcp_server.auth.token_manager import TokenManager

        request_log: list[httpx.Request] = []
        transport = make_mock_transport(REFRESH_RESPONSE, request_log=request_log)
        client = make_client(transport)

        manager = TokenManager.from_tokens(
            CREDENTIALS,
            access_token="expired-token",
            refresh_token="valid-refresh-token",
            expires_in=1,
            client=client,
            refresh_buffer_seconds=0,
        )
        manager._token_pair.expires_at = time.monotonic() - 10

        # Launch 10 concurrent get_valid_token calls
        results = await asyncio.gather(
            *[manager.get_valid_token() for _ in range(10)]
        )

        # All should get the same new token
        assert all(r == "refreshed-access-token" for r in results)
        # Only 1 refresh request should have been made
        assert len(request_log) == 1

    @pytest.mark.asyncio
    async def test_concurrent_callers_receive_same_token(self):
        from whoop_mcp_server.auth.token_manager import TokenManager

        transport = make_mock_transport(REFRESH_RESPONSE)
        client = make_client(transport)

        manager = TokenManager.from_tokens(
            CREDENTIALS,
            access_token="expired-token",
            refresh_token="valid-refresh-token",
            expires_in=1,
            client=client,
            refresh_buffer_seconds=0,
        )
        manager._token_pair.expires_at = time.monotonic() - 10

        results = await asyncio.gather(
            *[manager.get_valid_token() for _ in range(10)]
        )

        # All results should be identical
        assert len(set(results)) == 1
        assert results[0] == "refreshed-access-token"

    @pytest.mark.asyncio
    async def test_concurrent_refresh_failure_raises_to_all_waiters(self):
        from whoop_mcp_server.auth.token_manager import TokenManager

        transport = make_mock_transport(
            {"error": "invalid_grant"}, status_code=401
        )
        client = make_client(transport)

        manager = TokenManager.from_tokens(
            CREDENTIALS,
            access_token="expired-token",
            refresh_token="revoked-token",
            expires_in=1,
            client=client,
            refresh_buffer_seconds=0,
        )
        manager._token_pair.expires_at = time.monotonic() - 10

        results = await asyncio.gather(
            *[manager.get_valid_token() for _ in range(5)],
            return_exceptions=True,
        )

        # All should get AuthenticationError
        for result in results:
            assert isinstance(result, AuthenticationError)


# ---------------------------------------------------------------------------
# US4: from_tokens and store loading tests
# ---------------------------------------------------------------------------


class TestFromTokens:
    @pytest.mark.asyncio
    async def test_from_tokens_creates_valid_manager(self):
        from whoop_mcp_server.auth.token_manager import TokenManager

        request_log: list[httpx.Request] = []
        transport = make_mock_transport(REFRESH_RESPONSE, request_log=request_log)
        client = make_client(transport)

        manager = TokenManager.from_tokens(
            CREDENTIALS,
            access_token="preloaded-access",
            refresh_token="preloaded-refresh",
            expires_in=3600,
            client=client,
        )
        token = await manager.get_valid_token()

        assert token == "preloaded-access"
        assert len(request_log) == 0  # No network call

    @pytest.mark.asyncio
    async def test_from_tokens_expired_triggers_refresh(self):
        from whoop_mcp_server.auth.token_manager import TokenManager

        transport = make_mock_transport(REFRESH_RESPONSE)
        client = make_client(transport)

        manager = TokenManager.from_tokens(
            CREDENTIALS,
            access_token="expired-preloaded",
            refresh_token="preloaded-refresh",
            expires_in=1,
            client=client,
            refresh_buffer_seconds=0,
        )
        manager._token_pair.expires_at = time.monotonic() - 10

        token = await manager.get_valid_token()
        assert token == "refreshed-access-token"

    @pytest.mark.asyncio
    async def test_store_loading_on_first_get_valid_token(self):
        from whoop_mcp_server.auth.token_manager import TokenManager

        store = MemoryTokenStore()
        # Pre-populate the store with token data
        from datetime import datetime, timezone
        future_utc = datetime.now(timezone.utc).timestamp() + 3600
        dt = datetime.fromtimestamp(future_utc, tz=timezone.utc)
        await store.save({
            "access_token": "stored-access",
            "refresh_token": "stored-refresh",
            "expires_at_utc": dt.isoformat(),
            "scope": "offline",
            "token_type": "bearer",
        })

        request_log: list[httpx.Request] = []
        transport = make_mock_transport(REFRESH_RESPONSE, request_log=request_log)
        client = make_client(transport)

        manager = TokenManager(
            credentials=CREDENTIALS,
            store=store,
            client=client,
        )

        # Before first call, no tokens loaded
        assert manager._token_pair is None

        # First get_valid_token should lazy-load from store
        token = await manager.get_valid_token()
        assert token == "stored-access"
        assert len(request_log) == 0  # No refresh needed

    @pytest.mark.asyncio
    async def test_empty_store_starts_unauthenticated(self):
        from whoop_mcp_server.auth.token_manager import TokenManager

        store = MemoryTokenStore()  # Empty
        transport = make_mock_transport(REFRESH_RESPONSE)
        client = make_client(transport)

        manager = TokenManager(
            credentials=CREDENTIALS,
            store=store,
            client=client,
        )

        with pytest.raises(AuthenticationError, match="(?i)not authenticated"):
            await manager.get_valid_token()

    @pytest.mark.asyncio
    async def test_monotonic_utc_round_trip(self):
        from whoop_mcp_server.auth.token_manager import TokenManager

        store = MemoryTokenStore()
        transport = make_mock_transport(TOKEN_RESPONSE)
        client = make_client(transport)

        # Exchange to get tokens saved to store
        manager = TokenManager(
            credentials=CREDENTIALS,
            store=store,
            client=client,
        )
        await manager.exchange_code(
            code="test-code",
            redirect_uri="https://app.example.com/callback",
        )

        # Verify store has ISO 8601 UTC timestamp
        stored = await store.load()
        assert "expires_at_utc" in stored
        assert "T" in stored["expires_at_utc"]  # ISO format

        # Create a new manager that loads from the same store
        request_log: list[httpx.Request] = []
        transport2 = make_mock_transport(REFRESH_RESPONSE, request_log=request_log)
        client2 = make_client(transport2)

        manager2 = TokenManager(
            credentials=CREDENTIALS,
            store=store,
            client=client2,
        )
        token = await manager2.get_valid_token()

        # Should load the stored token (still valid, no refresh)
        assert token == "new-access-token"
        assert len(request_log) == 0
