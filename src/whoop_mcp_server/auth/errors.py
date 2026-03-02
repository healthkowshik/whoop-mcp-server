"""Error types for WHOOP OAuth token management."""

from __future__ import annotations


class AuthenticationError(Exception):
    """Permanent authentication failure requiring re-authentication.

    Raised when tokens are revoked, credentials are invalid, or the
    authorization code is rejected. The caller must re-authenticate
    through the browser-based OAuth flow.

    Attributes:
        message: Human-readable description (never contains secrets).
        status_code: HTTP status code from WHOOP, if available.
    """

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)

    def __str__(self) -> str:
        if self.status_code is not None:
            return f"AuthenticationError({self.status_code}): {self.message}"
        return f"AuthenticationError: {self.message}"


class TransientError(Exception):
    """Temporary failure that may succeed on retry.

    Raised after all retry attempts are exhausted for transient failures
    like network timeouts or server errors.

    Attributes:
        message: Human-readable description (never contains secrets).
        status_code: HTTP status code from WHOOP, if available.
        attempts: Number of retry attempts made before raising.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        attempts: int = 0,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.attempts = attempts
        super().__init__(message)

    def __str__(self) -> str:
        parts = ["TransientError"]
        if self.status_code is not None:
            parts[0] += f"({self.status_code})"
        parts.append(f": {self.message}")
        if self.attempts > 0:
            parts.append(f" (after {self.attempts} attempts)")
        return "".join(parts)
