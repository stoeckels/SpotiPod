from __future__ import annotations

import asyncio
import glob
from pathlib import Path
from typing import Any
from .utils.objects import Track
import yt_dlp

async def fetch_track(
    track: Track,
    output_dir: str,
    audio_format: str = "aac",
) -> Path:
    if track.isrc is None:
        search_url = f"ytsearch1:{track.name} {track.artists}"
    else:
        search_url = f"ytsearch1:{track.isrc}"

    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "format": "bestaudio/best",
        "extract_flat": False,
        "noplaylist": True,
        "outtmpl": f"{output_dir}/%(id)s.%(ext)s",
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
        
        if not isinstance(result, dict):
            raise RuntimeError(f"Unexpected result type: {type(result)}")
        
        # Try to find the file in the result
        filepath = None
        if result.get("filepath"):
            filepath = result["filepath"]
        elif result.get("_filename"):
            filepath = result["_filename"]
        
        if filepath:
            return Path(filepath)
        
        # Fallback: glob for the newest file in output_dir
        files = sorted(glob.glob(f"{output_dir}/*"), key=lambda p: Path(p).stat().st_mtime, reverse=True)
        if files:
            return Path(files[0])
        
        raise RuntimeError("Could not locate downloaded file")

    return await asyncio.to_thread(_download)
