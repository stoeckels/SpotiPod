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
    def __init__(self, data: dict, album: Optional["Album"] = None, image: Optional[str] = None) -> None:
        self.name: str = data.get("name", "Unknown")
        self.artists: str = ", ".join(artist.get("name", "") for artist in data.get("artists", []))
        self.length: float = data.get("duration_ms", 0)
        self.formatted_length: str = format_track_duration(self.length)
        self.id: str = data.get("id")
        self.album: Optional[str] = None
        self.total_tracks: Optional[int] = 0
        self.year: Optional[int] = data.get("album", {}).get("release_date", "")[:4]
        self.track_index: int = data.get("track_number", 0)
        
        self.isrc: Optional[str] = None
        if data.get("external_ids"):
            self.isrc = data["external_ids"].get("isrc")

        if album:
            self.album = getattr(album, "name", None)
            self.total_tracks = getattr(album, "total_tracks", 0)
            self.image = getattr(album, "image", None)
            self.year = getattr(album, "year", None)
        elif image:
            self.image = image
        else:
            # defensive access into nested album images
            try:
                self.image = data["album"]["images"][0]["url"]
            except Exception:
                self.image = ""
            

        self.uri: Optional[str] = None
        if not data.get("is_local", False):
            ext = data.get("external_urls") or {}
            self.uri = ext.get("spotify")

class Playlist:

    def __init__(self, data: dict, tracks: List[Track]) -> None:
        self.name: str = data.get("name", "")
        self.tracks = tracks
        self.owner: str = (data.get("owner") or {}).get("display_name", "")
        self.total_tracks: int = (data.get("tracks") or {}).get("total", len(self.tracks))
        self.total_duration: str = format_summary_duration(sum(track.length for track in self.tracks))
        if data.get("images") and len(data["images"]):
            self.image = data["images"][0].get("url", "")
        else:
            self.image = getattr(self.tracks[0], "image", "")
        self.uri = (data.get("external_urls") or {}).get("spotify", "")

class Album:
    def __init__(self, data: dict) -> None:
        self.name: str = data.get("name", "")
        self.artists: str = ", ".join(artist.get("name", "") for artist in data.get("artists", []))
        self.image: str = (data.get("images") or [{}])[0].get("url", "")
        self.total_tracks: int = data.get("total_tracks", (data.get("tracks") or {}).get("total", 0))
        self.year: int = int((data.get("release_date", "0")[:4]) or 0)
        items = (data.get("tracks") or {}).get("items", [])
        self.tracks = [Track(track, album=self) for track in items]
        self.total_duration: str = format_summary_duration(sum(track.length for track in self.tracks))
        self.uri: str = (data.get("external_urls") or {}).get("spotify", "")

class Artist:
    def __init__(self, data: dict, tracks: List[dict]) -> None:
        self.name: str = f"Top tracks for {data.get('name', '')}"
        self.image: str = (data.get("images") or [{}])[0].get("url", "")
        # tracks is a list of track dicts from Spotify top-tracks endpoint
        self.tracks = [Track(track, image=self.image) for track in tracks]
        self.total_duration: str = format_summary_duration(sum(track.length for track in self.tracks))
        self.uri: str = (data.get("external_urls") or {}).get("spotify", "")