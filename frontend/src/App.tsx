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
  isrc: string
  uri?: string
  image: string
}

type SearchResult = {
  id: string
  name: string
  image?: string
  uri?: string
  tracks?: Track[]
  total_tracks?: number
  owner?: string
  artists?: string
}

type SettingsResponse = {
  spotify_client_id: string
  spotify_client_secret: string
  download_path: string
  tokens_populated: boolean
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

function App() {
  const [activePage, setActivePage] = useState<'search' | 'settings'>('search')
  const [uri, setUri] = useState('')
  const [loading, setLoading] = useState(false)
  const [searchShake, setSearchShake] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<SearchResult | null>(null)
  const [settingsLoading, setSettingsLoading] = useState(true)
  const [settingsLoaded, setSettingsLoaded] = useState(false)
  const [settingsSaving, setSettingsSaving] = useState(false)
  const [settingsMessage, setSettingsMessage] = useState<string | null>(null)
  const [tokensReady, setTokensReady] = useState(false)
  const [clientId, setClientId] = useState('')
  const [clientSecret, setClientSecret] = useState('')
  const [downloadPath, setDownloadPath] = useState('')

  const tracks = useMemo(() => result?.tracks ?? [], [result])
  const isAlbumResult = Boolean(
    result?.artists &&
      result?.total_tracks !== undefined &&
      result?.tracks &&
      !result.name.startsWith('Top tracks for '),
  )
  const totalDurationMs = useMemo(
    () => tracks.reduce((sum, track) => sum + track.length, 0),
    [tracks],
  )
  const hasSearchContent = Boolean(result || error || (settingsLoaded && !tokensReady))

  const formatDuration = (durationMs: number) => {
    const totalSeconds = Math.floor(durationMs / 1000)
    const minutes = Math.floor(totalSeconds / 60)
    const seconds = totalSeconds % 60
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  }

  const onDownloadClick = () => {
  }

  const loadSettings = async () => {
    setSettingsLoading(true)
    setSettingsLoaded(false)
    setSettingsMessage(null)

    const sleep = (durationMs: number) =>
      new Promise<void>((resolve) => {
        window.setTimeout(resolve, durationMs)
      })

    try {
      for (let attempt = 0; attempt < 12; attempt += 1) {
        try {
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
          setTokensReady(data.tokens_populated)
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

    if (!uri.trim()) {
      setSearchShake(false)
      requestAnimationFrame(() => {
        setSearchShake(true)
      })
      return
    }

    setLoading(true)
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/search?uri=${encodeURIComponent(uri.trim())}`,
      )
      const data = await response.json()

      if (!response.ok) {
        setError('Search failed.')
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
    setSettingsMessage(null)

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
        }),
      })

      const data = await response.json()
      if (!response.ok || !data.ok) {
        return
      }

      setTokensReady(Boolean(data.tokens_populated))
      setSettingsMessage('Settings saved to config.json.')
      if (data.tokens_populated) {
        setActivePage('search')
      }
    } catch {
      setSettingsMessage(null)
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
                Spotify credentials are missing. Open Settings to update config.json.
              </p>
            )}

            {error && <p className="status error">{error}</p>}

            {result && (
              <section className="result-card">
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
                    {(result.owner || result.artists) && <p>{result.owner ?? result.artists}</p>}
                  </div>
                  <button
                    type="button"
                    className="object-action-button"
                    aria-label="Download object"
                    onClick={onDownloadClick}
                  >
                    <img className="download-icon-img" src={arrowIcon} alt="" />
                  </button>
                </div>

                <div className="meta-grid">
                  {typeof result.total_tracks === 'number' && (
                    <p>
                      <span>Total Tracks</span>
                      {result.total_tracks}
                    </p>
                  )}
                  {typeof result.total_tracks === 'number' && tracks.length > 0 && (
                    <p>
                      <span>Total Duration</span>
                      {formatDuration(totalDurationMs)}
                    </p>
                  )}
                </div>

                {tracks.length > 0 && (
                  <ol className="track-list">
                    {tracks.slice(0, 25).map((track) => (
                      <li key={track.id}>
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
                        <span className="track-duration">{formatDuration(track.length)}</span>
                        <button
                          type="button"
                          className="object-action-button track-download-button"
                          aria-label={`Download ${track.name}`}
                          onClick={onDownloadClick}
                        >
                          <img className="download-icon-img" src={arrowIcon} alt="" />
                        </button>
                      </li>
                    ))}
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
            <h2>Settings</h2>
            {settingsLoading ? (
              <p className="status">Loading current settings...</p>
            ) : (
              <form className="settings-form" onSubmit={onSaveSettings}>
                <label>
                  Spotify Client ID
                  <input
                    type="text"
                    value={clientId}
                    onChange={(event) => setClientId(event.target.value)}
                    placeholder="Paste Spotify client ID"
                  />
                </label>

                <label>
                  Spotify Client Secret
                  <input
                    type="password"
                    value={clientSecret}
                    onChange={(event) => setClientSecret(event.target.value)}
                    placeholder="Paste Spotify client secret"
                  />
                </label>

                <label>
                  Download Path (optional)
                  <input
                    type="text"
                    value={downloadPath}
                    onChange={(event) => setDownloadPath(event.target.value)}
                    placeholder="/Users/you/Music/SpotiPod"
                  />
                </label>

                <button type="submit" disabled={settingsSaving}>
                  {settingsSaving ? 'Saving...' : 'Save Settings'}
                </button>
              </form>
            )}
            {settingsMessage && <p className="status success">{settingsMessage}</p>}
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
