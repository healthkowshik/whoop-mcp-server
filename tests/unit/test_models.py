"""Unit tests for WhoopCredentials and TokenPair models."""

import time

import pytest

from whoop_mcp_server.auth.models import TokenPair, WhoopCredentials


class TestWhoopCredentials:
    def test_init(self):
        creds = WhoopCredentials(
            client_id="my-client-id",
            client_secret="my-client-secret",
        )
        assert creds.client_id == "my-client-id"
        assert creds.client_secret == "my-client-secret"

    def test_repr_redacts_secret(self):
        creds = WhoopCredentials(
            client_id="my-client-id",
            client_secret="super-secret-value",
        )
        r = repr(creds)
        assert "my-client-id" in r
        assert "super-secret-value" not in r
        assert "***" in r

    def test_str_redacts_secret(self):
        creds = WhoopCredentials(
            client_id="my-client-id",
            client_secret="super-secret-value",
        )
        s = str(creds)
        assert "super-secret-value" not in s


class TestTokenPair:
    def test_init(self):
        tp = TokenPair(
            access_token="access-abc",
            refresh_token="refresh-xyz",
            expires_at=time.monotonic() + 3600,
            scope="offline read:recovery",
            token_type="bearer",
        )
        assert tp.access_token == "access-abc"
        assert tp.refresh_token == "refresh-xyz"
        assert tp.scope == "offline read:recovery"
        assert tp.token_type == "bearer"

    def test_validation_empty_access_token(self):
        with pytest.raises(ValueError, match="access_token"):
            TokenPair(
                access_token="",
                refresh_token="refresh-xyz",
                expires_at=time.monotonic() + 3600,
                scope="offline",
                token_type="bearer",
            )

    def test_validation_empty_refresh_token(self):
        with pytest.raises(ValueError, match="refresh_token"):
            TokenPair(
                access_token="access-abc",
                refresh_token="",
                expires_at=time.monotonic() + 3600,
                scope="offline",
                token_type="bearer",
            )

    def test_validation_non_positive_expires_at(self):
        with pytest.raises(ValueError, match="expires_at"):
            TokenPair(
                access_token="access-abc",
                refresh_token="refresh-xyz",
                expires_at=-1.0,
                scope="offline",
                token_type="bearer",
            )

    def test_repr_redacts_tokens(self):
        tp = TokenPair(
            access_token="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.long_token_value",
            refresh_token="dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4.long_refresh_value",
            expires_at=time.monotonic() + 3600,
            scope="offline",
            token_type="bearer",
        )
        r = repr(tp)
        assert "long_token_value" not in r
        assert "long_refresh_value" not in r
        assert "***" in r

    def test_is_expired_false_when_valid(self):
        tp = TokenPair(
            access_token="access-abc",
            refresh_token="refresh-xyz",
            expires_at=time.monotonic() + 3600,
            scope="offline",
            token_type="bearer",
        )
        assert not tp.is_expired()

    def test_is_expired_true_when_past(self):
        tp = TokenPair(
            access_token="access-abc",
            refresh_token="refresh-xyz",
            expires_at=time.monotonic() - 10,
            scope="offline",
            token_type="bearer",
        )
        assert tp.is_expired()

    def test_is_expired_with_buffer(self):
        tp = TokenPair(
            access_token="access-abc",
            refresh_token="refresh-xyz",
            expires_at=time.monotonic() + 100,
            scope="offline",
            token_type="bearer",
        )
        # Not expired with default buffer
        assert not tp.is_expired(buffer_seconds=0)
        # Expired when buffer is larger than remaining time
        assert tp.is_expired(buffer_seconds=200)
