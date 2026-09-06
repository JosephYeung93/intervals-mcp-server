"""
Unit tests for formatting utilities in intervals_mcp_server.utils.formatting.

These tests verify that the formatting functions produce expected output strings for activities, workouts, wellness entries, events, and intervals.
"""

import json
from intervals_mcp_server.utils import formatting
from intervals_mcp_server.utils.formatting import (
    format_activity_summary,
    format_activity_message,
    format_athlete_profile,
    format_workout,
    format_wellness_entry,
    format_event_summary,
    format_event_details,
    format_intervals,
    format_power_curves,
)
from tests.sample_data import INTERVALS_DATA


def test_format_activity_summary():
    """
    Test that format_activity_summary returns a string containing the activity name and ID.
    """
    data = {
        "name": "Morning Ride",
        "id": 1,
        "type": "Ride",
        "startTime": "2024-01-01T08:00:00Z",
        "distance": 1000,
        "duration": 3600,
    }
    result = format_activity_summary(data)
    assert "Activity: Morning Ride" in result
    assert "ID: 1" in result


def test_format_activity_summary_uses_start_date_local_as_is():
    """
    Test that format_activity_summary prefers start_date_local over the UTC start_date,
    with no timezone conversion needed since it's already local wall-clock time.
    """
    data = {
        "name": "Kurnell loop",
        "id": "i169230762",
        "type": "Ride",
        "start_date": "2026-07-25T20:36:22Z",
        "start_date_local": "2026-07-26T06:36:22",
        "distance": 1000,
        "duration": 3600,
    }
    result = format_activity_summary(data)
    assert "Date: 2026-07-26 06:36:22" in result


def test_format_activity_summary_falls_back_to_converted_utc():
    """
    Test that format_activity_summary converts the UTC start_date using the supplied
    local timezone when start_date_local is absent (e.g. a manually-entered activity).
    """
    data = {
        "name": "Manual entry",
        "id": "i1",
        "type": "Ride",
        "start_date": "2026-07-25T20:36:22Z",
        "distance": 1000,
        "duration": 3600,
    }
    result = format_activity_summary(data, local_tz="Australia/Sydney")
    assert "Date: 2026-07-26 06:36:22" in result


def test_format_activity_summary_falls_back_to_raw_utc_without_timezone():
    """
    Test that format_activity_summary keeps its original UTC-string behavior when neither
    start_date_local nor a local_tz is available, rather than silently guessing.
    """
    data = {
        "name": "Morning Ride",
        "id": 1,
        "type": "Ride",
        "startTime": "2024-01-01T08:00:00Z",
        "distance": 1000,
        "duration": 3600,
    }
    result = format_activity_summary(data)
    assert "Date: 2024-01-01 08:00:00" in result


def test_format_activity_message_converts_created_using_local_timezone():
    """
    Test that format_activity_message converts the UTC created timestamp into local time
    when a timezone is supplied, since messages don't carry their own local field.
    """
    message = {
        "name": "Coach",
        "created": "2026-07-25T20:36:22Z",
        "type": "TEXT",
        "content": "Nice work out there",
    }
    result = format_activity_message(message, local_tz="Australia/Sydney")
    assert "Date: 2026-07-26 06:36:22" in result


def test_format_activity_message_falls_back_to_raw_utc_without_timezone():
    """
    Test that format_activity_message keeps its original UTC-string behavior when no
    local_tz is supplied.
    """
    message = {
        "name": "Coach",
        "created": "2024-06-15T11:00:00Z",
        "type": "TEXT",
        "content": "Good effort despite that!",
    }
    result = format_activity_message(message)
    assert "Date: 2024-06-15 11:00:00" in result


def test_format_athlete_profile():
    """
    Test that format_athlete_profile returns a string containing the athlete's
    location and timezone.
    """
    athlete = {
        "id": "i1",
        "name": "Joseph Yeung",
        "city": "Sydney",
        "country": "Australia",
        "timezone": "Australia/Sydney",
    }
    result = format_athlete_profile(athlete)
    assert "Name: Joseph Yeung" in result
    assert "City: Sydney" in result
    assert "Country: Australia" in result
    assert "Timezone: Australia/Sydney" in result


def test_format_athlete_profile_missing_fields_show_not_available():
    """
    Test that format_athlete_profile shows "N/A" rather than the literal string "None"
    for fields the athlete hasn't set on their Intervals.icu account.
    """
    athlete = {"id": "i1", "name": "Joseph Yeung", "city": None, "country": None, "timezone": None}
    result = format_athlete_profile(athlete)
    assert "City: N/A" in result
    assert "Country: N/A" in result
    assert "Timezone: N/A" in result
    assert "None" not in result


def test_format_workout():
    """
    Test that format_workout returns a string containing the workout name and interval count.
    """
    workout = {
        "name": "Workout1",
        "description": "desc",
        "sport": "Ride",
        "duration": 3600,
        "tss": 50,
        "intervals": [1, 2, 3],
    }
    result = format_workout(workout)
    assert "Workout: Workout1" in result
    assert "Intervals: 3" in result


