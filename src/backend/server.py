import json
import shutil
import tempfile
import fastapi
import uvicorn
from typing import Any
from types import SimpleNamespace
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from .download import fetch_track
from .sync import apply_metadata, detect_apple_music_dir
from .spotify import Spotify
from .utils.objects import Track, Album, Artist, Playlist

class SettingsUpdateRequest(BaseModel):
    spotify_client_id: str
    spotify_client_secret: str
    download_path: str = ""
    metadata: bool = True
    auto_sync: bool = True
    format: str = "aac"

class Client:
    def __init__(self):
        self.config: dict[str, Any] = {
            "SPOTIFY_CLIENT_ID": "",
            "SPOTIFY_CLIENT_SECRET": "",
            "metadata": True,
            "auto_sync": True,
            "format": "aac",
            "sync_dir": str(detect_apple_music_dir() or ""),
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


    def _refresh_spotify_client(self):
        client_id = self.config["SPOTIFY_CLIENT_ID"].strip()
        client_secret = self.config["SPOTIFY_CLIENT_SECRET"].strip()

        if not client_id or not client_secret:
            self.spotify = None
            return

        self.spotify = Spotify(client_id, client_secret)

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
                return results.__dict__ if results else None
            except Exception as e:
                return JSONResponse(status_code=500, content={"error": str(e)})

        @self.app.post("/api/download")
        async def download(payload: dict):
            """Download a track, album, playlist, or artist's top tracks."""
            try:
                data = payload.get("object_data", {})
                object_type = (payload.get("object_type") or "").strip().lower()

                if object_type == "track":
                    tracks = [data]
                else:
                    tracks = data.get("tracks", [])

                if not tracks:
                    return JSONResponse(
                        status_code=400,
                        content={"ok": False, "error": "No tracks found to download."},
                    )

                format = self.config["format"]

                async def stream_downloads():
                    results: list[dict[str, Any]] = []
                    for item in tracks:
                        track_obj = SimpleNamespace(
                            name=item.get("name", "Unknown Track"),
                            artists=item.get("artists", ""),
                            album=item.get("album") or "",
                            album_artist=item.get("album_artist") or item.get("artists", ""),
                            track_number=item.get("track_number") or 0,
                            total_tracks=item.get("total_tracks") or 0,
                            year=item.get("year") or 0,
                            image=item.get("image"),
                            isrc=item.get("isrc"),
                        )
                        yield json.dumps(
                            {
                                "type": "track-start",
                                "track_key": track_obj.isrc,
                                "track": track_obj.name,
                            }
                        ) + "\n"
                        with tempfile.TemporaryDirectory() as temp_dir:
                            try:
                                file = await fetch_track(track_obj, temp_dir, format)
                                await apply_metadata(file, track_obj)
                                shutil.move(file, self.config["sync_dir"])
                                result = {
                                    "track": track_obj.name,
                                    "track_key": track_obj.isrc,
                                    "ok": True,
                                }
                                results.append(result)
                                yield json.dumps({"type": "track-done", **result}) + "\n"
                            except Exception as exc:
                                result = {
                                    "track": track_obj.name,
                                    "track_key": track_obj.isrc,
                                    "ok": False,
                                    "error": str(exc),
                                }
                                results.append(result)
                                yield json.dumps({"type": "track-done", **result}) + "\n"

                    downloaded_count = sum(1 for r in results if r["ok"])
                    failed_count = len(results) - downloaded_count
                    yield json.dumps(
                        {
                            "type": "summary",
                            "ok": failed_count == 0,
                            "downloaded_count": downloaded_count,
                            "failed_count": failed_count,
                            "results": results,
                        }
                    ) + "\n"

                return StreamingResponse(stream_downloads(), media_type="application/x-ndjson")
            except Exception as e:
                return JSONResponse(status_code=500, content={"error": str(e)})
        
        @self.app.get("/api/settings")
        async def get_settings():
            return {
                "spotify_client_id": self.config["SPOTIFY_CLIENT_ID"],
                "spotify_client_secret": self.config["SPOTIFY_CLIENT_SECRET"],
                "download_path": self.config["download_path"],
                "metadata": bool(self.config.get("metadata", False)),
                "auto_sync": bool(self.config.get("auto_sync", False)),
                "sync_dir": detect_apple_music_dir() is not None,
                "format": self.config["format"],
            }

        @self.app.put("/api/settings")
        async def update_settings(payload: SettingsUpdateRequest):
            csecret = payload.spotify_client_secret.strip()
            if csecret != self.config["SPOTIFY_CLIENT_SECRET"].strip():
                self.config["SPOTIFY_CLIENT_ID"] = payload.spotify_client_id.strip()
                self.config["SPOTIFY_CLIENT_SECRET"] = payload.spotify_client_secret.strip()
                self._refresh_spotify_client()

            self.config.update({
                "download_path": payload.download_path.strip(),
                "metadata": bool(payload.metadata),
                "auto_sync": bool(payload.auto_sync),
                "format": payload.format.strip() or "aac",
            })

            return {
                "ok": True
            }
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        uvicorn.run(self.app, host=host, port=port, log_level=None)       
