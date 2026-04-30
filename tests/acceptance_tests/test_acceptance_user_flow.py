from fastapi.testclient import TestClient

from src.server import Client
from src.utils.objects import Track


class FakeSpotify:
    async def search(self, uri: str):
        assert "open.spotify.com/track/" in uri
        return Track(
            {
                "name": "Flim",
                "artists": [{"name": "Aphex Twin"}],
                "duration_ms": 177000,
                "id": "4uLU6hMCjMI75M1A2tKUQC",
                "is_local": False,
                "external_urls": {
                    "spotify": "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC"
                },
                "external_ids": {"isrc": "USABC1234567"},
                "album": {"images": [{"url": "https://img/cover.jpg"}]},
            }
        )


def test_acceptance_search_then_download_track(monkeypatch, tmp_path):
    client = Client()
    client.spotify = FakeSpotify()
    http = TestClient(client.app)

    def fake_fetch(track, *, output_dir=None, audio_format="mp3"):
        assert track.name == "Flim"
        assert output_dir != str(tmp_path)
        return {"title": "Flim (YouTube)"}

    monkeypatch.setattr("src.server.fetch", fake_fetch)

    http.put(
        "/api/settings",
        json={
            "spotify_client_id": "client-id",
            "spotify_client_secret": "client-secret",
            "download_path": str(tmp_path),
            "metadata_processing": True,
            "format_selection": "aac",
        },
    )

    client.spotify = FakeSpotify()

    search_response = http.get(
        "/api/search",
        params={"uri": "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC"},
    )
    assert search_response.status_code == 200

    track = search_response.json()
    assert track["name"] == "Flim"
    assert track["formatted_length"] == "2:57"

    download_response = http.post(
        "/api/download",
        json={"object_type": "track", "object_data": track},
    )
    assert download_response.status_code == 200

    body = download_response.json()
    assert body["ok"] is True
    assert body["downloaded_count"] == 1
    assert body["failed_count"] == 0
