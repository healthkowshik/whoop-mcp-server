from mcp.server.fastmcp import FastMCP

from app.services.whoop_client import WhoopAPIError, client
from app.utils.timezone import process_record_timestamps, process_response_timestamps


def register_cycle_tools(mcp: FastMCP):
    @mcp.tool()
    async def get_cycles(
        start: str | None = None,
        end: str | None = None,
        limit: int = 25,
    ) -> dict:
        """Get collection of physiological cycles.

        Cycles represent 24-hour periods starting from sleep, containing
        strain, recovery, and sleep data.

        Args:
            start: Start datetime (ISO 8601, e.g. "2024-01-01T00:00:00Z")
            end: End datetime (ISO 8601)
            limit: Max records to return (default 25, max 1000)

        Returns:
            records: List of cycles with scores (strain, kilojoule, heart rates)
            has_more: Whether more records exist
            next_token: Token for manual pagination if needed

        Timestamps:
        - start/end: Time when cycle started/ended in the user's timezone at that location
          (e.g., '2024-01-15 07:00 AM (-08:00)')

        Metrics:
        - duration_hours: Duration of the cycle in hours (None if cycle hasn't ended)
        - strain: 0-21 scale
        - kilojoule: energy expenditure in kJ
        - heart_rate: BPM
        """
        try:
            params = {}
            if start:
                params["start"] = start
            if end:
                params["end"] = end
            response = await client.get_paginated("/v2/cycle", params, limit)
            return process_response_timestamps(response)
        except WhoopAPIError as e:
            return {"error": e.message, "status_code": e.status_code}

    @mcp.tool()
    async def get_cycle(
        cycle_id: int,
        include_sleep: bool = False,
        include_recovery: bool = False,
    ) -> dict:
        """Get single cycle by ID with optional related data.

        Args:
            cycle_id: The cycle ID
            include_sleep: Include PRIMARY sleep for this cycle
            include_recovery: Include recovery data for this cycle

        Returns:
            cycle: Cycle data with scores and duration_hours (start/end in user's timezone when recorded)
            sleep: Primary sleep if include_sleep=True (start/end in user's timezone when recorded)
            recovery: Recovery data if include_recovery=True

        Note: include_sleep returns only PRIMARY sleep. Use get_sleeps(cycle_id=...)
        for all sleep sessions including naps.
        """
        try:
            cycle = await client.get(f"/v2/cycle/{cycle_id}")
            result = {"cycle": process_record_timestamps(cycle)}
            if include_sleep:
                try:
                    sleep = await client.get(f"/v2/cycle/{cycle_id}/sleep")
                    result["sleep"] = process_record_timestamps(sleep)
                except WhoopAPIError as e:
                    if e.status_code != 404:
                        raise
                    result["sleep"] = None
            if include_recovery:
                try:
                    result["recovery"] = await client.get(f"/v2/cycle/{cycle_id}/recovery")
                except WhoopAPIError as e:
                    if e.status_code != 404:
                        raise
                    result["recovery"] = None
            return result
        except WhoopAPIError as e:
            return {"error": e.message, "status_code": e.status_code}
