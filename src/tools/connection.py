"""
src/tools/connection.py — Tool to check Strava API connection
"""

from services.strava import get_athlete

def check_strava_connection() -> dict:
    """
    Verify that the MCP server can authenticate with the Strava API.

    Returns a summary of the authenticated athlete's profile if the
    connection is healthy, or a descriptive error message if not.
    """
    try:
        athlete = get_athlete()
        return {
            "status": "connected",
            "message": "Successfully connected to Strava API.",
            "athlete": {
                "id": athlete.get("id"),
                "username": athlete.get("username"),
                "firstname": athlete.get("firstname"),
                "lastname": athlete.get("lastname"),
                "city": athlete.get("city"),
                "country": athlete.get("country"),
                "profile_picture": athlete.get("profile_medium"),
                "follower_count": athlete.get("follower_count"),
                "friend_count": athlete.get("friend_count"),
                "measurement_preference": athlete.get("measurement_preference"),
            },
        }
    except RuntimeError as e:
        return {
            "status": "error",
            "message": str(e),
        }
