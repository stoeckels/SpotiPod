import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'
import enterIcon from './assets/enter.svg'
import settingsIcon from './assets/settings.svg'
import arrowIcon from './assets/arrow.svg'

type Track = {
  id: string
  name: string
  artists: string
  length: number
  formatted_length: string
  isrc: string | null
  uri: string | null
  image: string | null
}

type SearchResult = Track | Playlist | Album | Artist

type Playlist = {
  name: string
  owner: string
  image: string | null
  uri: string | null
  tracks: Track[]
  total_tracks: number
  total_duration: string
}

type Album = {
  name: string
  artists: string
  image: string | null
  uri: string | null
  upc: string | null
  tracks: Track[]
  total_tracks: number
  total_duration: string
}

type Artist = {
  name: string
  image: string | null
  uri: string | null
  tracks: Track[]
  total_tracks: number
  total_duration: string
}

type DownloadObjectType = 'track' | 'playlist' | 'album' | 'artist'

type SettingsResponse = {
  spotify_client_id: string
  spotify_client_secret: string
  download_path: string
  metadata: boolean
  auto_sync: boolean
  apple_music_folder_found: boolean
  format: string
  tokens_populated: boolean
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
const SETTINGS_STORAGE_KEY = 'spotipod.settings'

// Type guards
const isTrack = (result: SearchResult): result is Track => !('tracks' in result)
const isPlaylist = (result: SearchResult): result is Playlist => 'owner' in result && 'tracks' in result
const isAlbum = (result: SearchResult): result is Album => 'artists' in result && 'upc' in result && 'tracks' in result
const isArtist = (result: SearchResult): result is Artist => result.name.startsWith('Top tracks for ') && 'tracks' in result && !('owner' in result) && !('artists' in result)

function App() {
  const [activePage, setActivePage] = useState<'search' | 'settings'>('search')
  const [uri, setUri] = useState('')
  const [loading, setLoading] = useState(false)
  const [searchShake, setSearchShake] = useState(false)
  const [result, setResult] = useState<SearchResult | null>(null)
  const [, setError] = useState<string | null>(null)
  const [settingsLoading, setSettingsLoading] = useState(true)
  const [settingsLoaded, setSettingsLoaded] = useState(false)
  const [settingsSaving, setSettingsSaving] = useState(false)
  const [tokensReady, setTokensReady] = useState(false)
  const [clientId, setClientId] = useState('')
  const [clientSecret, setClientSecret] = useState('')
  const [downloadPath, setDownloadPath] = useState('')
  const [metadataProcessing, setMetadataProcessing] = useState(true)
  const [autoSync, setAutoSync] = useState(true)
  const [appleMusicFolderFound, setAppleMusicFolderFound] = useState(false)
  const [formatSelection, setFormatSelection] = useState('aac')
  const [downloadingTrackKeys, setDownloadingTrackKeys] = useState<Set<string>>(new Set())
  const [downloadedTrackKeys, setDownloadedTrackKeys] = useState<Set<string>>(new Set())
  const [resultDownloadLoading, setResultDownloadLoading] = useState(false)
  const [resultDownloadComplete, setResultDownloadComplete] = useState(false)

  const tracks = useMemo(() => {
    if (!result) return []
    return isTrack(result) ? [result] : result.tracks ?? []
  }, [result])
  const isAlbumResult = result ? isAlbum(result) : false
  const hasSearchContent = Boolean(result || (settingsLoaded && !tokensReady))

  const updateTrackDownloadingState = (trackKeys: string[], isDownloading: boolean) => {
    setDownloadingTrackKeys((prev) => {
      const next = new Set(prev)
      trackKeys.forEach((trackKey) => {
        if (isDownloading) {
          next.add(trackKey)
        } else {
          next.delete(trackKey)
        }
      })
      return next
    })
  }

  const updateTrackDownloadedState = (trackKeys: string[]) => {
    setDownloadedTrackKeys((prev) => {
      const next = new Set(prev)
      trackKeys.forEach((trackKey) => next.add(trackKey))
      return next
    })
  }

  const downloadTrack = async (track: Track) => {
    const trackKey = getTrackKey(track)

    updateTrackDownloadingState([trackKey], true)
    try {
      const ok = await requestDownload('track', track)

      if (ok) {
        updateTrackDownloadedState([trackKey])
      }

      return ok
    } finally {
      updateTrackDownloadingState([trackKey], false)
    }
  }

  const requestDownload = async (objectType: DownloadObjectType, objectData: SearchResult) => {
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/api/download`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          object_type: objectType,
          object_data: objectData,
        }),
      })

      const contentType = response.headers.get('content-type') ?? ''

      if (!response.ok || !response.body || !contentType.includes('application/x-ndjson')) {
        const data = await response.json()

        if (!response.ok || !data.ok) {
          setError(data.error ?? 'Download failed.')
          return false
        }

        return true
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let summaryOk = false
      let sawSummary = false

      const processEvent = (rawLine: string) => {
        if (!rawLine) {
          return
        }

        const event = JSON.parse(rawLine) as {
          type?: string
          track_key?: string
          ok?: boolean
        }

        if (event.type === 'track-start' && event.track_key) {
          updateTrackDownloadingState([event.track_key], true)
          return
        }

        if (event.type === 'track-done' && event.track_key) {
          updateTrackDownloadingState([event.track_key], false)

          if (event.ok) {
            updateTrackDownloadedState([event.track_key])
          }

          return
        }

        if (event.type === 'summary') {
          sawSummary = true
          summaryOk = Boolean(event.ok)
        }
      }

      while (true) {
        const { done, value } = await reader.read()
        buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done })

        let newlineIndex = buffer.indexOf('\n')
        while (newlineIndex !== -1) {
          const line = buffer.slice(0, newlineIndex).trim()
          buffer = buffer.slice(newlineIndex + 1)
          processEvent(line)
          newlineIndex = buffer.indexOf('\n')
        }

        if (done) {
          const remaining = buffer.trim()
          if (remaining) {
            processEvent(remaining)
          }
          break
        }
      }

      return sawSummary ? summaryOk : true
    } catch {
      setError('Download failed.')
      return false
    }
  }

  const onDownloadClick = async (objectData: SearchResult) => {
    if (resultDownloadLoading) {
      return
    }

    setResultDownloadLoading(true)
    try {
      if (isTrack(objectData)) {
        await downloadTrack(objectData)
      } else {
        const downloadTargets = (objectData.tracks ?? []).slice(0, 25)
        let allSucceeded = true

        for (const track of downloadTargets) {
          const ok = await downloadTrack(track)
          if (!ok) {
            allSucceeded = false
          }
        }

        if (allSucceeded) {
          setResultDownloadComplete(true)
        }
      }
    } finally {
      setResultDownloadLoading(false)
    }
  }

  const getTrackKey = (track: Track) => track.id || track.uri || `${track.name}:${track.artists}`

  const onTrackDownloadClick = async (track: Track) => {
    const trackKey = getTrackKey(track)
    if (downloadingTrackKeys.has(trackKey) || downloadedTrackKeys.has(trackKey)) {
      return
    }

    await downloadTrack(track)
  }

  const getResultSubtitle = (result: SearchResult): string => {
    if (isTrack(result)) return result.artists

    const parts: string[] = []

    if (isPlaylist(result)) {
      parts.push(result.owner)
    } else if (isAlbum(result)) {
      parts.push(result.artists)
    } else if (isArtist(result)) {
      parts.push('Top tracks')
    }

    if (result.total_tracks > 0) {
      parts.push(`${result.total_tracks} tracks`)
    }

    if (result.total_duration) {
      parts.push(result.total_duration)
    }

    return parts.join(' · ')
  }

  const triggerSearchShake = () => {
    setSearchShake(false)
    requestAnimationFrame(() => {
      setSearchShake(true)
    })
  }

  const loadSettings = async () => {
    setSettingsLoading(true)
    setSettingsLoaded(false)

    const rawCachedSettings = window.localStorage.getItem(SETTINGS_STORAGE_KEY)
    const cachedSettings: Partial<SettingsResponse> | null = rawCachedSettings
      ? JSON.parse(rawCachedSettings)
      : null

    if (cachedSettings) {
      setClientId(cachedSettings.spotify_client_id ?? '')
      setClientSecret(cachedSettings.spotify_client_secret ?? '')
      setDownloadPath(cachedSettings.download_path ?? '')
      setMetadataProcessing(Boolean(cachedSettings.metadata ?? true))
      setAutoSync(Boolean(cachedSettings.auto_sync ?? true))
      setAppleMusicFolderFound(Boolean(cachedSettings.apple_music_folder_found ?? false))
      setFormatSelection(cachedSettings.format ?? 'aac')
    }

    const sleep = (durationMs: number) =>
      new Promise<void>((resolve) => {
        window.setTimeout(resolve, durationMs)
      })

    try {
      for (let attempt = 0; attempt < 12; attempt += 1) {
        try {
          if (cachedSettings) {
            await fetch(`${API_BASE_URL}/api/settings`, {
              method: 'PUT',
              headers: {
                'Content-Type': 'application/json',
              },
                body: JSON.stringify({
                spotify_client_id: cachedSettings.spotify_client_id ?? '',
                spotify_client_secret: cachedSettings.spotify_client_secret ?? '',
                download_path: cachedSettings.download_path ?? '',
                metadata: cachedSettings.metadata ?? true,
                format: cachedSettings.format ?? 'aac',
              }),
            })
          }

          const response = await fetch(`${API_BASE_URL}/api/settings`, {
            cache: 'no-store',
          })

          if (!response.ok) {
            throw new Error('Unable to load settings.')
          }

          const data: SettingsResponse = await response.json()
          setClientId(data.spotify_client_id ?? '')
          setClientSecret(data.spotify_client_secret ?? '')
          setDownloadPath(data.download_path ?? '')
          setMetadataProcessing(Boolean(data.metadata ?? true))
          setAutoSync(Boolean((data as any).auto_sync ?? true))
          setAppleMusicFolderFound(Boolean(data.apple_music_folder_found ?? false))
          setFormatSelection(data.format ?? 'aac')
          setTokensReady(Boolean((data.spotify_client_id ?? '').trim() && (data.spotify_client_secret ?? '').trim()))
          setSettingsLoaded(true)

          if (!data.tokens_populated) {
            setActivePage('settings')
          }

          return
        } catch {
          if (attempt < 11) {
            await sleep(250)
          }
        }
      }
    } finally {
      setSettingsLoading(false)
    }
  }

  useEffect(() => {
    void loadSettings()
  }, [])

  useEffect(() => {
    setDownloadingTrackKeys(new Set())
    setDownloadedTrackKeys(new Set())
    setResultDownloadComplete(false)
  }, [result])

  useEffect(() => {
    if (!searchShake) {
      return
    }

    const timer = window.setTimeout(() => {
      setSearchShake(false)
    }, 300)

    return () => window.clearTimeout(timer)
  }, [searchShake])

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    setResult(null)

    if (!settingsLoaded) {
      return
    }

    if (!tokensReady) {
      setError('Open Settings and add Spotify credentials before searching.')
      setActivePage('settings')
      return
    }

    const trimmedUri = uri.trim()

    if (!trimmedUri) {
      triggerSearchShake()
      return
    }

    setLoading(true)
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/search?uri=${encodeURIComponent(trimmedUri)}`,
      )
      const data = await response.json()

      if (!response.ok) {
        setError('Search failed.')
        return
      }

      if (data === null) {
        triggerSearchShake()
        return
      }

      setResult(data)
    } catch {
      setError(null)
    } finally {
      setLoading(false)
    }
  }

  const onSaveSettings = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSettingsSaving(true)

    try {
      const response = await fetch(`${API_BASE_URL}/api/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          spotify_client_id: clientId,
          spotify_client_secret: clientSecret,
          download_path: downloadPath,
          metadata_processing: metadataProcessing,
          auto_sync: autoSync,
          format_selection: formatSelection,
        }),
      })

      const data = await response.json()
      if (!response.ok || !data.ok) {
        return
      }

      window.localStorage.setItem(
        SETTINGS_STORAGE_KEY,
        JSON.stringify({
          spotify_client_id: clientId,
          spotify_client_secret: clientSecret,
          download_path: downloadPath,
          metadata_processing: metadataProcessing,
          auto_sync: autoSync,
          format_selection: formatSelection,
        }),
      )

      setTokensReady(Boolean(clientId.trim() && clientSecret.trim()))
      if (data.tokens_populated) {
        setActivePage('search')
      }
    } catch {
    } finally {
      setSettingsSaving(false)
    }
  }

  return (
    <main className="app-shell">
      {activePage === 'search' && (
        <>
          <section className={`container ${hasSearchContent ? 'has-content' : 'center-search'}`}>

            <form className="search-form" onSubmit={onSubmit}>
              <div className="input-with-button">
                <input
                  type="url"
                  placeholder="https://open.spotify.com/playlist/..."
                  value={uri}
                  onChange={(event) => setUri(event.target.value)}
                  aria-label="Spotify URL"
                />
                <button
                  type="submit"
                  aria-label="Search"
                  className={[loading ? 'is-loading' : '', searchShake ? 'shake' : '']
                    .filter(Boolean)
                    .join(' ')}
                  disabled={loading}
                >
                  {loading ? (
                    <span className="spinner" aria-hidden="true"></span>
                  ) : (
                    <img className="search-icon-img" src={enterIcon} alt="" />
                  )}
                </button>
              </div>
            </form>

            {settingsLoaded && !tokensReady && (
              <p className="status warn">
                Spotify credentials are missing.
              </p>
            )}

            {/* error state retained internally but text indicators removed */}

            {result && (
              <section className="result-card">
                {!isTrack(result) && (
                  <div className="result-header">
                    {result.image && (
                      <img
                        className="result-cover"
                        src={result.image}
                        alt={`${result.name} cover art`}
                      />
                    )}
                    <div className="result-title-group">
                      <h2>{result.name}</h2>
                      {getResultSubtitle(result) && <p>{getResultSubtitle(result)}</p>}
                    </div>
                    {!resultDownloadLoading && !resultDownloadComplete && (
                      <button
                        type="button"
                        className="object-action-button"
                        aria-label="Download"
                        aria-busy={resultDownloadLoading}
                        disabled={resultDownloadLoading}
                        onClick={() => onDownloadClick(result)}
                      >
                        <img className="download-icon-img" src={arrowIcon} alt="" />
                      </button>
                    )}
                  </div>
                )}

                {tracks.length > 0 && (
                  <ol className="track-list">
                    {tracks.slice(0, 25).map((track: Track, index) => {
                      const trackKey = getTrackKey(track)
                      const isTrackDownloading = downloadingTrackKeys.has(trackKey)
                      const isTrackDownloaded = downloadedTrackKeys.has(trackKey)

                      return (
                        <li
                          key={trackKey}
                          className="track-list-item"
                          style={{ animationDelay: `${index * 45}ms` }}
                        >
                          <span
                            className={[
                              'track-number',
                              isTrackDownloaded ? 'is-downloaded' : '',
                            ]
                              .filter(Boolean)
                              .join(' ')}
                          >
                            {index + 1}
                          </span>
                          {!isAlbumResult && track.image && (
                            <img
                              className="track-cover"
                              src={track.image}
                              alt={`${track.name} album art`}
                            />
                          )}
                          <div className="track-info">
                            <strong>{track.name}</strong>
                            <p>{track.artists}</p>
                          </div>
                          <span className="track-duration">{track.formatted_length}</span>
                          {isTrackDownloading ? (
                            <span className="track-download-spinner" aria-label={`Downloading ${track.name}`}>
                              <span className="spinner track-download-spinner-icon" aria-hidden="true"></span>
                            </span>
                          ) : !isTrackDownloaded ? (
                            <button
                              type="button"
                              className="object-action-button track-download-button"
                              aria-label={`Download ${track.name}`}
                              onClick={() => onTrackDownloadClick(track)}
                            >
                              <img className="download-icon-img" src={arrowIcon} alt="" />
                            </button>
                          ) : null}
                        </li>
                      )
                    })}
                  </ol>
                )}
              </section>
            )}
          </section>

          <button
            className="settings-button"
            type="button"
            onClick={() => setActivePage('settings')}
            aria-label="Open settings"
          >
            <img className="settings-icon-img" src={settingsIcon} alt="" />
          </button>
        </>
      )}

      {activePage === 'settings' && (
        <>
          <section className="settings-card settings-container">
            {settingsLoading ? (
              <p className="status">Loading current settings...</p>
            ) : (
              <form className="settings-form" onSubmit={onSaveSettings}>
                <h2>Spotify API Credentials</h2>
                <p id="instructions">
                  To obtain a Client ID and Secret, please visit the
                  {' '}
                    <a href="https://developer.spotify.com/dashboard/create" target="_blank" rel="noreferrer noopener">
                      Spotify Developer Dashboard
                      <svg fill="#ffffff" width="20px" height="20px" style={{ verticalAlign: 'text-bottom'}}>
                          <path d="M18 7.05a1 1 0 0 0-1-1L9 6a1 1 0 0 0 0 2h5.56l-8.27 8.29a1 1 0 0 0 0 1.42 1 1 0 0 0 1.42 0L16 9.42V15a1 1 0 0 0 1 1 1 1 0 0 0 1-1z"/>
                      </svg>
                  </a>
              </p>
                <input
                  type="text"
                  value={clientId}
                  onChange={(event) => setClientId(event.target.value)}
                  placeholder="Client ID"
                />

                <input
                  type="password"
                  value={clientSecret}
                  onChange={(event) => setClientSecret(event.target.value)}
                  placeholder="Client Secret"
                />

                <h2>Download Settings</h2>
                <label className="toggle-row">
                  Automatic Syncing
                  <input
                    type="checkbox"
                    id="async-download"
                    className="toggle-switch"
                    checked={autoSync}
                    onChange={(e) => setAutoSync(e.target.checked)}
                  />
                </label>
                <p className="setting-hint">
                  {appleMusicFolderFound
                    ? 'Automatically Add to Apple Music folder found.'
                    : 'Automatically Add to Apple Music folder not found.'}
                </p>
                <label className="toggle-row">
                  Apply Metadata
                  <input
                    type="checkbox"
                    id="apply-metadata"
                    className="toggle-switch"
                    checked={metadataProcessing}
                    onChange={(e) => setMetadataProcessing(e.target.checked)}
                  />
                </label>

                <label>
                <h2>Preferred Format</h2>
                  <p id="instructions">Available sources include only lossy audio, AIFF, FLAC, ALAC, WAV are not recommended but provided</p>
                  <select
                    value={formatSelection}
                    onChange={(event) => setFormatSelection(event.target.value)}
                  >
                    <option value="aac">AAC</option>
                    <option value="mp3">MP3</option>
                    <option value="aiff">AIFF</option>
                    <option value="flac">ALAC</option>
                    <option value="flac">FLAC (Rockbox)</option>
                    <option value="wav">WAV</option>
                  </select>
                </label>

                <button type="submit" disabled={settingsSaving}>
                  {settingsSaving ? 'Saving...' : 'Save Settings'}
                </button>
              </form>
            )}
          </section>

          <button
            type="button"
            className="settings-button back"
            onClick={() => setActivePage('search')}
            aria-label="Back to search"
          >
            <img className="back-icon-img" src={arrowIcon} alt="" />
          </button>
        </>
      )}
    </main>
  )
}

export default App
