from mcp.server.fastmcp import FastMCP

from app.services.whoop_client import WhoopAPIError, client
from app.utils.timezone import process_response_timestamps


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

        Timestamps:
        - start/end: Time when workout started/ended in the user's timezone at that location
          (e.g., '2024-01-15 06:30 AM (-08:00)')

        Score fields:
        - strain: 0-21 scale
        - kilojoule: Energy expenditure in kJ
        - average_heart_rate: BPM
        - max_heart_rate: BPM
        - distance_meter: Distance in meters
        - altitude_gain_meter: Elevation gain in meters
        - zone_duration: Time in each HR zone (milliseconds)

        Computed fields (based on end time, falls back to start if ongoing):
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
            response = await client.get_paginated("/v2/activity/workout", params, limit)
            return process_response_timestamps(response)
        except WhoopAPIError as e:
            return {"error": e.message, "status_code": e.status_code}

    @mcp.tool()
    async def get_workout(workout_id: str) -> dict:
        """Get single workout by UUID.

        Args:
            workout_id: The workout UUID

        Returns:
            Workout record with scores

        Timestamps:
        - start/end: Time in user's timezone when workout occurred

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
            response = await client.get(f"/v2/activity/workout/{workout_id}")
            return process_response_timestamps(response)
        except WhoopAPIError as e:
            return {"error": e.message, "status_code": e.status_code}
