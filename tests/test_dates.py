"""
Unit tests for date utility functions in intervals_mcp_server.utils.dates.
"""

from intervals_mcp_server.utils.dates import to_local_datetime_str


def test_to_local_datetime_str_converts_utc_to_local():
    """A UTC ISO timestamp with a Z suffix converts to the target zone's wall-clock time."""
    result = to_local_datetime_str("2026-07-25T20:36:22Z", "Australia/Sydney")
    assert result == "2026-07-26 06:36:22"


def test_to_local_datetime_str_converts_utc_offset_form():
    """A UTC ISO timestamp with an explicit +00:00 offset converts the same as a Z suffix."""
    result = to_local_datetime_str("2026-07-25T20:36:22+00:00", "Australia/Sydney")
    assert result == "2026-07-26 06:36:22"


def test_to_local_datetime_str_assumes_utc_when_naive():
    """A timestamp with no timezone info is treated as UTC before converting."""
    result = to_local_datetime_str("2026-07-25T20:36:22", "Australia/Sydney")
    assert result == "2026-07-26 06:36:22"


def test_to_local_datetime_str_returns_none_without_timezone():
    """No timezone name means no conversion can be done; caller decides the fallback."""
    assert to_local_datetime_str("2026-07-25T20:36:22Z", None) is None
    assert to_local_datetime_str("2026-07-25T20:36:22Z", "") is None


def test_to_local_datetime_str_returns_none_for_invalid_timezone():
    """An unrecognized IANA timezone name fails safe rather than raising."""
    assert to_local_datetime_str("2026-07-25T20:36:22Z", "Not/AZone") is None


def test_to_local_datetime_str_returns_none_for_malformed_timezone_key():
    """A malformed timezone key (ZoneInfo raises ValueError, not ZoneInfoNotFoundError
    for these) fails safe rather than raising."""
    assert to_local_datetime_str("2026-07-25T20:36:22Z", "../etc/passwd") is None


def test_to_local_datetime_str_returns_none_for_unparsable_timestamp():
    """A timestamp that isn't valid ISO-8601 fails safe rather than raising."""
    assert to_local_datetime_str("not-a-timestamp", "Australia/Sydney") is None
