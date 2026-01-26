from mcp.server.fastmcp import FastMCP

from app.services.whoop_client import WhoopAPIError, client


def register_sleep_tools(mcp: FastMCP):
    @mcp.tool()
    async def get_sleeps(
        start: str | None = None,
        end: str | None = None,
        limit: int = 25,
    ) -> dict:
        """Get collection of sleep sessions.

        Includes both primary sleep and naps.

        Args:
            start: Start datetime (ISO 8601)
            end: End datetime (ISO 8601)
            limit: Max records to return (default 25, max 1000)

        Returns:
            records: List of sleep sessions with stage summaries
            has_more: Whether more records exist
            next_token: Token for manual pagination

        Units:
        - All durations in milliseconds (convert to hours: ms / 3,600,000)
        - respiratory_rate: breaths per minute
        - Percentages: 0-100 scale

        Stage summary includes:
        - total_in_bed_time_milli
        - total_awake_time_milli
        - total_light_sleep_time_milli
        - total_slow_wave_sleep_time_milli (deep sleep)
        - total_rem_sleep_time_milli
        - sleep_cycle_count
        - disturbance_count
        """
        try:
            params = {}
            if start:
                params["start"] = start
            if end:
                params["end"] = end
            return await client.get_paginated("/v2/activity/sleep", params, limit)
        except WhoopAPIError as e:
            return {"error": e.message, "status_code": e.status_code}

    @mcp.tool()
    async def get_sleep(sleep_id: str) -> dict:
        """Get single sleep session by UUID.

        Args:
            sleep_id: The sleep session UUID

        Returns:
            Sleep record with stage summary and scores

        Units:
        - All durations in milliseconds
        - respiratory_rate: breaths per minute
        - Percentages: 0-100 scale
        """
        try:
            return await client.get(f"/v2/activity/sleep/{sleep_id}")
        except WhoopAPIError as e:
            return {"error": e.message, "status_code": e.status_code}
