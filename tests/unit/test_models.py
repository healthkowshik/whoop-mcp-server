"""Unit tests for WhoopCredentials, TokenPair, and TokenResponse models."""

import time

import pytest

from whoop_mcp_server.auth.models import TokenPair, TokenResponse, WhoopCredentials


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

    def test_validation_empty_client_id(self):
        with pytest.raises(ValueError, match="client_id"):
            WhoopCredentials(client_id="", client_secret="my-secret")

    def test_validation_empty_client_secret(self):
        with pytest.raises(ValueError, match="client_secret"):
            WhoopCredentials(client_id="my-id", client_secret="")

    def test_immutability(self):
        creds = WhoopCredentials(
            client_id="my-client-id",
            client_secret="my-client-secret",
        )
        with pytest.raises(Exception):
            creds.client_id = "new-id"

    def test_fields_are_plain_str(self):
        creds = WhoopCredentials(
            client_id="my-client-id",
            client_secret="my-client-secret",
        )
        assert type(creds.client_id) is str
        assert type(creds.client_secret) is str


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

    def test_validation_zero_expires_at(self):
        with pytest.raises(ValueError, match="expires_at"):
            TokenPair(
                access_token="access-abc",
                refresh_token="refresh-xyz",
                expires_at=0.0,
                scope="offline",
                token_type="bearer",
            )

    def test_immutability(self):
        tp = TokenPair(
            access_token="access-abc",
            refresh_token="refresh-xyz",
            expires_at=time.monotonic() + 3600,
            scope="offline",
            token_type="bearer",
        )
        with pytest.raises(Exception):
            tp.expires_at = 0.0

    def test_model_copy_creates_new_instance(self):
        tp = TokenPair(
            access_token="access-abc",
            refresh_token="refresh-xyz",
            expires_at=time.monotonic() + 3600,
            scope="offline",
            token_type="bearer",
        )
        new_expires = time.monotonic() + 60
        tp2 = tp.model_copy(update={"expires_at": new_expires})
        assert tp2.expires_at == new_expires
        assert tp2.access_token == tp.access_token
        assert tp2 is not tp

    def test_extra_kwargs_ignored(self):
        tp = TokenPair(
            access_token="access-abc",
            refresh_token="refresh-xyz",
            expires_at=time.monotonic() + 3600,
            scope="offline",
            token_type="bearer",
            unknown_field="should be ignored",
        )
        assert tp.access_token == "access-abc"
        assert not hasattr(tp, "unknown_field")


class TestTokenPairSerialization:
    def test_round_trip_preserves_fields(self):
        tp = TokenPair(
            access_token="access-abc",
            refresh_token="refresh-xyz",
            expires_at=time.monotonic() + 3600,
            scope="offline read:recovery",
            token_type="bearer",
        )
        store_dict = tp.to_store_dict()
        restored = TokenPair.from_store_dict(store_dict)

        assert restored.access_token == tp.access_token
        assert restored.refresh_token == tp.refresh_token
        assert restored.scope == tp.scope
        assert restored.token_type == tp.token_type
        assert abs(restored.expires_at - tp.expires_at) < 1.0

    def test_round_trip_near_expiry(self):
        tp = TokenPair(
            access_token="access-abc",
            refresh_token="refresh-xyz",
            expires_at=time.monotonic() + 1,
            scope="offline",
            token_type="bearer",
        )
        store_dict = tp.to_store_dict()
        restored = TokenPair.from_store_dict(store_dict)
        assert abs(restored.expires_at - tp.expires_at) < 1.0

    def test_round_trip_far_future(self):
        tp = TokenPair(
            access_token="access-abc",
            refresh_token="refresh-xyz",
            expires_at=time.monotonic() + 30 * 86400,
            scope="offline",
            token_type="bearer",
        )
        store_dict = tp.to_store_dict()
        restored = TokenPair.from_store_dict(store_dict)
        assert abs(restored.expires_at - tp.expires_at) < 1.0

    def test_round_trip_minimal_scope(self):
        tp = TokenPair(
            access_token="access-abc",
            refresh_token="refresh-xyz",
            expires_at=time.monotonic() + 3600,
            scope="",
            token_type="bearer",
        )
        store_dict = tp.to_store_dict()
        restored = TokenPair.from_store_dict(store_dict)
        assert restored.scope == ""

    def test_round_trip_full_scope(self):
        tp = TokenPair(
            access_token="access-abc",
            refresh_token="refresh-xyz",
            expires_at=time.monotonic() + 3600,
            scope="offline read:recovery read:sleep",
            token_type="bearer",
        )
        store_dict = tp.to_store_dict()
        restored = TokenPair.from_store_dict(store_dict)
        assert restored.scope == "offline read:recovery read:sleep"

    def test_from_store_dict_ignores_extra_fields(self):
        store_dict = {
            "access_token": "access-abc",
            "refresh_token": "refresh-xyz",
            "expires_at_utc": "2099-01-01T00:00:00+00:00",
            "scope": "offline",
            "token_type": "bearer",
            "new_field_v2": "should be ignored",
        }
        tp = TokenPair.from_store_dict(store_dict)
        assert tp.access_token == "access-abc"
        assert not hasattr(tp, "new_field_v2")

    def test_from_store_dict_missing_expires_at_utc_treats_as_expired(self):
        store_dict = {
            "access_token": "access-abc",
            "refresh_token": "refresh-xyz",
            "scope": "offline",
            "token_type": "bearer",
        }
        tp = TokenPair.from_store_dict(store_dict)
        assert tp.is_expired()

    def test_from_store_dict_missing_required_field_raises(self):
        store_dict = {
            "refresh_token": "refresh-xyz",
            "expires_at_utc": "2099-01-01T00:00:00+00:00",
            "scope": "offline",
            "token_type": "bearer",
        }
        with pytest.raises((KeyError, ValueError)):
            TokenPair.from_store_dict(store_dict)

    def test_to_store_dict_output_keys(self):
        tp = TokenPair(
            access_token="access-abc",
            refresh_token="refresh-xyz",
            expires_at=time.monotonic() + 3600,
            scope="offline",
            token_type="bearer",
        )
        store_dict = tp.to_store_dict()
        expected_keys = {
            "access_token",
            "refresh_token",
            "expires_at_utc",
            "scope",
            "token_type",
        }
        assert set(store_dict.keys()) == expected_keys
        assert "T" in store_dict["expires_at_utc"]  # ISO format


