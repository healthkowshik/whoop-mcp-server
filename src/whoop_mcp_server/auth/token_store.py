"""Token persistence interface and default in-memory implementation."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class TokenStore(Protocol):
    """Interface for pluggable token persistence.

    Any class implementing save() and load() with matching signatures
    is a valid TokenStore — no inheritance required.
    """

    async def save(self, data: dict) -> None:
        """Persist token data.

        Called after every successful token exchange or refresh.
        """
        ...

    async def load(self) -> dict | None:
        """Load previously persisted token data.

        Returns None if no tokens are stored.
        """
        ...


class MemoryTokenStore:
    """In-memory TokenStore implementation.

    Tokens are lost on process restart. This is the default store
    when no persistent implementation is provided.
    """

    def __init__(self) -> None:
        self._data: dict | None = None

    async def save(self, data: dict) -> None:
        self._data = data

    async def load(self) -> dict | None:
        return self._data
