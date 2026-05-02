"""
scripts/get_token.py — One-time Strava OAuth2 Authorization Helper
"""

import os
import webbrowser
import httpx
from pathlib import Path
from dotenv import load_dotenv, set_key

# Find root for .env
ROOT_DIR = Path(__file__).parent.parent.resolve()
ENV_PATH = ROOT_DIR / ".env"
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
REQUIRED_SCOPES = "read,activity:read_all"

def main():
    print("=" * 60)
    print("  Strava OAuth2 Authorization Helper")
    print("=" * 60)

    load_dotenv(dotenv_path=ENV_PATH, override=True)
    client_id     = os.environ.get("STRAVA_CLIENT_ID", "")
    client_secret = os.environ.get("STRAVA_CLIENT_SECRET", "")

    if not client_id or "your_client_id" in client_id:
        print("\nFAIL: STRAVA_CLIENT_ID is not set in .env")
        sys.exit(1)
    if not client_secret or "your_client_secret" in client_secret:
        print("\nFAIL: STRAVA_CLIENT_SECRET is not set in .env")
        sys.exit(1)

    auth_url = (
        f"https://www.strava.com/oauth/authorize"
        f"?client_id={client_id}"
        f"&response_type=code"
        f"&redirect_uri=http://localhost"
        f"&approval_prompt=force"
        f"&scope={REQUIRED_SCOPES}"
    )

    print(f"\n[1/3] Opening Strava authorization page in your browser...")
    webbrowser.open(auth_url)

    print("[2/3] Paste the full redirect URL here: ")
    redirect_url = input("> ").strip()

    if "code=" not in redirect_url:
        print("\nFAIL: Could not find 'code=' in the URL.")
        sys.exit(1)

    code = redirect_url.split("code=")[1].split("&")[0]
    
    print("\n[3/3] Exchanging code for tokens...")
    try:
        response = httpx.post(
            STRAVA_TOKEN_URL,
            data={
                "client_id":     client_id,
                "client_secret": client_secret,
                "code":          code,
                "grant_type":    "authorization_code",
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        
        set_key(str(ENV_PATH), "STRAVA_ACCESS_TOKEN",    data["access_token"])
        set_key(str(ENV_PATH), "STRAVA_REFRESH_TOKEN",   data["refresh_token"])
        set_key(str(ENV_PATH), "STRAVA_TOKEN_EXPIRES_AT", str(data["expires_at"]))

        print(f"\n  OK: Tokens saved to .env")
    except Exception as e:
        print(f"\nFAIL: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
