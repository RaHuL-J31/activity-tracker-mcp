"""
scripts/basic-test.py — Essential Health Check for Strava MCP
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def main():
    print("=" * 60)
    print("  Strava MCP -- Basic Health Check")
    print("=" * 60)

    # 1. Check for .env file
    ROOT_DIR = Path(__file__).parent.parent.resolve()
    env_path = ROOT_DIR / ".env"
    
    print("\n[1/3] Checking .env file...")
    if not env_path.exists():
        print("  FAIL: .env file NOT FOUND at root.")
        print(f"  Expected path: {env_path}")
        print("  Please copy .env.example to .env and fill in your credentials.")
        sys.exit(1)
    
    load_dotenv(dotenv_path=env_path, override=True)
    print("  OK: .env file detected.")

    # 2. Test Authentication
    print("\n[2/3] Testing Strava Authentication...")
    try:
        # Ensure root is in path for imports
        if str(ROOT_DIR) not in sys.path:
            sys.path.insert(0, str(ROOT_DIR))
            
        from services.auth import get_valid_access_token
        token = get_valid_access_token()
        print(f"  OK: Successfully retrieved access token.")
    except Exception as e:
        print(f"  FAIL: Authentication failed.")
        print(f"  Error: {str(e)}")
        print("\n  DEBUG TIPS:")
        print("  - Check if your CLIENT_ID and CLIENT_SECRET in .env are correct.")
        print("  - Ensure your REFRESH_TOKEN is valid (run get_token.py if needed).")
        print("  - Run uv run scripts/get_token.py to refresh the token.")
        sys.exit(1)

    # 3. Test Connection Tool
    print("\n[3/3] Verifying Strava API Connection...")
    try:
        from tools.connection import check_strava_connection
        result = check_strava_connection()
        
        if result["status"] == "connected":
            athlete = result["athlete"]
            print(f"  OK: Connected to Strava API.")
            print(f"  Athlete: {athlete['firstname']} {athlete['lastname']} (@{athlete['username']})")
        else:
            print(f"  FAIL: API responded with an error.")
            print(f"  Message: {result['message']}")
            sys.exit(1)
    except Exception as e:
        print(f"  FAIL: Unexpected error during connection check.")
        print(f"  Error: {str(e)}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  BASIC HEALTH CHECK PASSED!")
    print("  The server is ready to be used with Claude Desktop.")
    print("=" * 60)

if __name__ == "__main__":
    main()
