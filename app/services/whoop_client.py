import logging
from typing import Any

import httpx

from app.config import settings

MAX_LIMIT = 1000
DEFAULT_LIMIT = 25

logger = logging.getLogger(__name__)


class WhoopAPIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"WHOOP API Error ({status_code}): {message}")


class WhoopClient:
    def __init__(self):
        self.base_url = settings.whoop_api_base_url
        self.token_url = settings.whoop_token_url
        self.access_token = settings.whoop_access_token
        self.refresh_token = settings.whoop_refresh_token
        self.client_id = settings.whoop_client_id
        self.client_secret = settings.whoop_client_secret

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def _refresh_access_token(self) -> bool:
        """Refresh the access token using the refresh token. Returns True if successful."""
        if not all([self.refresh_token, self.client_id, self.client_secret]):
            logger.warning("Cannot refresh token: missing refresh_token, client_id, or client_secret")
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_url,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": self.refresh_token,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    },
                    timeout=30.0,
                )
                if response.status_code != 200:
                    logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
                    return False

                tokens = response.json()
                self.access_token = tokens["access_token"]
                if "refresh_token" in tokens:
                    self.refresh_token = tokens["refresh_token"]
                logger.info("Successfully refreshed access token")
                return True
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return False

    async def _request(
        self, method: str, path: str, params: dict | None = None, _retry: bool = True
    ) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                f"{self.base_url}{path}",
                headers=self._get_headers(),
                params=params,
                timeout=30.0,
            )
            if response.status_code == 401:
                if _retry and await self._refresh_access_token():
                    return await self._request(method, path, params, _retry=False)
                raise WhoopAPIError(401, "Invalid or expired access token")
            if response.status_code == 404:
                raise WhoopAPIError(404, f"Resource not found: {path}")
            if response.status_code == 429:
                raise WhoopAPIError(429, "Rate limit exceeded. Please retry later.")
            if response.status_code >= 500:
                raise WhoopAPIError(response.status_code, "WHOOP server error. Please retry.")
            response.raise_for_status()
            return response.json()

    async def get(self, path: str, params: dict | None = None) -> dict:
        return await self._request("GET", path, params)

    async def get_paginated(
        self,
        path: str,
        params: dict | None = None,
        limit: int = DEFAULT_LIMIT,
    ) -> dict[str, Any]:
        """Fetch paginated results up to limit (max 1000)."""
        limit = min(limit, MAX_LIMIT)
        params = params or {}
        all_records: list[dict] = []
        next_token: str | None = None

        while len(all_records) < limit:
            page_params = {**params, "limit": min(25, limit - len(all_records))}
            if next_token:
                page_params["nextToken"] = next_token

            data = await self.get(path, page_params)
            records = data.get("records", [])
            all_records.extend(records)

            next_token = data.get("next_token")
            if not next_token or not records:
                break

        return {
            "records": all_records[:limit],
            "has_more": next_token is not None and len(all_records) >= limit,
            "next_token": next_token if len(all_records) >= limit else None,
        }


client = WhoopClient()
