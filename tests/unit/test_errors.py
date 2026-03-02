"""Unit tests for AuthenticationError and TransientError."""

from whoop_mcp_server.auth.errors import AuthenticationError, TransientError


class TestAuthenticationError:
    def test_init_with_message(self):
        err = AuthenticationError("Token revoked")
        assert err.message == "Token revoked"
        assert err.status_code is None

    def test_init_with_status_code(self):
        err = AuthenticationError("Invalid grant", status_code=400)
        assert err.message == "Invalid grant"
        assert err.status_code == 400

    def test_str_contains_message(self):
        err = AuthenticationError("Token revoked", status_code=401)
        s = str(err)
        assert "Token revoked" in s

    def test_str_does_not_contain_secrets(self):
        err = AuthenticationError(
            "Failed to refresh token"
        )
        s = str(err)
        # Should not contain any token-like or secret-like values
        assert "eyJ" not in s
        assert "client_secret" not in s

    def test_is_exception(self):
        err = AuthenticationError("test")
        assert isinstance(err, Exception)


class TestTransientError:
    def test_init_with_all_fields(self):
        err = TransientError("Server error", status_code=503, attempts=3)
        assert err.message == "Server error"
        assert err.status_code == 503
        assert err.attempts == 3

    def test_init_defaults(self):
        err = TransientError("Network timeout")
        assert err.message == "Network timeout"
        assert err.status_code is None
        assert err.attempts == 0

    def test_str_contains_message(self):
        err = TransientError("Connection refused", status_code=503, attempts=3)
        s = str(err)
        assert "Connection refused" in s

    def test_str_does_not_contain_secrets(self):
        err = TransientError("Failed after retries")
        s = str(err)
        assert "eyJ" not in s
        assert "client_secret" not in s

    def test_is_exception(self):
        err = TransientError("test")
        assert isinstance(err, Exception)
