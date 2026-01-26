import pytest

from app.services.whoop_client import MAX_LIMIT, WhoopClient


class TestWhoopClient:
    def test_max_limit_enforced(self):
        client = WhoopClient()
        assert MAX_LIMIT == 1000

    def test_headers_include_auth(self):
        client = WhoopClient()
        assert "Authorization" in client.headers
        assert client.headers["Authorization"].startswith("Bearer ")
