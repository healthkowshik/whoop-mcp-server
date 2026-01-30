from mcp.server.fastmcp import FastMCP

from app.services.whoop_client import WhoopAPIError, client
from app.utils.timezone import process_response_timestamps


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

        Timestamps:
        - start/end: Time when sleep started/ended in the user's timezone at that location
          (e.g., '2024-01-15 10:30 PM (-08:00)')

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

        Computed fields (based on end/wake time, falls back to start if ongoing):
        - date: Date string (YYYY-MM-DD)
        - weekday: Day of week (e.g., 'Monday', 'Tuesday')
        - is_weekend: Boolean, True if Saturday or Sunday
        """
        try:
            params = {}
            if start:
                params["start"] = start
            if end:
                params["end"] = end
            response = await client.get_paginated("/v2/activity/sleep", params, limit)
            return process_response_timestamps(response)
        except WhoopAPIError as e:
            return {"error": e.message, "status_code": e.status_code}

    @mcp.tool()
    async def get_sleep(sleep_id: str) -> dict:
        """Get single sleep session by UUID.

        Args:
            sleep_id: The sleep session UUID

        Returns:
            Sleep record with stage summary and scores

        Timestamps:
        - start/end: Time in user's timezone when sleep occurred

        Units:
        - All durations in milliseconds
        - respiratory_rate: breaths per minute
        - Percentages: 0-100 scale
        """
        try:
            response = await client.get(f"/v2/activity/sleep/{sleep_id}")
            return process_response_timestamps(response)
        except WhoopAPIError as e:
            return {"error": e.message, "status_code": e.status_code}
