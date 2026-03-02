import os
import asyncio
from dotenv import load_dotenv
from src.spotify import Spotify
from src.ytdlp import scsearch

load_dotenv()

async def main():
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise ValueError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set")
    
    spotify = Spotify(client_id, client_secret)
    uri = input("Enter Spotify URL or search query: ").strip()
    track = None
    result = await spotify.search(uri)
    if hasattr(result, "tracks") and isinstance(result.tracks, list):
        for track in result.tracks:
            print(track.__dict__)
        track = result.tracks[0] if result.tracks else None
    else:
        track = result
    if track:
        ytdlp_result = scsearch(track)
        print("Best match:", ytdlp_result)
        
if __name__ == "__main__":
    asyncio.run(main())