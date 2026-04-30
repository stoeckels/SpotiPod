from __future__ import annotations

import asyncio
import os
import shutil
import urllib.request
from pathlib import Path
from typing import Any

from mutagen.id3 import APIC, ID3, ID3NoHeaderError, TALB, TPE1, TPE2, TIT2, TRCK, TDRC
from mutagen.mp4 import MP4, MP4Cover

from .utils.objects import Track


def detect_apple_music_dir() -> Path | None:
	# Explicit override for any platform

	home = Path.home()
	candidates = [
		# macOS
		home / "Music/Music/Media.localized/Automatically Add to Music.localized",
		home / "Music/iTunes/iTunes Media/Automatically Add to iTunes",
		# Windows
		home / "Music/iTunes/iTunes Media/Automatically Add to iTunes",
		home / "Music/Apple Music/Media/Automatically Add to Music",
		# Linux / custom installs
		home / "Music/Apple Music/Automatically Add to Music",
	]

	for candidate in candidates:
		if candidate.is_dir():
			return candidate

	return None

def _download_cover_art(image_url: str) -> tuple[bytes, str]:
	request = urllib.request.Request(image_url, headers={"User-Agent": "SpotiPod/1.0"})
	with urllib.request.urlopen(request, timeout=15) as response:
		content_type = response.headers.get_content_type() or "image/jpeg"
		image_bytes = response.read()
	return image_bytes, content_type

def _apply_metadata_sync(file: Path, track: Track) -> None:
	cover_bytes, cover_type = _download_cover_art(track.image)

	if file.suffix.lower() == ".m4a":
		audio = MP4(file)
		audio["\xa9nam"] = [track.name]
		audio["\xa9ART"] = [track.artists]
		audio["\xa9alb"] = [track.album]
		if track.track_number:
			try:
				audio["trkn"] = [(int(track.track_number), track.total_tracks or 0)]
			except (ValueError, TypeError):
				pass
		if track.year:
			audio["\xa9day"] = [str(track.year)]
		audio["covr"] = [MP4Cover(cover_bytes, imageformat=_cover_format_from_content_type(cover_type))]
		audio.save()
		return

	if file.suffix.lower() == ".mp3":
		try:
			audio = ID3(file)
		except ID3NoHeaderError:
			audio = ID3()
		mime_type = cover_type or "image/jpeg"
		audio.add(
				APIC(
					encoding=3,
					mime=mime_type,
					type=3,
					desc="Cover",
					data=cover_bytes,
				)
			)
		audio.save(file)
		return
	
	audio.add(TIT2(encoding=3, text=track.name))
	audio.add(TPE1(encoding=3, text=track.artists))
	audio.add(TALB(encoding=3, text=track.album))
	audio.add(TPE2(encoding=3, text=track.album_artist))
	audio.add(TRCK(encoding=3, text=str(track.track_number)))
	audio.save(file)


async def apply_metadata(file: Path, track: Track) -> None:
	await asyncio.to_thread(_apply_metadata_sync, file, track)