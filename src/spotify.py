import aiohttp
import time
import orjson as json
from base64 import b64encode

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
        if not self._api_headers or time.time() >= self._api_expiry:
            await self._fetch_api_bearer()

    async def search(self, type: str, limit: int, query: str) -> dict:
        """Searches for Spotify items by type either "track", "album", or "artist"."""
        await self._api_expiry_check()
        session = await self._get_session()
        resp = await session.get(API_SEARCH_URL.format(type=type, limit=limit, query=query), headers=self._api_headers)
        data = await resp.json(loads=json.loads)
        return data
    
    async def track_by_id(self, track_id: str) -> dict:
        """Fetch Spotify track data from Spotify API."""
        await self._api_expiry_check()
        session = await self._get_session()
        resp = await session.get(API_URL.format(type="track", id=track_id), headers=self._api_headers)
        data = await resp.json(loads=json.loads)
        return data
    
    async def get_artist(self, artist_id: str) -> dict:
        """Fetch Spotify artist data from Spotify API."""
        await self._api_expiry_check()
        session = await self._get_session()
        resp = await session.get(API_URL.format(type="artist", id=artist_id), headers=self._api_headers)
        data = await resp.json(loads=json.loads)
        return data
