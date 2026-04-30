---
marp: true
theme: default
paginate: true
---

# SpotiPod — Design & Architecture

High-level architecture and data flow for the frontend and backend.

---

## System Diagram

```
┌─────────────────────────────────────────────────┐     NDJSON     ┌─────────────────────────────────────────────────┐
│                                                 │◀──────────────▶│                                                 │
│               Electron Shell / React UI         │                │                    FastAPI                      │
│           (Search, Results, Settings UI)        │◀──────────────▶│               (API / Orchestrator / Router)     │
│                                                 │     HTTP/WS    │                 (download, metadata)            │
└─────────────────────────────────────────────────┘                └─────────────────────────────────────────────────┘
                      │                                                   │
                      │ localStorage                                      │
                      ▼                                                   ▼
        ┌──────────────────────────────┐                       ┌──────────────────────────────────┐
        │        localStorage (UI)     │                       │         Download Engine          │
        │         (settings/session)   │                       │            (yt-dlp)              │
        └──────────────────────────────┘                       └──────────────────────────────────┘
                                                                   │
                                                                   ▼
                                                         ┌──────────────────────────────────┐
                                                         │        Metadata (mutagen)        │
                                                         └──────────────────────────────────┘
                                                                   │
                                                                   ▼
                                                         ┌──────────────────────────────────┐
                                                         │  Temp Dir → Move to Apple Music  │
                                                         │      "Automatically Add" folder  │
                                                         └──────────────────────────────────┘

                             ┌──────────────────────────────────────────────┐
                             │           Logs / Tests / Monitoring          │
                             └──────────────────────────────────────────────┘
```

---

## Components (short)

- Frontend: `Electron` · `React` — screens: Search, Results, Settings; widgets for track rows and spinners; `localStorage` for settings and session persistence.
- API: `FastAPI` — search, streaming download endpoint (NDJSON), settings endpoints.
- Download Orchestrator: coordinates `yt-dlp`, FFmpeg postprocessing, `tempfile` isolation, then `mutagen`/MP4 tagging.
- Sync: Moves completed files into discovered Apple Music/iTunes "Automatically Add" folders for legacy device syncing.
- Observability & Tests: structured logs and layered tests ensure acceptance and regression coverage.

---

## Data Flows

- User pastes Spotify URL → Frontend calls `/api/search` → Backend queries Spotify and returns structured object.
- User triggers download → Frontend POST `/api/download` → Backend streams NDJSON events (track-start, track-done, summary) → Frontend updates per-track UI state.
- Backend downloads into a temporary directory, applies metadata, then moves file to `sync_dir` when configured.

---

## Deployment & Runtime Notes

- Dev: `npm run frontend:dev` runs Vite + Electron; backend launched by Electron uses repo `.venv`.
- Packaging: Build frontend, bundle Electron assets, include Python runtime or instruct user to install `.venv` dependencies.
- Cross-platform: Path detection for Apple Music/iTunes differs by OS; detection happens at runtime in `sync.detect_apple_music_dir()`.

---

## Design Rationale (brief)

- Stream NDJSON for fine-grained UI feedback during long-running downloads.
- Use temporary directories to avoid polluting sync targets with partial downloads.
- Keep settings in `localStorage` so values persist across renderer reloads and Electron restarts.
