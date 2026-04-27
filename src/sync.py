from __future__ import annotations

import os
import shutil
import urllib.request
from pathlib import Path
from typing import Any

from mutagen.id3 import APIC, ID3, ID3NoHeaderError, TALB, TPE1, TPE2, TIT2, TRCK, TDRC
from mutagen.mp4 import MP4, MP4Cover

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


def _normalize_mode(mode: str | None) -> str:
	value = (mode or "standard").strip().lower()
	if value in {"none", "off"}:
		return "none"
	if value in {"enhanced", "apple_music"}:
		return "enhanced"
	return "standard"


def _resolve_downloaded_file(
	entry: dict[str, Any],
	*,
	output_dir: Path,
	audio_format: str,
) -> Path | None:
	requested = entry.get("requested_downloads")
	if isinstance(requested, list):
		for item in requested:
			if not isinstance(item, dict):
				continue
			candidate = item.get("filepath") or item.get("_filename")
			if candidate and Path(candidate).is_file():
				return Path(candidate)

	for key in ("filepath", "_filename", "filename"):
		candidate = entry.get(key)
		if candidate and Path(candidate).is_file():
			return Path(candidate)

	ext = audio_format.lower().strip(".")
	files = sorted(output_dir.glob(f"*.{ext}"), key=lambda p: p.stat().st_mtime, reverse=True)
	if files:
		return files[0]

	# Fallback for mismatched extension settings: use the newest common audio file.
	fallback_files = sorted(
		[
			*output_dir.glob("*.mp3"),
			*output_dir.glob("*.m4a"),
			*output_dir.glob("*.flac"),
			*output_dir.glob("*.wav"),
		],
		key=lambda p: p.stat().st_mtime,
		reverse=True,
	)
	if fallback_files:
		return fallback_files[0]

	return None


def _safe_meta(value: Any) -> str:
	if value is None:
		return ""
	return str(value).strip()


def _safe_int(value: Any) -> int | None:
	if value in (None, ""):
		return None
	try:
		return int(value)
	except (TypeError, ValueError):
		return None


def _download_cover_art(image_url: str) -> tuple[bytes, str]:
	request = urllib.request.Request(image_url, headers={"User-Agent": "SpotiPod/1.0"})
	with urllib.request.urlopen(request, timeout=15) as response:
		content_type = response.headers.get_content_type() or "image/jpeg"
		image_bytes = response.read()
	return image_bytes, content_type


def _cover_format_from_content_type(content_type: str) -> int:
	if content_type.lower() == "image/png":
		return MP4Cover.FORMAT_PNG
	return MP4Cover.FORMAT_JPEG


def _apply_metadata(file: Path, track: Track) -> None:
	if not file.is_file():
		raise FileNotFoundError(f"Downloaded file not found: {file}")

	title = _safe_meta(track.name)
	artist = _safe_meta(track.artists)
	album = _safe_meta(track.album)
	album_artist = _safe_meta(track.album_artist) or artist
	track_number = _safe_meta(track.track_number)
	total_tracks = _safe_int(getattr(track, "total_tracks", None))
	year = _safe_int(getattr(track, "year", None))
	image_url = _safe_meta(track.image)
	cover_bytes: bytes | None = None
	cover_type = "image/jpeg"
	if image_url:
		cover_bytes, cover_type = _download_cover_art(image_url)
	if file.suffix.lower() == ".m4a":
		audio = MP4(file)
		audio["\xa9nam"] = [title]
		audio["\xa9ART"] = [artist]
		if album:
			audio["\xa9alb"] = [album]
		if album_artist:
			audio["aART"] = [album_artist]
		if track_number:
			track_index = int(track_number)
			audio["trkn"] = [(track_index, total_tracks or 0)]
		if year:
			audio["\xa9day"] = [str(year)]
		if cover_bytes:
			audio["covr"] = [MP4Cover(cover_bytes, imageformat=_cover_format_from_content_type(cover_type))]
		audio.save()
		return

	if file.suffix.lower() == ".mp3":
		try:
			audio = ID3(file)
		except ID3NoHeaderError:
			audio = ID3()
		audio.add(TIT2(encoding=3, text=title))
		audio.add(TPE1(encoding=3, text=artist))
		if album:
			audio.add(TALB(encoding=3, text=album))
		if album_artist:
			audio.add(TPE2(encoding=3, text=album_artist))
		if track_number:
			track_text = str(track_number)
			if total_tracks:
				track_text = f"{track_text}/{total_tracks}"
			audio.add(TRCK(encoding=3, text=track_text))
		if year:
			audio.add(TDRC(encoding=3, text=str(year)))
		if cover_bytes:
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

	# Fallback for other audio containers that may still appear in downloads.
	try:
		audio = ID3(file)
	except ID3NoHeaderError:
		audio = ID3()
	audio.add(TIT2(encoding=3, text=title))
	audio.add(TPE1(encoding=3, text=artist))
	if album:
		audio.add(TALB(encoding=3, text=album))
	if album_artist:
		audio.add(TPE2(encoding=3, text=album_artist))
	if track_number:
		audio.add(TRCK(encoding=3, text=str(track_number)))
	audio.save(file)


def _sync_to_apple_music(file: Path) -> Path | None:
	apple_music_dir = _detect_apple_music_dir()
	if apple_music_dir is None:
		return None

	destination = apple_music_dir / file.name
	if destination.exists():
		stem = file.stem
		suffix = file.suffix
		counter = 1
		while destination.exists():
			destination = apple_music_dir / f"{stem} ({counter}){suffix}"
			counter += 1

	shutil.copy2(file, destination)
	return destination


def process_downloaded_track(
	*,
	track: Track,
	entry: dict[str, Any],
	output_dir: str,
	audio_format: str,
	metadata_mode: str,
) -> dict[str, Any]:
	mode = _normalize_mode(metadata_mode)
	output_path = Path(output_dir).expanduser()
	output_path.mkdir(parents=True, exist_ok=True)
	file = _resolve_downloaded_file(entry, output_dir=output_path, audio_format=audio_format)

	if file is None:
		return {
			"file_path": None,
			"metadata_applied": False,
			"synced_to_apple_music": False,
			"apple_music_path": None,
			"warning": "Downloaded file could not be resolved for metadata processing.",
		}

	metadata_applied = False
	apple_music_path: str | None = None

	if mode != "none":
		_apply_metadata(file, track)
		metadata_applied = True

	if mode == "enhanced":
		synced = _sync_to_apple_music(file)
		if synced is not None:
			apple_music_path = str(synced)

	return {
		"file_path": str(file),
		"metadata_applied": metadata_applied,
		"synced_to_apple_music": apple_music_path is not None,
		"apple_music_path": apple_music_path,
	}
