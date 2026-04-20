from __future__ import annotations

from typing import Any
from .utils.objects import Track
import yt_dlp

def fetch(
    track: Track,
    *,
    output_dir: str | None = None,
    audio_format: str = "mp3",
) -> dict[str, Any]:
    if track.isrc is None:
        search_url = f"ytsearch:{track.name} {track.artists}"
    else:
        search_url = f"ytsearch:{track.isrc}"

    opts: dict[str, Any] = {
        "quiet": True,
        "format": "bestaudio/best",
        "extract_flat": False,
        "noplaylist": True,
    }

    target_dir = output_dir or "downloads"
    opts.update(
        {
            "outtmpl": f"{target_dir}/%(title).180s.%(ext)s",
            "windowsfilenames": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": audio_format,
                    "preferredquality": "0",
                }
            ],
        }
    )
	
    with yt_dlp.YoutubeDL(opts) as ydl:
        result = ydl.extract_info(search_url)

    if not isinstance(result, dict) or not result.get("entries"):
        raise RuntimeError("No results returned from ytsearch")
    
    return result["entries"][0]
