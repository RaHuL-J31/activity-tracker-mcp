"""
src/tools/coach.py — AI Running Coach for Training Plans
"""

import math
from datetime import datetime, timedelta
from services.strava import get_athlete, get_athlete_activities, get_athlete_stats

def generate_training_plan(goal: str, weeks: int = None, runs_per_week: int = 3) -> dict:
    """
    Acts as a professional running coach to generate a structured training plan.
    
    Args:
        goal: The target race/distance (e.g., '5k', '10k', 'Half Marathon', 'Marathon').
        weeks: Duration of the plan. If missing, the coach will recommend one.
        runs_per_week: Number of days the user wants to run (default 3).
    """
    try:
        # 1. Fetch User Data
        athlete = get_athlete()
        athlete_id = athlete["id"]
        stats = get_athlete_stats(athlete_id)
        recent_activities = get_athlete_activities(per_page=30) # Last 30 to see patterns
        
        # 2. Analyze Fitness Level
        fitness = _analyze_fitness(recent_activities, stats)
        
        # 3. Validate Goal & Timeframe
        validation = _validate_goal(goal, weeks, fitness)
        if not validation["safe"]:
            return {
                "status": "warning",
                "message": validation["message"],
                "recommendation": validation["recommendation"]
            }
        
        # Use recommended weeks if none provided
        plan_weeks = weeks or validation["recommended_weeks"]
        
        # 4. Generate the Week-by-Week Plan
        plan = _build_plan(goal, plan_weeks, runs_per_week, fitness)
        
        return {
            "status": "success",
            "athlete_profile": {
                "name": f"{athlete.get('firstname')} {athlete.get('lastname')}",
                "fitness_level": fitness["level_desc"],
                "est_max_hr": fitness["max_hr"],
                "base_pace": _format_pace(fitness["base_pace_sec"])
            },
            "plan_metadata": {
                "goal": goal,
                "duration": f"{plan_weeks} weeks",
                "frequency": f"{runs_per_week} runs/week"
            },
            "training_plan": plan,
            "coach_notes": _get_coach_advice(goal, fitness)
        }

    except Exception as e:
        return {"status": "error", "message": f"Coaching engine failed: {str(e)}"}


def _analyze_fitness(activities: list, stats: dict) -> dict:
    """Determine zones and capability based on recent history."""
    runs = [a for a in activities if a.get("type") == "Run"]
    
    # Default values for new runners
    max_hr = 190
    threshold_pace = 420 # 7:00 /km
    
    if runs:
        # Calculate avg HR and estimated Max HR
        hrs = [r.get("average_heartrate") for r in runs if r.get("average_heartrate")]
        if hrs:
            avg_hr = sum(hrs) / len(hrs)
            max_hr = round(avg_hr + 40) # Rough estimate
            
        # Calculate Threshold Pace (approx. your 10k pace)
        paces = sorted([(r.get("moving_time", 1) / r.get("distance", 1)) * 1000 for r in runs])
        if paces:
            # We take the 20th percentile as threshold pace (faster end of your typical runs)
            threshold_pace = paces[int(len(paces) * 0.2)]

    # Calculate Zone Ranges
    # Zone 2 is typically 60-70% of Max HR and significantly slower than threshold
    return {
        "max_hr": max_hr,
        "threshold_pace_sec": threshold_pace,
        "base_pace_sec": threshold_pace + 90, # For the summary profile
        "level_desc": "Intermediate" if len(runs) > 10 else "Novice",
        "zones": {
            "Z1": {
                "hr": f"{round(max_hr * 0.50)} - {round(max_hr * 0.60)} bpm",
                "pace_sec": (threshold_pace + 120, threshold_pace + 180)
            },
            "Z2": {
                "hr": f"{round(max_hr * 0.60)} - {round(max_hr * 0.70)} bpm",
                "pace_sec": (threshold_pace + 60, threshold_pace + 120)
            },
            "Z3": {
                "hr": f"{round(max_hr * 0.70)} - {round(max_hr * 0.80)} bpm",
                "pace_sec": (threshold_pace + 20, threshold_pace + 60)
            },
            "Z4": {
                "hr": f"{round(max_hr * 0.80)} - {round(max_hr * 0.90)} bpm",
                "pace_sec": (threshold_pace - 10, threshold_pace + 20)
            },
            "Z5": {
                "hr": f"{round(max_hr * 0.90)}+ bpm",
                "pace_sec": (threshold_pace - 40, threshold_pace - 10)
            }
        }
    }


