from aiohttp import ClientSession

class Spotify:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = "https://accounts.spotify.com/api/token"
        self.api_base_url = "https://api.spotify.com/v1"
        self.access_token = None

    async def get_track(self, track_uri: str):
        
    