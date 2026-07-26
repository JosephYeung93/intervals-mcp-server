"""
Athlete-profile MCP tools for Intervals.icu.

This module provides:
- A module-level cache of the athlete's account record (name, city, country, timezone)
  to avoid hitting the /athlete/{id} endpoint on every activity/message lookup.
- A helper other tools use to resolve the athlete's IANA timezone, for converting UTC
  timestamps that don't carry their own local-time field (e.g. activity messages).
- A user-facing MCP tool `get_athlete_profile` so the assistant can look up the athlete's
  Intervals.icu-registered location/timezone (e.g. during onboarding) instead of asking.

The raw /athlete/{id} response also carries account secrets (e.g. icu_api_key) and PII
(email) that this server has no reason to hold onto or ever surface. Only a small
allow-list of fields is extracted before caching or returning anything from this module.
"""

from typing import Any

from intervals_mcp_server.api.client import make_intervals_request
from intervals_mcp_server.config import get_config
from intervals_mcp_server.utils.formatting import format_athlete_profile
from intervals_mcp_server.utils.validation import resolve_athlete_id

# Import mcp instance from shared module for tool registration
from intervals_mcp_server.mcp_instance import mcp  # noqa: F401

config = get_config()

_PROFILE_FIELDS = ("id", "name", "city", "country", "timezone")

# Module-level cache of the filtered athlete record, keyed by athlete_id.
_ATHLETE_CACHE: dict[str, dict[str, Any]] = {}


def _filter_profile_fields(raw: dict[str, Any]) -> dict[str, Any]:
    """Keep only the allow-listed fields from a raw /athlete/{id} response."""
    return {field: raw.get(field) for field in _PROFILE_FIELDS}


async def get_athlete_record(
    athlete_id: str | None = None,
    api_key: str | None = None,
    *,
    refresh: bool = False,
) -> dict[str, Any]:
    """Return (and cache) the athlete's account record, filtered to a small allow-list.

    One API call per athlete per process lifetime unless refresh=True. On error, returns
    the error dict as-is (not cached) so callers can surface or ignore it.

    Args:
        athlete_id: Athlete to look up. Defaults to ATHLETE_ID env var via config.
        api_key: Override the configured API key.
        refresh: If True, ignore the cache and re-fetch from the API.
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg or not athlete_id_to_use:
        return {"error": True, "message": error_msg or "Missing athlete ID."}

    if not refresh and athlete_id_to_use in _ATHLETE_CACHE:
        return _ATHLETE_CACHE[athlete_id_to_use]

    result = await make_intervals_request(url=f"/athlete/{athlete_id_to_use}", api_key=api_key)
    if isinstance(result, dict) and "error" not in result:
        filtered = _filter_profile_fields(result)
        _ATHLETE_CACHE[athlete_id_to_use] = filtered
        return filtered
    if isinstance(result, dict):
        return result
    return {"error": True, "message": "Unexpected response fetching athlete record."}


async def get_athlete_timezone(
    athlete_id: str | None = None,
    api_key: str | None = None,
) -> str | None:
    """Return the athlete's IANA timezone name from Intervals.icu, or None if unavailable."""
    athlete = await get_athlete_record(athlete_id=athlete_id, api_key=api_key)
    if "error" in athlete:
        return None
    tz = athlete.get("timezone")
    return tz if isinstance(tz, str) and tz else None


@mcp.tool()
async def get_athlete_profile(
    athlete_id: str | None = None,
    api_key: str | None = None,
    refresh: bool = False,
) -> str:
    """Get the athlete's Intervals.icu account profile (name, city, country, timezone).

    Useful during onboarding to pull location/timezone instead of asking the athlete
    directly. Cached for the MCP process lifetime; pass refresh=True to re-fetch.

    Args:
        athlete_id: The Intervals.icu athlete ID (optional, will use ATHLETE_ID from .env if not provided)
        api_key: The Intervals.icu API key (optional, will use API_KEY from .env if not provided)
        refresh: If True, bypass the cache and re-fetch from the API (default False)
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    athlete = await get_athlete_record(athlete_id=athlete_id_to_use, api_key=api_key, refresh=refresh)
    if "error" in athlete:
        return f"Error fetching athlete profile: {athlete.get('message')}"

    return format_athlete_profile(athlete)
