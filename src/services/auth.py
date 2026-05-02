"""
src/services/auth.py — Strava OAuth2 Token Manager

Handles:
  - Loading tokens from .env
  - Detecting expiry (with a 5-minute safety buffer)
  - Automatically refreshing tokens via Strava's token endpoint
  - Persisting new tokens back to .env so they survive restarts
"""

import os
import time
import httpx
from pathlib import Path
from dotenv import load_dotenv, set_key

# Absolute path to the .env file in the root directory
ENV_PATH = Path(__file__).parent.parent.parent / ".env"

# Strava OAuth2 token endpoint
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"

# Safety buffer: refresh 5 minutes before actual expiry
EXPIRY_BUFFER_SECONDS = 300


def _load_env() -> None:
    """Force-reload .env from disk (picks up fresh tokens after a refresh)."""
    load_dotenv(dotenv_path=ENV_PATH, override=True)


def _persist_tokens(access_token: str, refresh_token: str, expires_at: int) -> None:
    """Write updated tokens back to .env so they survive server restarts."""
    set_key(str(ENV_PATH), "STRAVA_ACCESS_TOKEN", access_token)
    set_key(str(ENV_PATH), "STRAVA_REFRESH_TOKEN", refresh_token)
    set_key(str(ENV_PATH), "STRAVA_TOKEN_EXPIRES_AT", str(expires_at))
    # Also update the live process environment
    os.environ["STRAVA_ACCESS_TOKEN"] = access_token
    os.environ["STRAVA_REFRESH_TOKEN"] = refresh_token
    os.environ["STRAVA_TOKEN_EXPIRES_AT"] = str(expires_at)


def _is_token_expired() -> bool:
    """Return True if the current access token has expired (or expires soon)."""
    try:
        expires_at = int(os.environ.get("STRAVA_TOKEN_EXPIRES_AT", "0"))
    except ValueError:
        expires_at = 0
    return time.time() >= (expires_at - EXPIRY_BUFFER_SECONDS)


def _refresh_tokens() -> str:
    """
    Call Strava's token endpoint with the refresh token.
    Updates .env and returns the new access token.
    Raises RuntimeError on any failure.
    """
    client_id = os.environ.get("STRAVA_CLIENT_ID", "")
    client_secret = os.environ.get("STRAVA_CLIENT_SECRET", "")
    refresh_token = os.environ.get("STRAVA_REFRESH_TOKEN", "")

    if not all([client_id, client_secret, refresh_token]):
        raise RuntimeError(
            "Missing STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, or STRAVA_REFRESH_TOKEN "
            "in .env — please fill in your credentials."
        )

    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }

    try:
        response = httpx.post(STRAVA_TOKEN_URL, data=payload, timeout=15)
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise RuntimeError(
            f"Strava token refresh failed (HTTP {e.response.status_code}): "
            f"{e.response.text}"
        ) from e
    except httpx.RequestError as e:
        raise RuntimeError(
            f"Network error during Strava token refresh: {e}"
        ) from e

    data = response.json()

    new_access_token: str = data["access_token"]
    new_refresh_token: str = data["refresh_token"]
    new_expires_at: int = data["expires_at"]

    _persist_tokens(new_access_token, new_refresh_token, new_expires_at)
    return new_access_token


def get_valid_access_token() -> str:
    """
    Public interface: return a guaranteed-fresh Strava access token.

    Algorithm:
      1. Load latest values from .env
      2. If the token is still valid → return it
      3. Otherwise → refresh, persist, return new token
    """
    _load_env()

    if not _is_token_expired():
        token = os.environ.get("STRAVA_ACCESS_TOKEN", "")
        if token and token != "your_access_token_here":
            return token

    # Token missing, expired, or placeholder — attempt refresh
    return _refresh_tokens()
