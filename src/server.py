import asyncio
from pathlib import Path
from typing import Any
from types import SimpleNamespace

import fastapi
import uvicorn
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .download import fetch
from .sync import process_downloaded_track
from .spotify import Spotify
from .utils.objects import Track, Album, Artist, Playlist


class SettingsUpdateRequest(BaseModel):
    spotify_client_id: str
    spotify_client_secret: str
    download_path: str = ""
    metadata_processing: str = "standard"
    format_selection: str = "mp3"


class TrackModel(BaseModel):
    id: str | None = None
    name: str
    artists: str
    length: float
    formatted_length: str
    album: str | None = None
    album_artist: str | None = None
    track_number: int | None = None
    isrc: str | None = None
    image: str | None = None
    uri: str | None = None


class PlaylistModel(BaseModel):
    id: str | None = None
    name: str
    owner: str
    image: str | None = None
    uri: str | None = None
    tracks: list[TrackModel] = Field(default_factory=list)
    total_tracks: int = 0
    total_duration: str


class AlbumModel(BaseModel):
    id: str | None = None
    name: str
    artists: str
    image: str | None = None
    uri: str | None = None
    upc: str | None = None
    tracks: list[TrackModel] = Field(default_factory=list)
    total_tracks: int = 0
    total_duration: str


class ArtistModel(BaseModel):
    id: str | None = None
    name: str
    image: str | None = None
    uri: str | None = None
    tracks: list[TrackModel] = Field(default_factory=list)
    total_tracks: int = 0
    total_duration: str


class DownloadRequest(BaseModel):
    object_type: str  # "track", "album", "playlist", or "artist"
    object_data: TrackModel | PlaylistModel | AlbumModel | ArtistModel


class Client:
    def __init__(self):
        self._config: dict[str, Any] = {
            "SPOTIFY_CLIENT_ID": "",
            "SPOTIFY_CLIENT_SECRET": "",
            "download_path": "",
            "metadata_processing": "standard",
            "format_selection": "mp3",
        }
        self.spotify = None
        self.app = fastapi.FastAPI()
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self._refresh_spotify_client()
        self._setup_routes()

    def _read_config(self) -> dict[str, Any]:
        return self._config.copy()

    def _write_config(self, config: dict[str, Any]):
        self._config = config.copy()

    def _refresh_spotify_client(self):
        config = self._read_config()
        client_id = config["SPOTIFY_CLIENT_ID"].strip()
        client_secret = config["SPOTIFY_CLIENT_SECRET"].strip()

        if not client_id or not client_secret:
            self.spotify = None
            return

        self.spotify = Spotify(client_id, client_secret)

    def _serialize_result(self, result: Track | Album | Artist | Playlist | None) -> dict | None:
        """Convert domain objects to serializable dicts."""
        if result is None:
            return None
        elif isinstance(result, Track):
            return result.to_dict()
        elif isinstance(result, Album):
            return result.to_dict()
        elif isinstance(result, Artist):
            return result.to_dict()
        elif isinstance(result, Playlist):
            return result.to_dict()
        return None

    def _setup_routes(self):
        @self.app.get("/")
        async def index():
            return {"service": "SpotiPod API", "status": "ok"}
        
        @self.app.get("/api/search")
        async def search(uri: str):
            if not self.spotify:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Spotify credentials are not set. Open Settings and add your client ID and secret.",
                    },
                )
            try:
                results = await self.spotify.search(uri)
                return self._serialize_result(results)
            except Exception as e:
                return JSONResponse(status_code=500, content={"error": str(e)})

        @self.app.post("/api/download")
        async def download(payload: DownloadRequest):
            """Download a track, album, playlist, or artist's top tracks."""
            try:
                config = self._read_config()
                data = payload.object_data.model_dump()
                object_type = payload.object_type.strip().lower()

                if object_type == "track":
                    tracks = [data]
                else:
                    tracks = data.get("tracks", [])

                if not tracks:
                    return JSONResponse(
                        status_code=400,
                        content={"ok": False, "error": "No tracks found to download."},
                    )

                target_dir = Path(config.get("download_path", "") or "downloads").expanduser()
                target_dir.mkdir(parents=True, exist_ok=True)

                def run_downloads() -> dict[str, Any]:
                    results: list[dict[str, Any]] = []
                    for item in tracks:
                        track_obj = SimpleNamespace(
                            name=item.get("name", "Unknown Track"),
                            artists=item.get("artists", ""),
                            album=item.get("album") or "",
                            album_artist=item.get("album_artist") or item.get("artists", ""),
                            track_number=item.get("track_number") or 0,
                            isrc=item.get("isrc"),
                        )
                        try:
                            entry = fetch(
                                track_obj,
                                output_dir=str(target_dir),
                                audio_format=config.get("format_selection", "mp3"),
                            )
                            sync_result = process_downloaded_track(
                                track=track_obj,
                                entry=entry,
                                output_dir=str(target_dir),
                                audio_format=config.get("format_selection", "mp3"),
                                metadata_mode=config.get("metadata_processing", "standard"),
                            )
                            results.append(
                                {
                                    "track": track_obj.name,
                                    "ok": True,
                                    "source_title": entry.get("title", ""),
                                    "file_path": sync_result.get("file_path"),
                                    "metadata_applied": sync_result.get("metadata_applied", False),
                                    "synced_to_apple_music": sync_result.get("synced_to_apple_music", False),
                                    "apple_music_path": sync_result.get("apple_music_path"),
                                    "warning": sync_result.get("warning"),
                                }
                            )
                        except Exception as exc:
                            results.append(
                                {
                                    "track": track_obj.name,
                                    "ok": False,
                                    "error": str(exc),
                                }
                            )

                    downloaded_count = sum(1 for r in results if r["ok"])
                    failed_count = len(results) - downloaded_count
                    return {
                        "ok": failed_count == 0,
                        "downloaded_count": downloaded_count,
                        "failed_count": failed_count,
                        "download_path": str(target_dir),
                        "results": results,
                    }

                summary = await asyncio.to_thread(run_downloads)
                if summary["failed_count"] > 0:
                    return JSONResponse(status_code=207, content=summary)

                return summary
            except Exception as e:
                return JSONResponse(status_code=500, content={"error": str(e)})
        
        @self.app.get("/api/settings")
        async def get_settings():
            config = self._read_config()
            return {
                "spotify_client_id": config["SPOTIFY_CLIENT_ID"],
                "spotify_client_secret": config["SPOTIFY_CLIENT_SECRET"],
                "download_path": config["download_path"],
                "metadata_processing": config["metadata_processing"],
                "format_selection": config["format_selection"],
                "tokens_populated": bool(
                    config["SPOTIFY_CLIENT_ID"].strip()
                    and config["SPOTIFY_CLIENT_SECRET"].strip()
                ),
            }

        @self.app.put("/api/settings")
        async def update_settings(payload: SettingsUpdateRequest):
            next_config = {
                "SPOTIFY_CLIENT_ID": payload.spotify_client_id.strip(),
                "SPOTIFY_CLIENT_SECRET": payload.spotify_client_secret.strip(),
                "download_path": payload.download_path.strip(),
                "metadata_processing": payload.metadata_processing.strip() or "standard",
                "format_selection": payload.format_selection.strip() or "mp3",
            }

            self._write_config(next_config)
            self._refresh_spotify_client()

            return {
                "ok": True,
                "tokens_populated": bool(
                    next_config["SPOTIFY_CLIENT_ID"]
                    and next_config["SPOTIFY_CLIENT_SECRET"]
                ),
            }
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        uvicorn.run(self.app, host=host, port=port)
