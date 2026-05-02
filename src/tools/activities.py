"""
src/tools/activities.py — Tool to fetch recent Strava activities
"""

from services.strava import get_athlete_activities

def get_recent_activities(count: int = 10, page: int = 1) -> dict:
    """
    Retrieve the authenticated athlete's recent Strava activities.

    Args:
        count: Number of activities to fetch (1–50, default 10).
        page:  Page number for pagination (default 1).

    Returns a list of activities with key stats such as name, type,
    distance, duration, elevation gain, pace, and date.
    """
    # Clamp count to a safe range
    count = max(1, min(count, 50))

    try:
        raw_activities = get_athlete_activities(per_page=count, page=page)

        if not raw_activities:
            return {
                "status": "success",
                "count": 0,
                "page": page,
                "activities": [],
                "message": "No activities found for this page.",
            }

        activities = []
        for act in raw_activities:
            # Distance: Strava returns metres — convert to km
            distance_m: float = act.get("distance", 0)
            distance_km = round(distance_m / 1000, 2)

            # Moving time in seconds → mm:ss or hh:mm:ss
            moving_time_s: int = act.get("moving_time", 0)
            hours, remainder = divmod(moving_time_s, 3600)
            minutes, seconds = divmod(remainder, 60)
            duration_str = (
                f"{hours}h {minutes}m {seconds}s"
                if hours
                else f"{minutes}m {seconds}s"
            )

            # Average pace (min/km) — only meaningful for runs
            avg_pace = None
            if distance_m > 0 and moving_time_s > 0:
                pace_sec_per_km = (moving_time_s / distance_m) * 1000
                pace_min = int(pace_sec_per_km // 60)
                pace_sec = int(pace_sec_per_km % 60)
                avg_pace = f"{pace_min}:{pace_sec:02d} min/km"

            activities.append({
                "id": act.get("id"),
                "name": act.get("name"),
                "type": act.get("type"),
                "sport_type": act.get("sport_type"),
                "start_date_local": act.get("start_date_local"),
                "distance_km": distance_km,
                "duration": duration_str,
                "moving_time_seconds": moving_time_s,
                "elevation_gain_m": act.get("total_elevation_gain"),
                "average_speed_kmh": round((act.get("average_speed", 0)) * 3.6, 2),
                "max_speed_kmh": round((act.get("max_speed", 0)) * 3.6, 2),
                "average_pace_per_km": avg_pace,
                "average_heartrate": act.get("average_heartrate"),
                "max_heartrate": act.get("max_heartrate"),
                "average_watts": act.get("average_watts"),
                "kudos_count": act.get("kudos_count"),
                "suffer_score": act.get("suffer_score"),
                "trainer": act.get("trainer", False),
                "commute": act.get("commute", False),
                "map_polyline": act.get("map", {}).get("summary_polyline"),
            })

        return {
            "status": "success",
            "count": len(activities),
            "page": page,
            "activities": activities,
        }

    except RuntimeError as e:
        return {
            "status": "error",
            "message": str(e),
        }
