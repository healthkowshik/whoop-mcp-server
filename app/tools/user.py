from mcp.server.fastmcp import FastMCP

from app.services.whoop_client import WhoopAPIError, client


def register_user_tools(mcp: FastMCP):
    @mcp.tool()
    async def get_user() -> dict:
        """Get authenticated user's profile and body measurements.

        Returns combined profile (user_id, email, first_name, last_name)
        and body measurements (height_meter, weight_kilogram, max_heart_rate).

        Units:
        - height: meters
        - weight: kilograms
        - max_heart_rate: BPM
        """
        try:
            profile = await client.get("/v2/user/profile/basic")
            body = await client.get("/v2/user/measurement/body")
            return {"profile": profile, "body_measurement": body}
        except WhoopAPIError as e:
            return {"error": e.message, "status_code": e.status_code}
