from __future__ import annotations

import asyncio
from typing import Any
from .utils.objects import Track
import yt_dlp

async def fetch_track(
    track: Track,
    output_dir: str,
    audio_format: str = "aac",
) -> dict[str, Any]:
    if track.isrc is None:
        search_url = f"ytsearch:{track.name} {track.artists}"
    else:
        search_url = f"ytsearch:{track.isrc}"

    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "format": "bestaudio/best",
        "extract_flat": False,
        "noplaylist": True,
        "outtmpl": f"{output_dir}/%(title).%(ext)s",
        "windowsfilenames": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format,
                "preferredquality": "0",
            }
        ],
    }

    def _download():
        with yt_dlp.YoutubeDL(opts) as ydl:
            result = ydl.extract_info(search_url)
        if not isinstance(result, dict) or not result.get("entries"):
            raise RuntimeError("No results returned from ytsearch")
        return result.items

    return await asyncio.to_thread(_download)
