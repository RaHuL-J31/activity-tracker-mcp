"""
src/services/strava.py — Thin HTTP client wrapper for the Strava v3 API

Every request:
  1. Obtains a fresh access token via the auth manager
  2. Makes the API call
  3. On 401 Unauthorized → forces a token refresh and retries ONCE
"""

import httpx
from services.auth import get_valid_access_token

STRAVA_API_BASE = "https://www.strava.com/api/v3"


def _build_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _make_request(
    method: str,
    endpoint: str,
    params: dict | None = None,
    retry_on_401: bool = True,
) -> dict | list:
    """
    Internal helper: performs an authenticated request to the Strava API.
    """
    token = get_valid_access_token()
    url = f"{STRAVA_API_BASE}{endpoint}"

    try:
        response = httpx.request(
            method,
            url,
            headers=_build_headers(token),
            params=params,
            timeout=20,
        )

        # 401 → token may have just expired mid-session; refresh & retry once
        if response.status_code == 401 and retry_on_401:
            from services.auth import _refresh_tokens  # noqa: PLC0415
            token = _refresh_tokens()
            response = httpx.request(
                method,
                url,
                headers=_build_headers(token),
                params=params,
                timeout=20,
            )

        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        raise RuntimeError(
            f"Strava API error (HTTP {e.response.status_code}) "
            f"on {method} {endpoint}: {e.response.text}"
        ) from e
    except httpx.RequestError as e:
        raise RuntimeError(
            f"Network error on {method} {endpoint}: {e}"
        ) from e


# ---------------------------------------------------------------------------
# Public API helpers
# ---------------------------------------------------------------------------

def get_athlete() -> dict:
    """Fetch the authenticated athlete's profile."""
    return _make_request("GET", "/athlete")  # type: ignore[return-value]


def get_athlete_activities(per_page: int = 10, page: int = 1) -> list:
    """
    Fetch a page of the athlete's recent activities.
    """
    return _make_request(  # type: ignore[return-value]
        "GET",
        "/athlete/activities",
        params={"per_page": per_page, "page": page},
    )


def get_activity_details(activity_id: int) -> dict:
    """
    Fetch full details for a specific activity, including splits and segments.
    """
    return _make_request("GET", f"/activities/{activity_id}")  # type: ignore[return-value]


def get_athlete_stats(athlete_id: int) -> dict:
    """
    Fetch lifetime statistics for a specific athlete.
    """
    return _make_request("GET", f"/athletes/{athlete_id}/stats")  # type: ignore[return-value]
