from typing import Any

import httpx

from app.config import settings

MAX_LIMIT = 1000
DEFAULT_LIMIT = 25


class WhoopAPIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"WHOOP API Error ({status_code}): {message}")


class WhoopClient:
    def __init__(self):
        self.base_url = settings.whoop_api_base_url
        self.headers = {
            "Authorization": f"Bearer {settings.whoop_access_token}",
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, path: str, params: dict | None = None) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                f"{self.base_url}{path}",
                headers=self.headers,
                params=params,
                timeout=30.0,
            )
            if response.status_code == 401:
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
