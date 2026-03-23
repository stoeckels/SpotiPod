from __future__ import annotations

from typing import Any
from .utils.objects import Track
import yt_dlp


def fetch(track: Track, download: bool = True) -> dict[str, Any]:
    if track.isrc == None:
        search_url = f"ytsearch:{track.name} {track.artists}"
    else:
        search_url = f"ytsearch:{track.isrc}"

    opts: dict[str, Any] = {
        "quiet": True,
        "format": "bestaudio/best",
        "extract_flat": False,
    }
	
    with yt_dlp.YoutubeDL(opts) as ydl:
        result = ydl.extract_info(search_url, download=download)
	
    if not isinstance(result, dict) or not result.get("entries"):
        raise RuntimeError("No results returned from ytsearch")
    
    return result["entries"][0]