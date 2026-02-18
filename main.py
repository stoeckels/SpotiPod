import os
from dotenv import load_dotenv
from src.spotify import Spotify
from src.server import Client

load_dotenv()

def main():
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise ValueError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set")
    
    spotify = Spotify(client_id, client_secret)
    
    #Base for future frontend impementation
    client = Client(spotify)
    client.run(port=8000)

if __name__ == "__main__":
    main()