from mcp.server.fastmcp import FastMCP

from app.services.whoop_client import WhoopAPIError, client


def register_workout_tools(mcp: FastMCP):
    @mcp.tool()
    async def get_workouts(
        start: str | None = None,
        end: str | None = None,
        limit: int = 25,
    ) -> dict:
        """Get collection of workout records.

        Includes all activities tracked by WHOOP (running, cycling, strength, etc).

        Args:
            start: Start datetime (ISO 8601)
            end: End datetime (ISO 8601)
            limit: Max records to return (default 25, max 1000)

        Returns:
            records: List of workouts with scores
            has_more: Whether more records exist
            next_token: Token for manual pagination

        Score fields:
        - strain: 0-21 scale
        - kilojoule: Energy expenditure in kJ
        - average_heart_rate: BPM
        - max_heart_rate: BPM
        - distance_meter: Distance in meters
        - altitude_gain_meter: Elevation gain in meters
        - zone_duration: Time in each HR zone (milliseconds)
        """
        try:
            params = {}
            if start:
                params["start"] = start
            if end:
                params["end"] = end
            return await client.get_paginated("/v2/activity/workout", params, limit)
        except WhoopAPIError as e:
            return {"error": e.message, "status_code": e.status_code}

    @mcp.tool()
    async def get_workout(workout_id: str) -> dict:
        """Get single workout by UUID.

        Args:
            workout_id: The workout UUID

        Returns:
            Workout record with scores

        Score fields:
        - strain: 0-21 scale
        - kilojoule: Energy in kJ
        - average_heart_rate/max_heart_rate: BPM
        - distance_meter: Distance in meters
        - altitude_gain_meter: Elevation gain in meters
        - percent_recorded: Percentage of workout with HR data
        - zone_duration: Time in HR zones 0-5 (milliseconds)
        """
        try:
            return await client.get(f"/v2/activity/workout/{workout_id}")
        except WhoopAPIError as e:
            return {"error": e.message, "status_code": e.status_code}
