---
marp: true
size: 16:9

---

## Spotipod

Bridging modern streaming with classic iPod devices

---

## Problem Space

- Legacy devices (iPods) provide a focused listening experience.
- Spotify and modern streaming services don't provide simple offline syncing to these devices.

---

- Download audio (yt-dlp + FFmpeg) into MP3/AAC
- Organize files for Apple Music / iTunes automatic import

---
- Spotify API integration for metadata retrieval
- Metadata application (title, artist, album, year, cover)
- Streamed progress API and robust error handling
- File organization for easy device syncing
## Architecture Overview
- Frontend: Electron + React — user input, progress, settings
- Backend: FastAPI — Spotify queries, download orchestration, tagging
 - Burndown rate for the features = 100%
	 - (2 / 2) × 100%
 - Burndown rate for the requirements = 100%
	 - (7 / 7) × 100%

---

## Core Components (code pointers)

- `src/backend/spotify.py` — URL parsing & Spotify API fetching
- `src/backend/utils/objects.py` — `Track`, `Album`, `Playlist`, `Artist`
- `src/backend/download.py` — yt-dlp wrapper and file discovery
- `src/backend/sync.py` — applies metadata and cover art
- `src/backend/server.py` — FastAPI endpoints for search & download

---

## Sprint 1 — Metrics & Retrospective

- LoC: ~306
- Features planned/completed: 2/2 (100%)
- Requirements completed: 5/5 (100%)

What went well:
- Completed sprint features; flexible tech choices
What went wrong:
- Spotify API changes caused uncertainty; documentation gaps

---

## Weekly Breakdown

- Week 1: Project setup & architecture
- Week 2: Spotify integration
- Week 3: Metadata handling & format detection
- Week 4: Download pipeline & local storage

---

## Sprint 2 Roadmap

- Apple Music / iPod sync automation
- Electron UI polish & packaging
- Expanded testing and CI
- Packaging & distribution (macOS first)

---

## Demo Flow (User Journey)

1. Enter Spotify URL in the app
2. Server fetches metadata and lists tracks
3. User selects tracks and starts download
4. Backend downloads, tags, and moves files to sync folder
5. User syncs device with Apple Music / iTunes

---

## Testing Strategy

- Unit tests: URL parsing, object serialization, format utilities
- Integration tests: end-to-end download + tagging
- Manual tests: verify ID3/MP4 tags and APIC cover frames

---

## Risks & Mitigations

- Spotify API changes: add monitoring and integration tests
- yt-dlp reliability: retries and alternative search heuristics
- Metadata mismatches: log raw metadata for debugging

---

## Next Steps / Ask

- Finish Electron UI and packaging
- Add CI for download + tagging integration tests
- Run real-device sync testing with iPods

---

# Thank you

Questions?

Contact: Project lead (sam)
