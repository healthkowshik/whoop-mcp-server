"""Integration test: full token lifecycle with mocked WHOOP endpoint."""

import asyncio
import json
import time

import httpx
import pytest

from whoop_mcp_server.auth.models import WhoopCredentials
from whoop_mcp_server.auth.token_manager import TokenManager
from whoop_mcp_server.auth.token_store import MemoryTokenStore

CREDENTIALS = WhoopCredentials(
    client_id="integration-client-id",
    client_secret="integration-client-secret",
)


class RequestTracker:
    """Track requests to the mock WHOOP token endpoint."""

    def __init__(self):
        self.requests: list[httpx.Request] = []
        self._call_count = 0
        self._exchange_response = {
            "access_token": "initial-access-token",
            "refresh_token": "initial-refresh-token",
            "expires_in": 3600,
            "scope": "offline read:recovery",
            "token_type": "bearer",
        }
        self._refresh_response = {
            "access_token": "refreshed-access-token",
            "refresh_token": "refreshed-refresh-token",
            "expires_in": 3600,
            "scope": "offline read:recovery",
            "token_type": "bearer",
        }

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        self._call_count += 1
        body = request.content.decode()

        if "grant_type=authorization_code" in body:
            return httpx.Response(
                200, content=json.dumps(self._exchange_response).encode()
            )
        elif "grant_type=refresh_token" in body:
            return httpx.Response(
                200, content=json.dumps(self._refresh_response).encode()
            )
        else:
            return httpx.Response(400, content=b'{"error": "unsupported_grant_type"}')

    @property
    def call_count(self) -> int:
        return self._call_count

    @property
    def refresh_count(self) -> int:
        return sum(
            1
            for r in self.requests
            if "grant_type=refresh_token" in r.content.decode()
        )

    @property
    def exchange_count(self) -> int:
        return sum(
            1
            for r in self.requests
            if "grant_type=authorization_code" in r.content.decode()
        )


class TestTokenRefreshFlow:
    """Full lifecycle: exchange → get_valid_token → refresh → concurrent refresh."""

    @pytest.mark.asyncio
    async def test_full_lifecycle(self):
        tracker = RequestTracker()
        transport = httpx.MockTransport(tracker.handler)
        client = httpx.AsyncClient(transport=transport)
        store = MemoryTokenStore()

        manager = TokenManager(
            credentials=CREDENTIALS,
            store=store,
            client=client,
            refresh_buffer_seconds=300,
        )

        # Step 1: Exchange authorization code
        await manager.exchange_code(
            code="test-auth-code",
            redirect_uri="https://app.example.com/callback",
        )
        assert tracker.exchange_count == 1
        assert tracker.refresh_count == 0

        # Step 2: get_valid_token returns the initial token (no refresh needed)
        token = await manager.get_valid_token()
        assert token == "initial-access-token"
        assert tracker.refresh_count == 0

        # Step 3: Simulate time passing — token now within refresh buffer
        # 1 min left but buffer is 5 min — triggers refresh
        manager._token_pair = manager._token_pair.model_copy(
            update={"expires_at": time.monotonic() + 60}
        )

        token = await manager.get_valid_token()
        assert token == "refreshed-access-token"
        assert tracker.refresh_count == 1

        # Step 4: Simulate token expired again for concurrent refresh test
        manager._token_pair = manager._token_pair.model_copy(
            update={"expires_at": time.monotonic() - 10}
        )

        # Step 5: Concurrent get_valid_token calls — should produce only 1 refresh
        results = await asyncio.gather(
            *[manager.get_valid_token() for _ in range(10)]
        )
        assert all(r == "refreshed-access-token" for r in results)
        assert tracker.refresh_count == 2  # Only 1 additional refresh (total 2)

        # Step 6: Verify token rotation — old tokens should not be reused
        assert manager._token_pair.access_token == "refreshed-access-token"
        assert manager._token_pair.refresh_token == "refreshed-refresh-token"

        # Step 7: Verify store was updated
        stored = await store.load()
        assert stored is not None
        assert stored["access_token"] == "refreshed-access-token"
        assert stored["refresh_token"] == "refreshed-refresh-token"

        # Cleanup
        await manager.aclose()
