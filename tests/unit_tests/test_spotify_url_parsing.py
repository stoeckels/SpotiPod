from src.backend.spotify import parse_spotify_url


def test_parse_spotify_url_valid_playlist():
    parsed = parse_spotify_url("https://open.spotify.com/playlist/4IG2L9hS3YqAIy4peznwSZ")
    assert parsed == {"type": "playlist", "id": "4IG2L9hS3YqAIy4peznwSZ"}


def test_parse_spotify_url_valid_track_with_query_params():
    parsed = parse_spotify_url("https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC?si=abc123")
    assert parsed == {"type": "track", "id": "4uLU6hMCjMI75M1A2tKUQC"}


def test_parse_spotify_url_invalid_returns_none():
    assert parse_spotify_url("https://example.com/not-spotify") is None
    assert parse_spotify_url("open.spotify.com/playlist/4IG2L9hS3YqAIy4peznwSZ") is None
