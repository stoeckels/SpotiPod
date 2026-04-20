from fastapi.testclient import TestClient

from src.server import Client


def test_search_requires_credentials():
    client = Client()
    http = TestClient(client.app)

    response = http.get(
        "/api/search",
        params={"uri": "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC"},
    )

    assert response.status_code == 400
    assert "credentials" in response.json()["error"].lower()


def test_settings_round_trip_updates_backend_state():
    client = Client()
    http = TestClient(client.app)

    update = {
        "spotify_client_id": "client-id",
        "spotify_client_secret": "client-secret",
        "download_path": "/tmp/spotipod",
        "metadata_processing": "standard",
        "format_selection": "mp3",
    }

    put_response = http.put("/api/settings", json=update)
    assert put_response.status_code == 200
    assert put_response.json()["ok"] is True
    assert put_response.json()["tokens_populated"] is True

    get_response = http.get("/api/settings")
    assert get_response.status_code == 200

    settings = get_response.json()
    assert settings["spotify_client_id"] == "client-id"
    assert settings["spotify_client_secret"] == "client-secret"
    assert settings["download_path"] == "/tmp/spotipod"
    assert settings["metadata_processing"] == "standard"
    assert settings["format_selection"] == "mp3"
    assert settings["tokens_populated"] is True
