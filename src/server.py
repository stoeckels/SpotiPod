import json
import os
from typing import Any

import fastapi
import uvicorn
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .spotify import Spotify


class SettingsUpdateRequest(BaseModel):
    spotify_client_id: str
    spotify_client_secret: str
    download_path: str = ""


class Client:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.spotify = None
        self.app = fastapi.FastAPI()
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self._ensure_config_file()
        self._refresh_spotify_client()
        self._setup_routes()

    def _ensure_config_file(self):
        if os.path.exists(self.config_path):
            return

        with open(self.config_path, "w") as f:
            json.dump(
                {
                    "SPOTIFY_CLIENT_ID": "",
                    "SPOTIFY_CLIENT_SECRET": "",
                    "download_path": "",
                },
                f,
                indent=4,
            )

    def _read_config(self) -> dict[str, Any]:
        self._ensure_config_file()
        with open(self.config_path) as f:
            data = json.load(f)
        return {
            "SPOTIFY_CLIENT_ID": data.get("SPOTIFY_CLIENT_ID", ""),
            "SPOTIFY_CLIENT_SECRET": data.get("SPOTIFY_CLIENT_SECRET", ""),
            "download_path": data.get("download_path", ""),
        }

    def _write_config(self, config: dict[str, Any]):
        with open(self.config_path, "w") as f:
            json.dump(config, f, indent=4)

    def _refresh_spotify_client(self):
        config = self._read_config()
        client_id = config["SPOTIFY_CLIENT_ID"].strip()
        client_secret = config["SPOTIFY_CLIENT_SECRET"].strip()

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
                return results
            except Exception as e:
                return JSONResponse(status_code=500, content={"error": str(e)})

        @self.app.get("/api/settings")
        async def get_settings():
            config = self._read_config()
            return {
                "spotify_client_id": config["SPOTIFY_CLIENT_ID"],
                "spotify_client_secret": config["SPOTIFY_CLIENT_SECRET"],
                "download_path": config["download_path"],
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