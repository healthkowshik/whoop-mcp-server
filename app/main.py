from fastmcp import FastMCP

from app.tools.cycles import register_cycle_tools
from app.tools.recovery import register_recovery_tools
from app.tools.sleep import register_sleep_tools
from app.tools.user import register_user_tools
from app.tools.workouts import register_workout_tools

mcp = FastMCP(
    "whoop",
    instructions="MCP server for WHOOP wearable health data",
)

register_user_tools(mcp)
register_cycle_tools(mcp)
register_sleep_tools(mcp)
register_recovery_tools(mcp)
register_workout_tools(mcp)


def main():
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
