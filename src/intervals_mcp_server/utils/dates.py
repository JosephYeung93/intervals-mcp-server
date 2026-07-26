"""
Date utility functions for Intervals.icu MCP Server.

This module provides helper functions for date parsing and default date calculations.
"""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def get_default_start_date(days_ago: int = 30) -> str:
    """
    Get a default start date string in YYYY-MM-DD format.

    Args:
        days_ago: Number of days ago from today. Defaults to 30.

    Returns:
        Date string in YYYY-MM-DD format.
    """
    return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")


def get_default_end_date() -> str:
    """
    Get today's date string in YYYY-MM-DD format.

    Returns:
        Date string in YYYY-MM-DD format.
    """
    return datetime.now().strftime("%Y-%m-%d")


def get_default_future_end_date(days_ahead: int = 30) -> str:
    """
    Get a default future end date string in YYYY-MM-DD format.

    Args:
        days_ahead: Number of days ahead from today. Defaults to 30.

    Returns:
        Date string in YYYY-MM-DD format.
    """
    return (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")


def to_local_datetime_str(utc_iso: str, tz_name: str | None) -> str | None:
    """Convert a UTC ISO-8601 timestamp into a local wall-clock string for the given timezone.

    Args:
        utc_iso: A UTC timestamp, either with an explicit offset/Z suffix or naive (assumed UTC).
        tz_name: An IANA timezone name (e.g. "Australia/Sydney"), or None/empty if unknown.

    Returns:
        The local wall-clock time as "YYYY-MM-DD HH:MM:SS", or None if tz_name is missing,
        utc_iso can't be parsed, or tz_name isn't a recognized timezone — callers fall back
        to displaying the raw value rather than a silently wrong one.
    """
    if not tz_name:
        return None
    try:
        dt = datetime.fromisoformat(utc_iso.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    try:
        local_dt = dt.astimezone(ZoneInfo(tz_name))
    except ZoneInfoNotFoundError:
        return None
    return local_dt.strftime("%Y-%m-%d %H:%M:%S")


def parse_date_range(
    start_date: str | None, end_date: str | None, default_start_days_ago: int = 30
) -> tuple[str, str]:
    """
    Parse and validate a date range, providing defaults if needed.

    Args:
        start_date: Start date in YYYY-MM-DD format (optional).
        end_date: End date in YYYY-MM-DD format (optional).
        default_start_days_ago: Number of days ago for default start date. Defaults to 30.

    Returns:
        Tuple of (start_date, end_date) as strings in YYYY-MM-DD format.
    """
    if not start_date:
        start_date = get_default_start_date(default_start_days_ago)
    if not end_date:
        end_date = get_default_end_date()
    return start_date, end_date
