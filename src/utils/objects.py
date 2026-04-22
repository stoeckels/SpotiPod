from typing import List
from typing import Optional

from .format import format_summary_duration, format_track_duration

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
        self.formatted_length: str = format_track_duration(self.length)
        self.id: str = data["id"]
        self.album: Optional[str] = None
        self.track_number: Optional[int] = None
        self.total_tracks: Optional[int] = None
        album = data.get("album")
        if album:
            album_type = album.get("album_type")
            total_tracks = int(album.get("total_tracks") or 0)
            if album_type != "single" or total_tracks > 1:
                self.album = album.get("name")
                self.track_number = data.get("track_number")
                self.total_tracks = album.get("total_tracks")
        self.year: Optional[int] = None
        if album and album.get("release_date"):
            self.year = int(str(album["release_date"])[:4])
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
        self.total_duration: str = format_summary_duration(sum(track.length for track in self.tracks))
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
        self.total_duration: str = format_summary_duration(sum(track.length for track in self.tracks))
        self.uri: str = data["external_urls"]["spotify"]
        self.upc: Optional[str] = None
        if data.get("external_ids"):
            self.upc = data["external_ids"].get("upc")

class Artist:
    def __init__(self, data: dict, tracks: dict) -> None:
        self.name: str = (
            f"Top tracks for {data['name']}"
        )
        self.image: str = data["images"][0]["url"]
        self.tracks = [Track(track, image=self.image) for track in tracks]
        self.total_duration: str = format_summary_duration(sum(track.length for track in self.tracks))
        self.uri: str = data["external_urls"]["spotify"]