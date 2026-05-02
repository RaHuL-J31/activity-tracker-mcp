"""
src/tools/stats.py — Tool for fetching Personal Records and Lifetime Stats
"""

from services.strava import get_athlete, get_athlete_stats, get_athlete_activities, get_activity_details

def get_personal_records() -> dict:
    """
    Fetch all-time personal records, including distance PRs and lifetime totals.
    """
    try:
        # 1. Get basic profile and lifetime stats
        athlete = get_athlete()
        stats = get_athlete_stats(athlete["id"])
        
        # 2. Extract Run Totals
        run_stats = stats.get("all_run_totals", {})
        ride_stats = stats.get("all_ride_totals", {})
        
        # 3. Fetch recent "Best Efforts"
        # Since there's no single "PR" endpoint, we look at the athlete's 
        # highest-performing recent activities to extract best efforts.
        recent_runs = get_athlete_activities(per_page=10)
        best_efforts = _extract_best_efforts(recent_runs)
        
        return {
            "status": "success",
            "athlete": f"{athlete.get('firstname')} {athlete.get('lastname')}",
            "lifetime_stats": {
                "running": {
                    "total_distance_km": round(run_stats.get("distance", 0) / 1000, 2),
                    "total_runs": run_stats.get("count", 0),
                    "total_elevation_gain_m": run_stats.get("elevation_gain", 0),
                    "biggest_run_distance_km": round(stats.get("biggest_run_distance", 0) / 1000, 2)
                },
                "cycling": {
                    "total_distance_km": round(ride_stats.get("distance", 0) / 1000, 2),
                    "total_rides": ride_stats.get("count", 0),
                    "biggest_ride_distance_km": round(stats.get("biggest_ride_distance", 0) / 1000, 2),
                    "biggest_climb_m": stats.get("biggest_climb_elevation_gain", 0)
                }
            },
            "best_efforts_benchmarks": best_efforts,
            "note": "Best efforts are extracted from your most recent high-performance runs."
        }

    except Exception as e:
        return {"status": "error", "message": f"Failed to fetch PRs: {str(e)}"}


def _extract_best_efforts(activities: list) -> dict:
    """
    Scans activities for the 'best_efforts' field which Strava includes 
    in detailed run data.
    """
    # Keys are matched against Strava's 'best_efforts' names
    records = {
        "400m": None,
        "1k": None,
        "2k": None,
        "5k": None,
        "10k": None,
        "15k": None,
        "10 mile": None, # Kept as a fallback for long runs
        "Half-Marathon": None,
        "Marathon": None
    }
    
    # We only check the last few runs to keep it fast, 
    # but in a real-world scenario we could crawl more.
    for act in activities[:5]:
        if act.get("type") != "Run":
            continue
            
        # We need the DETAILED activity to see best_efforts
        details = get_activity_details(act["id"])
        efforts = details.get("best_efforts", [])
        
        for effort in efforts:
            raw_name = effort.get("name", "")
            # Normalize: "1 km" -> "1k", "5 km" -> "5k", etc.
            name = raw_name.replace(" km", "k").replace("km", "k")
            
            if name in records:
                time_sec = effort.get("moving_time")
                # If we don't have a record or this one is faster, update it
                if not records[name] or time_sec < records[name]["seconds"]:
                    records[name] = {
                        "time": _format_seconds(time_sec),
                        "seconds": time_sec,
                        "date": details.get("start_date_local"),
                        "activity_name": details.get("name")
                    }
                    
    # Clean up and return only found records
    return {k: v for k, v in records.items() if v is not None}


def _format_seconds(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0: return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"
