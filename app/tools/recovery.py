from mcp.server.fastmcp import FastMCP

from app.schemas.recovery import Recovery
from app.services.whoop_client import WhoopAPIError, client


def register_recovery_tools(mcp: FastMCP):
    @mcp.tool()
    async def get_recoveries(
        start: str | None = None,
        end: str | None = None,
        limit: int = 25,
    ) -> dict:
        """Get collection of recovery records.

        Recovery represents how prepared your body is to perform,
        calculated each morning based on sleep and HRV.

        Args:
            start: Start datetime (ISO 8601)
            end: End datetime (ISO 8601)
            limit: Max records to return (default 25, max 1000)

        Returns:
            records: List of recovery records with scores
            has_more: Whether more records exist
            next_token: Token for manual pagination

        Score fields:
        - recovery_score: 0-100% (green 67-100, yellow 34-66, red 0-33)
        - resting_heart_rate: BPM
        - hrv_rmssd_milli: Heart rate variability in milliseconds
        - spo2_percentage: Blood oxygen saturation (0-100)
        - skin_temp_celsius: Skin temperature in Celsius
        """
        try:
            params = {}
            if start:
                params["start"] = start
            if end:
                params["end"] = end
            response = await client.get_paginated("/v2/recovery", params, limit)

            # Parse records through Pydantic models
            response["records"] = [
                Recovery(**record).model_dump() for record in response["records"]
            ]
            return response
        except WhoopAPIError as e:
            return {"error": e.message, "status_code": e.status_code}

    @mcp.tool()
    async def get_recovery(cycle_id: int) -> dict:
        """Get recovery for a specific cycle.

        Args:
            cycle_id: The cycle ID to get recovery for

        Returns:
            Recovery record with scores

        Score fields:
        - recovery_score: 0-100%
        - resting_heart_rate: BPM
        - hrv_rmssd_milli: HRV in milliseconds
        - spo2_percentage: Blood oxygen (0-100)
        - skin_temp_celsius: Skin temperature in Celsius
        - user_calibrating: Whether user is still in calibration period
        """
        try:
            response = await client.get(f"/v2/cycle/{cycle_id}/recovery")
            return Recovery(**response).model_dump()
        except WhoopAPIError as e:
            return {"error": e.message, "status_code": e.status_code}