class TestTokenResponse:
    def test_valid_response(self):
        resp = TokenResponse(
            access_token="access-abc",
            refresh_token="refresh-xyz",
            expires_in=3600,
            scope="offline read:recovery",
            token_type="bearer",
        )
        assert resp.access_token == "access-abc"
        assert resp.refresh_token == "refresh-xyz"
        assert resp.expires_in == 3600
        assert resp.scope == "offline read:recovery"
        assert resp.token_type == "bearer"

    def test_missing_access_token_raises(self):
        with pytest.raises(ValueError, match="access_token"):
            TokenResponse(
                refresh_token="refresh-xyz",
                expires_in=3600,
            )

    def test_missing_refresh_token_raises(self):
        with pytest.raises(ValueError, match="refresh_token"):
            TokenResponse(
                access_token="access-abc",
                expires_in=3600,
            )

    def test_expires_in_string_coerced_to_int(self):
        resp = TokenResponse(
            access_token="access-abc",
            refresh_token="refresh-xyz",
            expires_in="3600",
            scope="offline",
            token_type="bearer",
        )
        assert resp.expires_in == 3600
        assert type(resp.expires_in) is int

    def test_extra_fields_ignored(self):
        resp = TokenResponse(
            access_token="access-abc",
            refresh_token="refresh-xyz",
            expires_in=3600,
            scope="offline",
            token_type="bearer",
            new_api_field="ignored",
        )
        assert resp.access_token == "access-abc"
        assert not hasattr(resp, "new_api_field")

    def test_to_token_pair_creates_valid_pair(self):
        resp = TokenResponse(
            access_token="access-abc",
            refresh_token="refresh-xyz",
            expires_in=3600,
            scope="offline read:recovery",
            token_type="bearer",
        )
        before = time.monotonic()
        tp = resp.to_token_pair()
        after = time.monotonic()

        assert tp.access_token == "access-abc"
        assert tp.refresh_token == "refresh-xyz"
        assert tp.scope == "offline read:recovery"
        assert tp.token_type == "bearer"
        assert before + 3600 <= tp.expires_at <= after + 3600

    def test_to_token_pair_fields_match(self):
        resp = TokenResponse(
            access_token="access-abc",
            refresh_token="refresh-xyz",
            expires_in=100,
            scope="offline",
            token_type="bearer",
        )
        tp = resp.to_token_pair()
        assert tp.access_token == resp.access_token
        assert tp.refresh_token == resp.refresh_token
        assert tp.scope == resp.scope
        assert tp.token_type == resp.token_type

    def test_default_scope_empty_string(self):
        resp = TokenResponse(
            access_token="access-abc",
            refresh_token="refresh-xyz",
            expires_in=3600,
        )
        assert resp.scope == ""

    def test_default_token_type_bearer(self):
        resp = TokenResponse(
            access_token="access-abc",
            refresh_token="refresh-xyz",
            expires_in=3600,
        )
        assert resp.token_type == "bearer"
