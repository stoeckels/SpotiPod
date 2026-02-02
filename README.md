# SpotiPod

SpotiPod is a lightweight application that bridges modern music streaming with legacy music devices. It allows users to convert Spotify playlist or track links into downloadable audio files that can be synced and played on an iPod or similar offline music players.

---

## Problem Domain and Motivation

Despite being considered obsolete, physical music devices such as iPods still offer a unique listening experience: distraction-free playback, and a tangible connection to music. However, there is currently no simple and accessible way to transfer modern Spotify playlists onto these devices. SpotiPod addresses this gap by enabling users to preserve their curated Spotify playlists and enjoy them on physical hardware, combining modern convenience with nostalgic technology.

---

## Features

- Convert Spotify track or playlist links into playable audio files  
- Support for common audio formats compatible with iPods (e.g., MP3, AAC)  
- Preserve metadata such as song title, artist, album, and album art  
- Organized local file storage by playlist or artist  
- Progress feedback during the conversion process  
- Graceful handling of invalid or private links  

---

## Requirements

### Functional Requirements

- Users can input a Spotify track or playlist URL  
- The system retrieves track metadata using the Spotify API  
- Tracks are converted into playable audio files  
- Converted files are stored locally in an organized directory structure  
- Invalid or unsupported links are handled without crashing the application  

### Non-Functional Requirements

- The application should perform conversions efficiently  
- The user interface should be simple and intuitive  
- Errors should be logged for debugging and testing  

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
- title  
- artist  
- album  
- duration  
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