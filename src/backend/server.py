import json
import os
import shutil
import tempfile
import fastapi
import uvicorn
from typing import Any
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from .download import fetch_track
from .sync import apply_metadata, detect_apple_music_dir
from .spotify import Spotify
from .utils.objects import Track

class SettingsUpdateRequest(BaseModel):
    spotify_client_id: str
    spotify_client_secret: str
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
            "sync_dir": detect_apple_music_dir() or ""
        }
        # State: track the last search result so client can reference it by key
        self.current_search_result: dict[str, Any] | None = None
        self.current_tracks_by_key: dict[str, Track] = {}
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
                if not results:
                    return None
                
                # Store result in server state for later reference
                result_dict = results.__dict__ if results else {}
                self.current_search_result = result_dict
                
                # Index tracks by key (id) for quick lookup on download
                self.current_tracks_by_key = {}
                
                # If it's a single track
                if hasattr(results, 'isrc') and hasattr(results, 'name'):
                    track_id = getattr(results, 'id', None) or getattr(results, 'isrc', None)
                    if track_id:
                        self.current_tracks_by_key[track_id] = results
                
                # If it has multiple tracks (album, playlist, artist)
                if hasattr(results, 'tracks'):
                    for track in results.tracks:
                        track_id = getattr(track, 'id', None) or getattr(track, 'isrc', None)
                        if track_id:
                            self.current_tracks_by_key[track_id] = track
                
                return result_dict
            except Exception as e:
                return JSONResponse(status_code=500, content={"error": str(e)})

        @self.app.post("/api/download")
        async def download(payload: dict):
            """Download track(s) by key.
            
            Client sends: {"track_key": "isrc_or_id"}
            Server resolves from stored state (from last search).
            """
            try:
                track_key = payload.get("track_key")
                if not track_key:
                    return JSONResponse(
                        status_code=400,
                        content={"ok": False, "error": "track_key is required. Search for a track first."},
                    )
                
                if track_key not in self.current_tracks_by_key:
                    return JSONResponse(
                        status_code=400,
                        content={"ok": False, "error": f"Track key '{track_key}' not found in server state. Search for a track first."},
                    )
                
                track_obj = self.current_tracks_by_key[track_key]
                tracks = [track_obj]
                format = self.config["format"]

                async def stream_downloads():
                    results: list[dict[str, Any]] = []
                    for track_obj in tracks:
                        result_track_key = getattr(track_obj, "id", None) or getattr(track_obj, "isrc", None)
                        yield json.dumps(
                            {
                                "type": "track-start",
                                "track_key": result_track_key,
                                "track": track_obj.name,
                            }
                        ) + "\n"
                        with tempfile.TemporaryDirectory() as temp_dir:
                            try:
                                file = await fetch_track(track_obj, temp_dir, format)
                                await apply_metadata(file, track_obj)
                                
                                # Determine destination directory
                                dest_dir = self.config.get("sync_dir") or ""
                                if not dest_dir:
                                    # Fallback to a default if sync_dir is not set
                                    dest_dir = os.path.expanduser("~/Music/SpotiPod Downloads")
                                    os.makedirs(dest_dir, exist_ok=True)
                                
                                # Move file to destination
                                dest_path = os.path.join(dest_dir, file.name)
                                shutil.move(str(file), dest_path)
                                
                                result = {
                                    "track": track_obj.name,
                                    "track_key": result_track_key,
                                    "ok": True,
                                }
                                results.append(result)
                                yield json.dumps({"type": "track-done", **result}) + "\n"
                            except Exception as exc:
                                result = {
                                    "track": track_obj.name,
                                    "track_key": result_track_key,
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
                "metadata": bool(payload.metadata),
                "auto_sync": bool(payload.auto_sync),
                "format": payload.format.strip() or "aac",
            })

            return {
                "ok": True
            }
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        uvicorn.run(self.app, host=host, port=port)       
