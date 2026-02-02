# SpotiPod

SpotiPod is a lightweight application that bridges modern music streaming with legacy music devices. It allows users to convert Spotify playlist or track links into downloadable audio files that can be synced and played on an iPod or similar offline music players.

---

## Problem Domain and Motivation

Despite being considered obsolete, physical music devices such as iPods still offer a unique listening experience: distraction-free playback, and a tangible connection to music. However, there is currently no simple and accessible way to transfer modern Spotify playlists onto these devices. SpotiPod addresses this gap by enabling users to preserve their curated Spotify playlists and enjoy them on physical hardware, combining modern convenience with nostalgic technology.

---

## Features and Requirements

Sprint 1 (Required Features):
1. Fetch track metadata from Spotify for formatting locally
- R.1 Integration with Spotify API for song, album, artist, playlist endpoints
- R.2 Format that metadata into usable objects for local 

2. Find available music formats based off of track metadata. 
- R.1 yt-dlp must be able to download formats based on ISRC metadata
- R.2 Apply the metadata from Spotify to the local music file
- R.3 Formats must be able to be stored locally in an efficient matter

Sprint 2 (More non-trivial features):
3. Automatic integration with Apple Music syncing to iPod
- R.1 User must have Apple Music or iTunes installed in order to interface with iPod
- R.2 Files must be able to be moved to specific directories for syncing.

4. A clean UI/UX experience through a deployed App 
- R.1 App must be easy to navigate and have good modularity.
- R.2 Efficient error handing for user error or app error.
- R.3 Settings must be readily available to the user for format or general app controls.
- R.4 App must be packaged via Electron, or a similar technology.

---

## Architecture and Data Model

### High-Level Architecture

- Frontend  
  - Simple UI for link input and conversion progress display  

- Backend  
  - Spotify API integration for metadata retrieval  
  - Audio conversion service  
  - File management and organization module  

The application follows a modular design to allow independent development and testing of each component.

### Data Model

#### Track

- track_id  
- track metadata
- file_path  

#### Playlist

- playlist_id  
- name
- list of tracks  

---

## Testing




- Unit Tests  
  - Spotify API response handling  
  - URL validation  
  - Metadata tagging and file naming  

- Integration Tests  
  - End-to-end playlist conversion  
  - File output verification  

- Edge Case Testing  
  - Empty playlists  
  - Invalid or unsupported links  
  - Network or API failures  

- Manual Testing  
  - UI usability testing  
  - Syncing converted files to an iPod or emulator  

---

## Team Members and Roles

For an individual project, all roles are handled by a single developer.

---

## Project Links

- Documentation: TBD  
- Presentation: https://github.com/stoeckels/SpotiPod/docs/presentation/ppp.md

---