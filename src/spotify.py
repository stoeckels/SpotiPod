import aiohttp
import time
import orjson as json
import re
from base64 import b64encode

from .utils.objects import Track, Album, Artist, Playlist

type_re = re.compile(
    r"^https?://open\.spotify\.com/(track|playlist|artist|album)/([A-Za-z0-9]{22})(?:\?.*)?$"
)

def parse_spotify_url(url: str):
    m = type_re.match(url)
    if not m:
        return None
    return {"type": m.group(1), "id": m.group(2)}

API_TOKEN_URL = "https://accounts.spotify.com/api/token"
API_URL = "https://api.spotify.com/v1/{type}s/{id}"
API_SEARCH_URL = "https://api.spotify.com/v1/search?query={query}&type={type}&limit={limit}"

class Spotify:
    def __init__(self, client_id, client_secret):
        self.session = None
        self._client_id = client_id
        self._api_expiry = 0.0
        self._api_headers: dict  = None
        self._auth_token = b64encode(f"{client_id}:{client_secret}".encode())
        self._grant_headers = {"Authorization": f"Basic {self._auth_token.decode()}"}
    
    async def _get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def _fetch_api_bearer(self):
        session = await self._get_session()
        resp = await session.post(API_TOKEN_URL, data={"grant_type": "client_credentials"}, headers=self._grant_headers)
        data = await resp.json(loads=json.loads)
        self._bearer_token = data["access_token"]
        self._api_expiry = time.time() + int(data["expires_in"])
        self._api_headers = {
            "Authorization": f"Bearer {self._bearer_token}",
        }

    async def _api_expiry_check(self):
        if not self.session:
            await self._get_session()
        if not self._api_headers or time.time() >= self._api_expiry:
            await self._fetch_api_bearer()
    
    async def search(self, uri: str) -> dict:
        """Searches for Spotify items by type either "track", "album", or "artist"."""
        await self._api_expiry_check()
        parsed = parse_spotify_url(uri)
        if not parsed:
            raise ValueError("Invalid Spotify URL")

        resource_type = parsed["type"]
        resource_id = parsed["id"]

        resp = await self.session.get(
            API_URL.format(type=resource_type, id=resource_id),
            headers=self._api_headers
        )

        resp.raise_for_status()
        data = await resp.json(loads=json.loads)

        if resource_type == "playlist":
            tracks = []
            playlist_data = data
            page = playlist_data["tracks"]

            # Spotify paginates playlist tracks, so we need to fetch them all
            while True:
                for item in page["items"]:
                    tracks.append(Track(item["track"]))
                if page["next"] is None:
                    break
                resp = await self.session.get(page["next"], headers=self._api_headers)
                resp.raise_for_status()
                page = await resp.json(loads=json.loads)
            return Playlist(playlist_data, tracks)
        
        parser_map = {
            "track": Track,
            "album": Album,
            "artist": Artist,
        }

        parser_class = parser_map.get(data.get("type"))
        if not parser_class:
            return data

        return parser_class(data)
