from src.backend.utils.objects import Album, Artist, Playlist, Track


def _track_payload(name: str, *, is_local: bool = False, with_album: bool = True):
    payload = {
        "name": name,
        "artists": [{"name": "Aphex Twin"}],
        "duration_ms": 177000,
        "id": f"id-{name}",
        "is_local": is_local,
        "external_urls": {"spotify": f"https://open.spotify.com/track/id-{name}"},
        "external_ids": {"isrc": "USABC1234567"},
    }
    if with_album:
        payload["album"] = {"images": [{"url": "https://img/cover.jpg"}]}
    return payload


def test_track_to_dict_contains_expected_fields():
    track = Track(_track_payload("Flim"))
    as_dict = track.to_dict()

    assert as_dict["name"] == "Flim"
    assert as_dict["artists"] == "Aphex Twin"
    assert as_dict["formatted_length"] == "2:57"
    assert as_dict["isrc"] == "USABC1234567"
    assert as_dict["uri"].startswith("https://open.spotify.com/track/")


def test_playlist_to_dict_uses_track_image_fallback_and_tracks():
    track = Track(_track_payload("Flim"))
    playlist_data = {
        "name": "Best of Aphex Twin",
        "owner": {"display_name": "creeperrandom"},
        "tracks": {"total": 1},
        "images": [],
        "external_urls": {"spotify": "https://open.spotify.com/playlist/xyz"},
    }

    playlist = Playlist(playlist_data, [track])
    as_dict = playlist.to_dict()

    assert as_dict["image"] == track.image
    assert as_dict["total_tracks"] == 1
    assert as_dict["tracks"][0]["name"] == "Flim"


def test_album_and_artist_to_dict_have_total_duration_and_tracks():
    album_data = {
        "name": "Come to Daddy",
        "artists": [{"name": "Aphex Twin"}],
        "images": [{"url": "https://img/album.jpg"}],
        "tracks": {"items": [_track_payload("Flim", with_album=False)]},
        "total_tracks": 1,
        "external_urls": {"spotify": "https://open.spotify.com/album/abc"},
        "external_ids": {"upc": "123456789012"},
    }
    album = Album(album_data)

    artist_data = {
        "name": "Aphex Twin",
        "images": [{"url": "https://img/artist.jpg"}],
        "external_urls": {"spotify": "https://open.spotify.com/artist/def"},
    }
    artist = Artist(artist_data, [_track_payload("Flim")])

    album_dict = album.to_dict()
    artist_dict = artist.to_dict()

    assert album_dict["total_duration"].endswith("min")
    assert album_dict["tracks"][0]["formatted_length"] == "2:57"
    assert artist_dict["total_tracks"] == 1
    assert artist_dict["tracks"][0]["name"] == "Flim"
