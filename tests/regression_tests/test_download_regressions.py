from fastapi.testclient import TestClient

from src.server import Client


def test_download_track_allows_null_id_regression(monkeypatch, tmp_path):
    client = Client()
    http = TestClient(client.app)

    def fake_fetch(track, *, output_dir=None, audio_format="mp3"):
        assert track.name == "Flim"
        assert audio_format == "mp3"
        assert output_dir == str(tmp_path)
        return {"title": "Flim (YouTube)"}

    monkeypatch.setattr("src.server.fetch", fake_fetch)

    payload = {
        "object_type": "track",
        "object_data": {
            "id": None,
            "name": "Flim",
            "artists": "Aphex Twin",
            "length": 177000,
            "formatted_length": "2:57",
            "isrc": None,
            "uri": None,
            "image": None,
        },
    }

    http.put(
        "/api/settings",
        json={
            "spotify_client_id": "",
            "spotify_client_secret": "",
            "download_path": str(tmp_path),
            "metadata_processing": "standard",
            "format_selection": "mp3",
        },
    )

    response = http.post("/api/download", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert body["ok"] is True
    assert body["downloaded_count"] == 1
    assert body["failed_count"] == 0
    assert body["results"][0]["source_title"] == "Flim (YouTube)"


def test_download_non_track_requires_tracks_list_regression():
    client = Client()
    http = TestClient(client.app)

    payload = {
        "object_type": "playlist",
        "object_data": {
            "id": None,
            "name": "Empty Playlist",
            "owner": "tester",
            "image": None,
            "uri": None,
            "tracks": [],
            "total_tracks": 0,
            "total_duration": "0 min",
        },
    }

    response = http.post("/api/download", json=payload)
    assert response.status_code == 400
    assert "No tracks found" in response.json()["error"]
