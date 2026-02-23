from typing import List
from typing import Optional

__all__ = (
    "Track",
    "Playlist",
    "Album",
    "Artist",
)


class Track:
    def __init__(self, data: dict, image: Optional[str] = None) -> None:
        self.name: str = data["name"]
        self.artists: str = ", ".join(artist["name"] for artist in data["artists"])
        self.length: float = data["duration_ms"]
        self.id: str = data["id"]

        self.isrc: Optional[str] = None
        if data.get("external_ids"):
            self.isrc = data["external_ids"]["isrc"]

        self.image: Optional[str] = image
        if data.get("album") and data["album"].get("images"):
            self.image = data["album"]["images"][0]["url"]

        self.uri: Optional[str] = None
        if not data["is_local"]:
            self.uri = data["external_urls"]["spotify"]


class Playlist:

    def __init__(self, data: dict, tracks: List[Track]) -> None:
        self.name: str = data["name"]
        self.tracks = tracks
        self.owner: str = data["owner"]["display_name"]
        self.total_tracks: int = data["tracks"]["total"]
        self.id: str = data["id"]
        if data.get("images") and len(data["images"]):
            self.image = data["images"][0]["url"]
        else:
            self.image = self.tracks[0].image
        self.uri = data["external_urls"]["spotify"]


class Album:
    def __init__(self, data: dict) -> None:
        self.name: str = data["name"]
        self.artists: str = ", ".join(artist["name"] for artist in data["artists"])
        self.image: str = data["images"][0]["url"]
        self.tracks = [Track(track, image=self.image) for track in data["tracks"]["items"]]
        self.total_tracks: int = data["total_tracks"]
        self.id: str = data["id"]
        self.uri: str = data["external_urls"]["spotify"]


class Artist:
    def __init__(self, data: dict, tracks: dict) -> None:
        self.name: str = (
            f"Top tracks for {data['name']}"
        )
        self.image: str = data["images"][0]["url"]
        self.tracks = [Track(track, image=self.image) for track in tracks]
        self.id: str = data["id"]
        self.uri: str = data["external_urls"]["spotify"]
