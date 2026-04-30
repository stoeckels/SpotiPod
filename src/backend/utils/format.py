def format_track_duration(duration_ms: int | float) -> str:
    total_seconds = int(duration_ms // 1000)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"


def format_summary_duration(duration_ms: int | float) -> str:
    total_minutes = int(duration_ms // 60000)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if hours == 0:
        return f"{minutes} min"
    return f"{hours} hr {minutes} min"
