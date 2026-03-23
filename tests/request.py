import json
import asyncio
from src.spotify import Spotify
from src.sync import sync_track_to_music
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
        moved_files = sync_track_to_music(track)
        print(f"Downloaded and moved {len(moved_files)} file(s) for: {track.name}")
        
if __name__ == "__main__":
    asyncio.run(main())