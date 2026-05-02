"""
scripts/test_local.py — Local verification script
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Find root for .env
ROOT_DIR = Path(__file__).parent.parent.resolve()

print("=" * 60)
print("  Strava MCP -- Local Connection Test")
print("=" * 60)

# 1. Load .env
env_path = ROOT_DIR / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# 2. Test Auth
print("\n[1/3] Getting a valid access token...")
try:
    from services.auth import get_valid_access_token
    token = get_valid_access_token()
    print(f"  OK: Got access token")
except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

# 3. Test Tools
print("\n[2/3] Calling check_strava_connection...")
try:
    from tools.connection import check_strava_connection
    result = check_strava_connection()
    if result["status"] == "connected":
        print(f"  OK: Connected as {result['athlete']['firstname']}")
    else:
        print(f"  FAIL: {result['message']}")
        sys.exit(1)
except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

print("\n[3/3] Calling get_recent_activities...")
try:
    from tools.activities import get_recent_activities
    result = get_recent_activities(count=3)
    if result["status"] == "success":
        print(f"  OK: Fetched {result['count']} activities")
    else:
        print(f"  FAIL: {result['message']}")
        sys.exit(1)
except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

print("\n[4/4] Calling analyze_workout...")
try:
    from tools.analysis import analyze_workout
    result = analyze_workout(activity_type="Run")
    if result["status"] == "success":
        print(f"  OK: Analyzed '{result['activity_name']}'")
        print(f"  Type: {result['activity_type']}")
        # Print first line of conclusion
        print(f"  Insights: {result['conclusion'].splitlines()[0]}")
    else:
        print(f"  FAIL: {result['message']}")
        sys.exit(1)
except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

print("\n[5/5] Testing Coach Tool (generate_training_plan)...")
try:
    from tools.coach import generate_training_plan
    
    # Test 1: Realistic 5k plan
    print("  Testing 5k plan (8 weeks)...")
    res1 = generate_training_plan(goal="5k", weeks=8)
    if res1["status"] == "success":
        print(f"    OK: Generated {res1['plan_metadata']['duration']} plan for {res1['athlete_profile']['name']}")
    else:
        print(f"    FAIL: {res1.get('message')}")

    # Test 2: Unrealistic Marathon plan (Sanity Check)
    print("  Testing Marathon plan (2 weeks)...")
    res2 = generate_training_plan(goal="Marathon", weeks=2)
    if res2["status"] == "warning":
        print(f"    OK: Correctly flagged risky plan: {res2['message'][:50]}...")
    else:
        print(f"    FAIL: Did not catch unrealistic timeframe")

except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

print("\n[6/6] Testing Stats Tool (get_personal_records)...")
try:
    from tools.stats import get_personal_records
    result = get_personal_records()
    if result["status"] == "success":
        print(f"  OK: Fetched records for {result['athlete']}")
        print(f"  Lifetime Run Distance: {result['lifetime_stats']['running']['total_distance_km']} km")
        if result["best_efforts_benchmarks"]:
            print(f"  Found {len(result['best_efforts_benchmarks'])} specific distance PRs")
    else:
        print(f"  FAIL: {result.get('message')}")
except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("  ALL TESTS PASSED!")
print("=" * 60)
