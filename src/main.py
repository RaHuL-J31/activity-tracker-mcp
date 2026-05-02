"""
src/main.py — Strava MCP Server Entry Point
"""

from fastmcp import FastMCP
from tools.connection import check_strava_connection
from tools.activities import get_recent_activities
from tools.analysis import analyze_workout
from tools.coach import generate_training_plan
from tools.stats import get_personal_records

# ---------------------------------------------------------------------------
# Server initialization
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="Strava MCP",
    instructions=(
        "You are connected to the Strava API. You can retrieve the user's "
        "training activities, athlete profile, and stats. \n\n"
        "CRITICAL: When generating a training plan, ALWAYS display the pace ranges "
        "and heart rate zones for each workout as provided by the tool. Do not "
        "omit these technical details, as they are essential for the user's training."
    ),
)

# ---------------------------------------------------------------------------
# Tool Registration
# ---------------------------------------------------------------------------

# Register tools imported from the tools/ directory
mcp.tool()(check_strava_connection)
mcp.tool()(get_recent_activities)
mcp.tool()(analyze_workout)
mcp.tool()(generate_training_plan)
mcp.tool()(get_personal_records)

if __name__ == "__main__":
    mcp.run()
