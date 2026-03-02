from __future__ import annotations

from typing import Any
from .utils.objects import Track
import yt_dlp


#Searches for best match to track based on duration. I would like to make this use ISRC but many hooks are broken as of now.
def scsearch(track: Track) -> dict[str, Any]:
    search_url = f"scsearch:{track.artists} {track.name}"
    print(search_url)
    opts: dict[str, Any] = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": False,
    }
	
    with yt_dlp.YoutubeDL(opts) as ydl:
        result = ydl.extract_info(search_url, download=False)
	
    if not isinstance(result, dict) or not result.get("entries"):
        raise RuntimeError("No results returned from scsearch")

    entries = result["entries"]

    # Ensure Spotify duration is in seconds
    spotify_duration = track.length / 1000

    best_match = None
    smallest_diff = float("inf")

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        duration = entry.get("duration")
        if duration is None:
            continue

        diff = abs(duration - spotify_duration)

        if diff < smallest_diff:
            smallest_diff = diff
            best_match = entry

    if best_match:
        return best_match

    raise RuntimeError("No suitable duration match found")