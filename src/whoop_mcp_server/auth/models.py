"""Core data models for WHOOP OAuth token management."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

NonEmptyStr = Annotated[str, Field(min_length=1)]


def _mask(value: str, visible: int = 6) -> str:
    """Mask a secret string, showing only the first `visible` characters."""
    if len(value) <= visible:
        return "***"
    return value[:visible] + "***"


class WhoopCredentials(BaseModel):
    """WHOOP OAuth client credentials.

    The client_secret is always masked in repr/str output.
    """

    model_config = ConfigDict(frozen=True, extra="ignore")

    client_id: NonEmptyStr
    client_secret: NonEmptyStr

    def __repr__(self) -> str:
        return (
            f"WhoopCredentials(client_id={self.client_id!r}, client_secret='***')"
        )

    def __str__(self) -> str:
        return self.__repr__()


class TokenPair(BaseModel):
    """Represents the current authentication state.

    Attributes:
        access_token: Bearer token for WHOOP API requests.
        refresh_token: Token used to obtain a new access token.
        expires_at: time.monotonic() timestamp after which the access token is expired.
        scope: Space-delimited scope string from the token response.
        token_type: Always "bearer" for WHOOP.
    """

    model_config = ConfigDict(frozen=True, extra="ignore")

    access_token: NonEmptyStr
    refresh_token: NonEmptyStr
    expires_at: Annotated[float, Field(gt=0)]
    scope: str
    token_type: str

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

    def to_store_dict(self) -> dict:
        """Serialize to store format with UTC expiry."""
        remaining = self.expires_at - time.monotonic()
        expires_at_utc = datetime.now(timezone.utc).timestamp() + remaining
        dt = datetime.fromtimestamp(expires_at_utc, tz=timezone.utc)
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at_utc": dt.isoformat(),
            "scope": self.scope,
            "token_type": self.token_type,
        }

    @classmethod
    def from_store_dict(cls, data: dict) -> TokenPair:
        """Deserialize from store format, converting UTC back to monotonic."""
        expires_at_utc_str = data.get("expires_at_utc")
        if expires_at_utc_str:
            expires_dt = datetime.fromisoformat(expires_at_utc_str)
            remaining = (
                expires_dt - datetime.now(timezone.utc)
            ).total_seconds()
            expires_at = time.monotonic() + remaining
        else:
            expires_at = time.monotonic()  # Treat as expired

        return cls(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_at=max(expires_at, 0.01),
            scope=data.get("scope", ""),
            token_type=data.get("token_type", "bearer"),
        )


class TokenResponse(BaseModel):
    """Intermediate representation of a WHOOP token endpoint response.

    Validates the raw API response and provides conversion to TokenPair.
    """

    model_config = ConfigDict(extra="ignore")

    access_token: NonEmptyStr
    refresh_token: NonEmptyStr
    expires_in: Annotated[int, Field(gt=0)]
    scope: str = ""
    token_type: str = "bearer"

    def to_token_pair(self) -> TokenPair:
        """Convert to a TokenPair with monotonic expiry."""
        return TokenPair(
            access_token=self.access_token,
            refresh_token=self.refresh_token,
            expires_at=time.monotonic() + self.expires_in,
            scope=self.scope,
            token_type=self.token_type,
        )
