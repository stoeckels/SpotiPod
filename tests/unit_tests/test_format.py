from src.backend.utils.format import format_summary_duration, format_track_duration


def test_format_track_duration_rounds_down_and_pads_seconds():
    assert format_track_duration(185000) == "3:05"
    assert format_track_duration(59999) == "0:59"


def test_format_summary_duration_minutes_and_hours():
    assert format_summary_duration(59_000) == "0 min"
    assert format_summary_duration(125 * 60_000) == "2 hr 5 min"
