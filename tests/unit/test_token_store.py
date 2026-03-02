"""Unit tests for MemoryTokenStore."""

import pytest

from whoop_mcp_server.auth.token_store import MemoryTokenStore, TokenStore


class TestMemoryTokenStore:
    @pytest.mark.asyncio
    async def test_load_returns_none_when_empty(self):
        store = MemoryTokenStore()
        result = await store.load()
        assert result is None

    @pytest.mark.asyncio
    async def test_save_and_load_round_trip(self):
        store = MemoryTokenStore()
        data = {
            "access_token": "abc",
            "refresh_token": "xyz",
            "expires_at_utc": "2026-03-02T12:00:00+00:00",
            "scope": "offline",
            "token_type": "bearer",
        }
        await store.save(data)
        result = await store.load()
        assert result == data

    @pytest.mark.asyncio
    async def test_save_overwrites_previous(self):
        store = MemoryTokenStore()
        await store.save({"access_token": "first"})
        await store.save({"access_token": "second"})
        result = await store.load()
        assert result == {"access_token": "second"}

    def test_satisfies_token_store_protocol(self):
        store = MemoryTokenStore()
        assert isinstance(store, TokenStore)