def _validate_goal(goal: str, weeks: int, fitness: dict) -> dict:
    """Sanity check for the goal vs timeframe."""
    g = goal.lower()
    
    # Define minimum safe prep weeks based on goal
    requirements = {
        "5k": 4,
        "10k": 6,
        "half": 10,
        "marathon": 16
    }
    
    # Match goal string
    req_weeks = 4
    for key, val in requirements.items():
        if key in g:
            req_weeks = val
            break
            
    if weeks and weeks < (req_weeks / 2): # Extremely aggressive
        return {
            "safe": False,
            "message": f"A {goal} in just {weeks} week(s) is risky and likely to cause injury.",
            "recommendation": f"For your fitness level, a minimum of {req_weeks} weeks is recommended for a safe and effective build-up."
        }
        
    return {"safe": True, "recommended_weeks": req_weeks}


def _build_plan(goal: str, weeks: int, freq: int, fitness: dict) -> list:
    """Generate the actual training blocks with ranges."""
    plan = []
    zones = fitness["zones"]
    
    for w in range(1, weeks + 1):
        # Progression logic: Recovery week every 4 weeks
        is_recovery = (w % 4 == 0)
            
        week_workouts = []
        
        # Day 1: Easy Run (Zone 2)
        z2 = zones["Z2"]
        week_workouts.append({
            "type": "Recovery / Easy Run",
            "distance": f"{round(3 + (w*0.5), 1)} km",
            "pace_range": f"{_format_pace(z2['pace_sec'][1])} - {_format_pace(z2['pace_sec'][0])}",
            "hr_range": z2["hr"],
            "description": "Keep it easy. You should be able to talk in full sentences."
        })
        
        # Day 2: Quality Session (Tempo or Intervals)
        if freq > 1:
            if w % 2 == 0 and not is_recovery:
                # Interval Session (Zone 4/5)
                z4 = zones["Z4"]
                week_workouts.append({
                    "type": "Intervals",
                    "sets": f"{3 + (w//3)} x 800m",
                    "pace_target": f"{_format_pace(z4['pace_sec'][0])}",
                    "hr_range": z4["hr"],
                    "description": "High intensity bursts. Push your threshold."
                })
            else:
                # Tempo Run (Zone 3)
                z3 = zones["Z3"]
                week_workouts.append({
                    "type": "Tempo Run",
                    "distance": f"{round(4 + (w*0.3), 1)} km",
                    "pace_range": f"{_format_pace(z3['pace_sec'][1])} - {_format_pace(z3['pace_sec'][0])}",
                    "hr_range": z3["hr"],
                    "description": "Steady, 'comfortably hard' effort."
                })
                
        # Day 3: Long Run (Zone 2)
        if freq > 2:
            long_dist = 5 + (w * 1.5)
            if "marathon" in goal.lower(): long_dist = 10 + (w * 2)
            if is_recovery: long_dist *= 0.7
            
            week_workouts.append({
                "type": "Long Run",
                "distance": f"{round(long_dist, 1)} km",
                "pace_range": f"{_format_pace(z2['pace_sec'][1])} - {_format_pace(z2['pace_sec'][0])}",
                "hr_range": z2["hr"],
                "description": "Focus on time on feet. Speed is not important here."
            })

        plan.append({
            "week": w,
            "phase": "Recovery" if is_recovery else ("Build" if w <= (weeks//2) else "Peak"),
            "workouts": week_workouts
        })
        
    return plan


def _get_coach_advice(goal: str, fitness: dict) -> str:
    advice = [
        "Hydration is key. Drink 500ml of water 2 hours before your runs.",
        "If you feel sharp pain, stop immediately. Don't run through injury.",
        "The 'Slow' end of your Zone 2 pace is your friend for recovery."
    ]
    if "marathon" in goal.lower():
        advice.append("Practice your race-day nutrition during your Long Runs.")
    return " ".join(advice)


def _format_pace(seconds_per_km: float) -> str:
    minutes = int(seconds_per_km // 60)
    seconds = int(seconds_per_km % 60)
    return f"{minutes}:{seconds:02d} /km"