def test_format_wellness_entry():
    """
    Test that format_wellness_entry returns a string containing the date and fitness (CTL).
    """
    with open("tests/ressources/wellness_entry.json", "r", encoding="utf-8") as f:
        entry = json.load(f)
    result = format_wellness_entry(entry)

    with open("tests/ressources/wellness_entry_formatted.txt", "r", encoding="utf-8") as f:
        expected_result = f.read()
    assert result == expected_result


def test_format_wellness_entry_include_all_fields():
    """
    Test that format_wellness_entry with include_all_fields=True includes additional unknown fields.
    """
    entry = {
        "id": "2024-06-01",
        "ctl": 80,
        "weight": 75,
        "customField1": "hello",
        "customField2": 42,
        "updated": "2024-06-01T10:00:00Z",
    }
    result = format_wellness_entry(entry, include_all_fields=True)
    assert "Date: 2024-06-01" in result
    assert "Fitness (CTL): 80" in result
    assert "Weight: 75 kg" in result
    assert "Other Fields:" in result
    assert "customField1: hello" in result
    assert "customField2: 42" in result
    # "updated" is a known built-in field, should not appear in Other Fields
    assert "updated:" not in result


def test_format_wellness_entry_no_extra_fields_by_default():
    """
    Test that format_wellness_entry without include_all_fields does not include additional fields.
    """
    entry = {
        "id": "2024-06-01",
        "ctl": 80,
        "customField1": "hello",
    }
    result = format_wellness_entry(entry)
    assert "Other Fields:" not in result
    assert "customField1" not in result


def test_format_wellness_entry_macros_populated():
    """
    Test that format_wellness_entry renders native nutrition macros
    (carbohydrates, protein, fatTotal) in grams when present.
    """
    entry = {
        "id": "2026-04-08",
        "carbohydrates": 310,
        "protein": 145,
        "fatTotal": 72,
    }
    result = format_wellness_entry(entry)
    assert "Nutrition & Hydration:" in result
    assert "- Carbohydrates: 310 g" in result
    assert "- Protein: 145 g" in result
    assert "- Fat: 72 g" in result


# --- Wellness projections (ADR-0016 / #119 in ai-cycling-coach): future rows are a do-nothing decay
# forecast, structurally identical to a measured row apart from their date, so the label lives on the
# Date: line itself rather than a header. "Today" is pinned via `formatting.get_default_end_date` -- the
# same clock the module compares against -- so these tests never depend on the real wall clock.


def test_format_wellness_entry_labels_a_future_date_as_projected(monkeypatch):
    """AC1: exact wording, on the Date: line."""
    monkeypatch.setattr(formatting, "get_default_end_date", lambda: "2026-09-06")
    entry = {"id": "2026-09-16", "ctl": 67.7}

    result = format_wellness_entry(entry)

    assert (
        "Date: 2026-09-16 — PROJECTED (future date; interval.icu decay forecast, not measured)" in result
    )


def test_format_wellness_entry_todays_date_is_never_labelled(monkeypatch):
    """AC2: today's own row is a measurement, not a projection."""
    monkeypatch.setattr(formatting, "get_default_end_date", lambda: "2026-09-06")
    entry = {"id": "2026-09-06", "ctl": 85.9}

    result = format_wellness_entry(entry)

    assert "Date: 2026-09-06\n" in result
    assert "PROJECTED" not in result


def test_format_wellness_entry_past_date_is_never_labelled(monkeypatch):
    """AC2: byte-identical rendering for a past date is what makes this change purely additive."""
    monkeypatch.setattr(formatting, "get_default_end_date", lambda: "2026-09-06")
    entry = {"id": "2026-08-20", "ctl": 80}

    result = format_wellness_entry(entry)

    assert "Date: 2026-08-20\n" in result
    assert "PROJECTED" not in result


def test_format_wellness_entry_still_returns_future_rows_unfiltered(monkeypatch):
    """AC6: labelling, never filtering -- "what does my form look like if I rest all week?" must keep
    working."""
    monkeypatch.setattr(formatting, "get_default_end_date", lambda: "2026-09-06")
    entry = {"id": "2026-09-16", "ctl": 67.7}

    result = format_wellness_entry(entry)

    assert "Fitness (CTL): 67.7" in result


def test_format_wellness_entry_missing_date_renders_unlabelled_not_raising(monkeypatch):
    """AC7: the existing 'N/A' fallback for a missing id must stay unlabelled, not crash."""
    monkeypatch.setattr(formatting, "get_default_end_date", lambda: "2026-09-06")
    entry = {"ctl": 80}

    result = format_wellness_entry(entry)

    assert "Date: N/A" in result
    assert "PROJECTED" not in result


def test_format_wellness_entry_unparseable_date_renders_unlabelled_not_raising(monkeypatch):
    """AC7: a date string interval.icu doesn't actually send, defensively -- must not raise."""
    monkeypatch.setattr(formatting, "get_default_end_date", lambda: "2026-09-06")
    entry = {"id": "not-a-date", "ctl": 80}

    result = format_wellness_entry(entry)

    assert "Date: not-a-date" in result
    assert "PROJECTED" not in result


