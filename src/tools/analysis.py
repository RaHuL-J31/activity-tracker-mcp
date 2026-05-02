"""
src/tools/analysis.py — Tool for detailed per-km activity analysis
"""

from services.strava import get_athlete_activities, get_activity_details

def analyze_workout(activity_id: int = None, activity_type: str = None) -> dict:
    """
    Perform a detailed per-km analysis of a workout.
    
    Args:
        activity_id: Optional specific activity ID. If provided, filters are ignored.
        activity_type: Optional type filter (e.g., 'Run', 'Walk', 'Ride'). 
                       Finds the latest activity of this type.
    """
    try:
        target_activity = None

        # 1. If ID is provided, use it directly
        if activity_id:
            target_activity = get_activity_details(activity_id)
        else:
            # 2. Otherwise, search recent activities
            # We fetch more than 1 to allow for type filtering (e.g., skip a walk to find a run)
            recent = get_athlete_activities(per_page=10)
            if not recent:
                return {"status": "error", "message": "No activities found to analyze."}
            
            if activity_type:
                # Find the latest matching type
                for act in recent:
                    if act.get("type", "").lower() == activity_type.lower() or \
                       act.get("sport_type", "").lower() == activity_type.lower():
                        target_activity = get_activity_details(act["id"])
                        break
                
                if not target_activity:
                    return {
                        "status": "error", 
                        "message": f"Could not find a recent activity of type '{activity_type}' in the last 10 entries."
                    }
            else:
                # Default to absolute latest
                target_activity = get_activity_details(recent[0]["id"])
        
        full_act = target_activity
        activity_id = full_act["id"]
        
        # 3. Basic Info
        activity_type = full_act.get("type", "Workout")
        name = full_act.get("name", "Unnamed Activity")
        splits = full_act.get("splits_metric", [])
        
        if not splits:
            return {
                "status": "success",
                "message": f"Found '{name}' ({activity_type}), but it has no per-km split data for analysis.",
                "summary": {
                    "distance_km": round(full_act.get("distance", 0) / 1000, 2),
                    "duration": f"{full_act.get('moving_time', 0) // 60} mins"
                }
            }

        # 4. Perform Analysis
        analysis_results = _perform_split_analysis(splits, activity_type)
        
        return {
            "status": "success",
            "activity_name": name,
            "activity_type": activity_type,
            "date": full_act.get("start_date_local"),
            "distance_km": round(full_act.get("distance", 0) / 1000, 2),
            "total_moving_time": _format_seconds(full_act.get("moving_time", 0)),
            "analysis": analysis_results,
            "conclusion": _generate_conclusion(analysis_results, activity_type)
        }

    except Exception as e:
        return {"status": "error", "message": f"Analysis failed: {str(e)}"}


def _perform_split_analysis(splits: list, activity_type: str) -> dict:
    """Analyze per-km splits for trends."""
    processed_splits = []
    paces = []
    heart_rates = []
    
    for i, s in enumerate(splits, 1):
        # Strava gives pace in seconds per metre. 
        # Convert to min/km: (seconds / distance_m) * 1000 / 60
        dist = s.get("distance", 0)
        time = s.get("moving_time", 0)
        
        pace_min_km = None
        if dist > 100: # Ignore very small splits
            pace_sec_km = (time / dist) * 1000
            paces.append(pace_sec_km)
            pace_min_km = _format_pace(pace_sec_km)
        
        hr = s.get("average_heartrate")
        if hr:
            heart_rates.append(hr)
            
        processed_splits.append({
            "km": i,
            "pace": pace_min_km,
            "avg_hr": round(hr) if hr else None,
            "elevation_diff": round(s.get("elevation_difference", 0), 1)
        })

    # Stats
    fastest_split = min(paces) if paces else 0
    slowest_split = max(paces) if paces else 0
    avg_pace = sum(paces) / len(paces) if paces else 0
    
    # Consistency: Standard deviation would be better, but range works for a quick check
    pace_variance_sec = slowest_split - fastest_split
    
    return {
        "splits": processed_splits,
        "metrics": {
            "fastest_km": _format_pace(fastest_split),
            "slowest_km": _format_pace(slowest_split),
            "avg_pace": _format_pace(avg_pace),
            "pace_variance_seconds": round(pace_variance_sec),
            "avg_hr": round(sum(heart_rates) / len(heart_rates)) if heart_rates else None,
            "hr_trend": _analyze_hr_trend(heart_rates) if heart_rates else "N/A"
        }
    }


def _analyze_hr_trend(hrs: list) -> str:
    if len(hrs) < 3: return "Stable"
    # Simple check: compare first third vs last third
    first_part = sum(hrs[:len(hrs)//3]) / (len(hrs)//3)
    last_part = sum(hrs[-len(hrs)//3:]) / (len(hrs)//3)
    
    diff = last_part - first_part
    if diff > 10: return "Significant drift (Fatigue or intensity increase)"
    if diff > 5: return "Slight drift"
    if diff < -5: return "Decreasing (Cooling down or lower intensity)"
    return "Stable"


def _generate_conclusion(results: dict, activity_type: str) -> str:
    metrics = results["metrics"]
    variance = metrics["pace_variance_seconds"]
    hr_trend = metrics["hr_trend"]
    
    positives = []
    negatives = []
    
    # 1. Pace Consistency
    if variance < 20:
        positives.append("Excellent pace consistency.")
    elif variance > 60:
        negatives.append("High pace variance; try to maintain a more even effort.")
        
    # 2. Heart Rate
    if "drift" in hr_trend.lower():
        negatives.append(f"Heart rate showed {hr_trend.lower()}. Check your hydration or aerobic base.")
    elif hr_trend == "Stable":
        positives.append("Heart rate remained stable, showing good aerobic efficiency.")
        
    # 3. Type specific
    if activity_type.lower() == "run" and metrics["avg_hr"] and metrics["avg_hr"] > 170:
        negatives.append("High average heart rate; ensure you aren't overtraining.")

    conclusion = "What went right: " + (" ".join(positives) if positives else "Maintained a steady move.")
    conclusion += "\nWhat to improve: " + (" ".join(negatives) if negatives else "Great consistency! Keep it up.")
    
    return conclusion


def _format_pace(seconds_per_km: float) -> str:
    minutes = int(seconds_per_km // 60)
    seconds = int(seconds_per_km % 60)
    return f"{minutes}:{seconds:02d} /km"


def _format_seconds(seconds: int) -> str:
    h, r = divmod(seconds, 3600)
    m, s = divmod(r, 60)
    if h > 0: return f"{h}h {m}m {s}s"
    return f"{m}m {s}s"
