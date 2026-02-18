class Track:
    def __init__(self, raw: dict):
        self.id = raw["id"]
        self.name = raw["name"]
        self.duration_ms = raw["duration_ms"]
        self.explicit = raw["explicit"]
        self.popularity = raw["popularity"]
        self.album_id = raw["album"]["id"]
        self.artists = [Artist(artist) for artist in raw["artists"]]
        self.isrc = raw["external_ids"]["isrc"]

class Album:
    def __init__(self, raw: dict):
        self.id = raw["id"]
        self.name = raw["name"]
        self.release_date = raw["release_date"]
        self.total_tracks = raw["total_tracks"]
        self.tracks = [Track(track) for track in raw["tracks"]["items"]]
        self.artist_ids = [artist["id"] for artist in raw["artists"]]

class Artist:
    def __init__(self, raw: dict):
        self.id = raw["id"]
        self.name = raw["name"]


class Playlist:
    def __init__(self, raw: dict):
        self.id = raw["id"]
        self.name = raw["name"]
        self.description = raw["description"]
        self.owner_id = raw["owner"]["id"]
        self.tracks = [Track(track["track"]) for track in raw["tracks"]["items"]]
