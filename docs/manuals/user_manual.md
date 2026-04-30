---
marp: true
theme: default
---

# SpotiPod User Manual

Desktop music downloading for iPods and other older media devices.

---

## What SpotiPod Does

SpotiPod helps you move modern Spotify music onto iPods and other old media devices that still thrive on offline audio libraries. It lets you search Spotify links, inspect tracks, and download audio files for offline use.

It is designed around two workflows:

1. Search for a Spotify track, album, playlist, or artist page.
2. Download the selected music as audio files, optionally applying metadata and syncing to the Apple Music "Automatically Add" folder.

---

## Before You Start

You need:

- A Spotify Client ID and Client Secret from the Spotify Developer Dashboard.
- The app running locally.
- Optionally, Apple Music or iTunes installed if you want automatic sync support for syncing to an iPod or similar legacy player.

The app now uses AAC as the default format.

---

## Running the App

From the repository root, start the app with:

```bash
npm run frontend:dev
```

That command starts the frontend and the Electron desktop shell together.

---

## Searching for Music

1. Open the app.
2. Paste a Spotify URL into the search field.
3. Press the search button.

You can search for:

- A single track
- An album
- A playlist
- An artist page that exposes top tracks

If Spotify credentials are missing, the app sends you to the Settings page.

---

## Downloading Music

### Download a Single Track

1. Search for a track.
2. Click the download button for that track.

The track row shows a spinner while it is being downloaded. When it finishes, the track number turns green.

### Download an Album, Playlist, or Artist Result

1. Search for the collection.
2. Click the main download button on the result card.

The app downloads tracks one at a time. The album-level button is hidden while the collection is downloading.

This workflow is intended for building libraries you can later sync onto an iPod, iPhone-era music library, or another older portable media device.

---

## Settings

Open Settings from the gear button in the lower-right corner of the search screen.

### Spotify API Credentials

Enter your Client ID and Client Secret here. SpotiPod checks whether both fields are filled in before allowing searches.

### Download Settings

- Automatic Syncing: Enables sync behavior for the Apple Music "Automatically Add" folder.
- Apply Metadata: Adds track metadata to the downloaded files.
- Preferred Format: Chooses the output format.

Available formats include:

- AAC
- MP3
- AIFF
- FLAC
- WAV

---

### Apple Music Folder Detection

The Settings page shows whether SpotiPod can find the "Automatically Add to Music" folder on your system. If it is detected, the app can use it for sync-related behavior and prepare music for an iPod or other legacy device library.

---

## What Happens During Download

When you download a track, SpotiPod:

1. Downloads the audio into a temporary folder.
2. Applies metadata if enabled.
3. Moves the finished file into the configured sync location.

This keeps partial downloads out of your final music library.

---

## Troubleshooting

### Search does not work

- Make sure your Spotify Client ID and Secret are saved in Settings.
- Confirm the URL you pasted is a valid Spotify link.

### Download fails

- Make sure the selected source has a downloadable audio result.
- Try another format if the current one is not available for that item.

### Apple Music folder is not found

- Install Apple Music or iTunes if needed.
- Confirm the "Automatically Add" folder exists on your system.
- Restart the app after changing your local music setup.