def test_format_wellness_entry_projection_label_is_on_the_date_line_itself(monkeypatch):
    """AC3: the label rides the date line, not a header, so it survives one entry quoted in isolation."""
    monkeypatch.setattr(formatting, "get_default_end_date", lambda: "2026-09-06")
    entry = {"id": "2026-09-16", "ctl": 67.7}

    result = format_wellness_entry(entry)

    date_line = result.splitlines()[1]
    assert (
        date_line
        == "Date: 2026-09-16 — PROJECTED (future date; interval.icu decay forecast, not measured)"
    )


def test_format_wellness_entry_projection_uses_the_same_clock_as_get_default_end_date(monkeypatch):
    """AC4: comparing against `get_default_end_date()` itself -- not a second, separately-derived notion
    of "today" -- is what this test actually pins; changing what that function returns is the only knob."""
    monkeypatch.setattr(formatting, "get_default_end_date", lambda: "2026-01-01")
    entry = {"id": "2026-06-15", "ctl": 80}  # future under the patched clock, past under the real one

    result = format_wellness_entry(entry)

    assert "PROJECTED" in result


def test_format_event_summary_never_labels_future_dated_events(monkeypatch):
    """AC5: scoped to wellness. A future-dated calendar event is the athlete's real planned session, and
    format_event_summary must render one exactly as it always has."""
    monkeypatch.setattr(formatting, "get_default_end_date", lambda: "2026-09-06")
    event = {"date": "2026-09-16", "name": "Long ride", "id": 1}

    result = format_event_summary(event)

    assert "PROJECTED" not in result
    assert "Date: 2026-09-16" in result


def test_format_wellness_entry_macros_null_hidden():
    """
    Test that format_wellness_entry hides macro lines when the fields are null,
    preserving backward compatibility with older wellness records.
    """
    entry = {
        "id": "2026-04-08",
        "ctl": 80,
        "carbohydrates": None,
        "protein": None,
        "fatTotal": None,
    }
    result = format_wellness_entry(entry)
    assert "Carbohydrates" not in result
    assert "Protein" not in result
    # "Fat" could legitimately appear inside e.g. "Body Fat" elsewhere, so
    # anchor the negative assertion on the line-prefix form we would emit.
    assert "- Fat:" not in result


def test_format_event_summary():
    """
    Test that format_event_summary returns a string containing the event date and type.
    """
    event = {
        "start_date_local": "2024-01-01",
        "id": "e1",
        "name": "Event1",
        "description": "desc",
        "race": True,
    }
    summary = format_event_summary(event)
    assert "Date: 2024-01-01" in summary
    assert "Type: Race" in summary


def test_format_event_details():
    """
    Test that format_event_details returns a string containing event and workout details.
    """
    event = {
        "id": "e1",
        "date": "2024-01-01",
        "name": "Event1",
        "description": "desc",
        "workout": {
            "id": "w1",
            "sport": "Ride",
            "duration": 3600,
            "tss": 50,
            "intervals": [1, 2],
        },
        "race": True,
        "priority": "A",
        "result": "1st",
        "calendar": {"name": "Main"},
    }
    details = format_event_details(event)
    assert "Event Details:" in details
    assert "Workout Information:" in details


def test_format_intervals():
    """
    Test that format_intervals returns a string containing interval analysis and the interval label.
    """
    result = format_intervals(INTERVALS_DATA)
    assert "Intervals Analysis:" in result
    assert "Rep 1" in result


def test_format_power_curves():
    """
    Test that format_power_curves returns a concise string with curve labels,
    power values, W/kg values, and activity IDs.
    """
    curves = [
        {
            "id": "s0",
            "label": "This season",
            "start": "2025-09-29T00:00:00",
            "end": "2026-03-14T00:00:00",
            "data_points": [
                {"secs": 5, "watts": 780, "activity_id": "i100", "watts_per_kg": 10.4, "wkg_activity_id": "i100"},
                {"secs": 60, "watts": 380, "activity_id": "i102", "watts_per_kg": 5.07, "wkg_activity_id": "i102"},
                {"secs": 3600, "watts": 210, "activity_id": "i107", "watts_per_kg": 2.8, "wkg_activity_id": "i107"},
            ],
        },
    ]
    result = format_power_curves(curves, "Ride", include_normalised=True)
    assert "Power Curves (Ride):" in result
    assert "This season" in result
    assert "5s: 780W" in result
    assert "10.40W/kg" in result
    assert "1m: 380W" in result
    assert "1h: 210W" in result
    assert "i100" in result
    assert "i107" in result


def test_format_power_curves_without_normalised():
    """
    Test that format_power_curves without normalised data does not include W/kg.
    """
    curves = [
        {
            "id": "s0",
            "label": "This season",
            "start": "",
            "end": "",
            "data_points": [
                {"secs": 5, "watts": 780, "activity_id": "i100"},
            ],
        },
    ]
    result = format_power_curves(curves, "Ride", include_normalised=False)
    assert "780W" in result
    assert "W/kg" not in result
