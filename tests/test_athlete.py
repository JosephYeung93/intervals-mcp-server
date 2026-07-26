"""
Unit tests for athlete-profile tools in intervals_mcp_server.tools.athlete.
"""

import asyncio

from intervals_mcp_server.tools import athlete as athlete_module
from intervals_mcp_server.tools.athlete import (
    get_athlete_profile,
    get_athlete_record,
    get_athlete_timezone,
)


def _reset_athlete_cache():
    """Helper to clear the module-level athlete cache between tests."""
    athlete_module._ATHLETE_CACHE.clear()  # pylint: disable=protected-access


def test_get_athlete_profile(monkeypatch):
    """Test get_athlete_profile returns a formatted string with location/timezone."""
    _reset_athlete_cache()

    sample = {
        "id": "i1",
        "name": "Joseph Yeung",
        "city": "Sydney",
        "country": "Australia",
        "timezone": "Australia/Sydney",
        "email": "should-not-appear@example.com",
        "icu_api_key": "should-not-appear-either",
    }

    async def fake_request(*_args, **_kwargs):
        return sample

    monkeypatch.setattr("intervals_mcp_server.api.client.make_intervals_request", fake_request)
    monkeypatch.setattr(
        "intervals_mcp_server.tools.athlete.make_intervals_request", fake_request
    )
    result = asyncio.run(get_athlete_profile(athlete_id="i1"))
    assert "Name: Joseph Yeung" in result
    assert "City: Sydney" in result
    assert "Timezone: Australia/Sydney" in result
    # Sensitive fields from the raw account record must never be surfaced.
    assert "should-not-appear" not in result


def test_get_athlete_profile_missing_athlete_id(monkeypatch):
    """Test get_athlete_profile errors clearly when no athlete ID is available."""
    _reset_athlete_cache()

    async def fake_request(*_args, **_kwargs):
        raise AssertionError("should not be called without a resolved athlete id")

    monkeypatch.setattr("intervals_mcp_server.api.client.make_intervals_request", fake_request)
    monkeypatch.setattr(
        "intervals_mcp_server.tools.athlete.make_intervals_request", fake_request
    )
    monkeypatch.setattr(athlete_module.config, "athlete_id", "")
    result = asyncio.run(get_athlete_profile(athlete_id=None))
    assert "Error" in result


def test_get_athlete_record_caches_and_refreshes(monkeypatch):
    """Test that the athlete record is cached per-process and refresh=True busts the cache."""
    _reset_athlete_cache()

    call_count = {"n": 0}
    sample = {"id": "i1", "name": "Joseph", "city": "Sydney", "country": "Australia", "timezone": "Australia/Sydney"}

    async def fake_request(*_args, **_kwargs):
        call_count["n"] += 1
        return sample

    monkeypatch.setattr("intervals_mcp_server.api.client.make_intervals_request", fake_request)
    monkeypatch.setattr(
        "intervals_mcp_server.tools.athlete.make_intervals_request", fake_request
    )

    asyncio.run(get_athlete_record(athlete_id="i1"))
    assert call_count["n"] == 1

    asyncio.run(get_athlete_record(athlete_id="i1"))
    assert call_count["n"] == 1

    asyncio.run(get_athlete_record(athlete_id="i1", refresh=True))
    assert call_count["n"] == 2


def test_get_athlete_timezone_returns_value(monkeypatch):
    """Test get_athlete_timezone extracts the timezone field from the athlete record."""
    _reset_athlete_cache()

    sample = {"id": "i1", "timezone": "Australia/Sydney"}

    async def fake_request(*_args, **_kwargs):
        return sample

    monkeypatch.setattr("intervals_mcp_server.api.client.make_intervals_request", fake_request)
    monkeypatch.setattr(
        "intervals_mcp_server.tools.athlete.make_intervals_request", fake_request
    )
    result = asyncio.run(get_athlete_timezone(athlete_id="i1"))
    assert result == "Australia/Sydney"


def test_get_athlete_timezone_returns_none_on_error(monkeypatch):
    """Test get_athlete_timezone fails safe (returns None) when the API call errors."""
    _reset_athlete_cache()

    async def fake_request(*_args, **_kwargs):
        return {"error": True, "message": "Unauthorized"}

    monkeypatch.setattr("intervals_mcp_server.api.client.make_intervals_request", fake_request)
    monkeypatch.setattr(
        "intervals_mcp_server.tools.athlete.make_intervals_request", fake_request
    )
    result = asyncio.run(get_athlete_timezone(athlete_id="i1"))
    assert result is None


def test_get_athlete_timezone_returns_none_when_missing_athlete_id(monkeypatch):
    """Test get_athlete_timezone fails safe (returns None) with no resolvable athlete id."""
    _reset_athlete_cache()

    async def fake_request(*_args, **_kwargs):
        raise AssertionError("should not be called without a resolved athlete id")

    monkeypatch.setattr("intervals_mcp_server.api.client.make_intervals_request", fake_request)
    monkeypatch.setattr(
        "intervals_mcp_server.tools.athlete.make_intervals_request", fake_request
    )
    monkeypatch.setattr(athlete_module.config, "athlete_id", "")
    result = asyncio.run(get_athlete_timezone(athlete_id=None))
    assert result is None


def test_get_athlete_record_does_not_cache_sensitive_fields(monkeypatch):
    """Test that the cached athlete record never retains secrets/PII beyond the allow-list."""
    _reset_athlete_cache()

    sample = {
        "id": "i1",
        "name": "Joseph",
        "city": "Sydney",
        "country": "Australia",
        "timezone": "Australia/Sydney",
        "email": "joseph@example.com",
        "icu_api_key": "super-secret-key",
    }

    async def fake_request(*_args, **_kwargs):
        return sample

    monkeypatch.setattr("intervals_mcp_server.api.client.make_intervals_request", fake_request)
    monkeypatch.setattr(
        "intervals_mcp_server.tools.athlete.make_intervals_request", fake_request
    )
    asyncio.run(get_athlete_record(athlete_id="i1"))
    cached = athlete_module._ATHLETE_CACHE["i1"]  # pylint: disable=protected-access
    assert "email" not in cached
    assert "icu_api_key" not in cached
