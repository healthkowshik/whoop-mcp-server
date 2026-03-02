"""Core data models for WHOOP OAuth token management."""

from __future__ import annotations

import time
from dataclasses import dataclass


def _mask(value: str, visible: int = 6) -> str:
    """Mask a secret string, showing only the first `visible` characters."""
    if len(value) <= visible:
        return "***"
    return value[:visible] + "***"


@dataclass(frozen=True)
class WhoopCredentials:
    """WHOOP OAuth client credentials.

    The client_secret is always masked in repr/str output.
    """

    client_id: str
    client_secret: str

    def __repr__(self) -> str:
        return (
            f"WhoopCredentials(client_id={self.client_id!r}, client_secret='***')"
        )

    def __str__(self) -> str:
        return self.__repr__()


@dataclass
class TokenPair:
    """Represents the current authentication state.

    Attributes:
        access_token: Bearer token for WHOOP API requests.
        refresh_token: Token used to obtain a new access token.
        expires_at: time.monotonic() timestamp after which the access token is expired.
        scope: Space-delimited scope string from the token response.
        token_type: Always "bearer" for WHOOP.
    """

    access_token: str
    refresh_token: str
    expires_at: float
    scope: str
    token_type: str

    def __post_init__(self) -> None:
        if not self.access_token:
            raise ValueError("access_token must be a non-empty string")
        if not self.refresh_token:
            raise ValueError("refresh_token must be a non-empty string")
        if self.expires_at <= 0:
            raise ValueError("expires_at must be a positive float")

    def __repr__(self) -> str:
        return (
            f"TokenPair(access_token='{_mask(self.access_token)}', "
            f"refresh_token='{_mask(self.refresh_token)}', "
            f"expires_at={self.expires_at}, "
            f"scope={self.scope!r}, token_type={self.token_type!r})"
        )

    def is_expired(self, buffer_seconds: float = 0) -> bool:
        """Check if the token is expired or will expire within buffer_seconds."""
        return time.monotonic() >= (self.expires_at - buffer_seconds)
