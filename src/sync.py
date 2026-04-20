from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

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


def _apply_metadata(file: Path, track: Track) -> None:
	if not file.is_file():
		raise FileNotFoundError(f"Downloaded file not found: {file}")

	title = _safe_meta(track.name)
	artist = _safe_meta(track.artists)
	album = _safe_meta(track.album)
	album_artist = _safe_meta(track.album_artist) or artist
	track_number = _safe_meta(track.track_number)

	tmp_file = file.with_name(f"{file.stem}.metadata_tmp{file.suffix}")
	cmd: list[str] = [
		"ffmpeg",
		"-y",
		"-i",
		str(file),
		"-map_metadata",
		"0",
		"-codec",
		"copy",
	]

	metadata_pairs = [
		("title", title),
		("artist", artist),
		("album", album),
		("album_artist", album_artist),
		("track", track_number),
	]
	for key, value in metadata_pairs:
		if value:
			cmd.extend(["-metadata", f"{key}={value}"])

	cmd.append(str(tmp_file))

	try:
		result = subprocess.run(cmd, capture_output=True, text=True, check=False)
		if result.returncode != 0:
			raise RuntimeError((result.stderr or "ffmpeg metadata update failed").strip())
		tmp_file.replace(file)
	finally:
		if tmp_file.exists():
			tmp_file.unlink(missing_ok=True)


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

