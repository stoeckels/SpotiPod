from __future__ import annotations

import os
import shutil
from pathlib import Path

import yt_dlp

from .download import fetch
from .utils.objects import Track


def _detect_apple_music_dir() -> Path | None:
	# Explicit override for any platform.
	override = os.getenv("SPOTIPOD_APPLE_MUSIC_DIR")
	if override:
		candidate = Path(override).expanduser()
		if candidate.is_dir():
			return candidate

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


def _ensure_temp_dir() -> Path:
	temp_dir = Path.cwd() / "temp_downloads"
	temp_dir.mkdir(parents=True, exist_ok=True)
	return temp_dir


def _download_url(url: str, temp_dir: Path) -> None:
	if not url.strip():
		raise ValueError("No URL provided")

	opts = {
		"format": "bestaudio/best",
		"outtmpl": str(temp_dir / "%(playlist_index,autonumber)02d - %(title)s.%(ext)s"),
		"quiet": False,
		"noplaylist": False,
		"postprocessors": [
			{
				"key": "FFmpegExtractAudio",
				"preferredcodec": "m4a",
				"preferredquality": "0",
			},
			{"key": "EmbedThumbnail"},
			{"key": "FFmpegMetadata"},
		],
		"postprocessor_args": {"ffmpeg": ["-aac_pns", "0", "-metadata", "comment="]},
		"parse_metadata": [
			"uploader:%(artist)s",
			"%(playlist_title)s:%(album)s",
			"%(playlist_uploader)s:%(album_artist)s",
			"title:%(title)s",
			"%(playlist_index)s:%(track_number)s",
			"%(genre)s:%(genre)s",
		],
		"replace_in_metadata": [
			["album", "NA", ""],
			["album_artist", "NA", ""],
			["genre", "NA", ""],
			["track_number", "NA", ""],
		],
	}

	with yt_dlp.YoutubeDL(opts) as ydl:
		ydl.download([url])


def _move_downloads(temp_dir: Path, music_dir: Path | None) -> list[Path]:
	if music_dir is None or not music_dir.is_dir():
		return []

	moved_files: list[Path] = []
	for src in temp_dir.glob("*.m4a"):
		dst = music_dir / src.name
		shutil.move(str(src), str(dst))
		moved_files.append(dst)
	return moved_files


def sync_url_to_music(url: str) -> list[Path]:
	temp_dir = _ensure_temp_dir()
	_download_url(url, temp_dir)
	return _move_downloads(temp_dir, _detect_apple_music_dir())


def sync_track_to_music(track: Track) -> list[Path]:
	search_result = fetch(track, download=False)
	url = search_result.get("webpage_url") or search_result.get("url")
	if not url:
		raise RuntimeError(f"Could not resolve a media URL for track: {track.name}")
	return sync_url_to_music(url)
