import json
import asyncio
from src.spotify import Spotify
from src.download import fetch
from src.utils.objects import Track, Album, Artist, Playlist

async def main():
    with open("config.json") as f:
        config = json.load(f)
    
    client_id = config["SPOTIFY_CLIENT_ID"]
    client_secret = config["SPOTIFY_CLIENT_SECRET"]
    
    if not client_id or not client_secret:
        raise ValueError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set")
    
    spotify = Spotify(client_id, client_secret)
    uri = input("Enter Spotify URL or search query: ").strip()
    track = None
    result = await spotify.search(uri)
    print(result.__dict__)
    if type(result) == Track:
        tracks = [result]
    else:
        tracks = result.tracks
    for track in tracks:
        fetch(track)
        
if __name__ == "__main__":
    asyncio.run(main())