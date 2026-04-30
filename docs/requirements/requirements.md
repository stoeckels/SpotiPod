---
marp: true
---

## SpotiPod Requirements

1. The app shall accept Spotify track, album, playlist, and artist URLs.
2. The app shall retrieve Spotify metadata and show results in the UI.
3. The app shall download selected tracks in the chosen output format.
4. The app shall apply metadata tags when the setting is enabled.
5. The app shall support optional automatic sync to Apple Music/iTunes "Automatically Add" folders when found.
6. The app shall provide per-track download status (in progress and complete).
7. The app shall provide a Settings page for Spotify credentials and download preferences.
8. The app shall persist settings across app restarts.
9. The app shall handle invalid links and failed downloads without crashing.

---

## Acceptance Criteria (Measurable)

- Given a valid Spotify URL, when the user searches, then the app returns and displays matching result data.
- Given credentials are configured, when the user downloads, then at least one output audio file is created in the target flow.
- Given metadata is enabled, when a track download completes, then title and artist metadata fields are present on the file.
- Given automatic sync is enabled and folder exists, when download completes, then the file is moved to the sync destination.
- Given invalid input or source failure, when a download is attempted, then the app responds with an error state and keeps running.
- Given saved settings, when the app is restarted, then previous settings values are restored.

