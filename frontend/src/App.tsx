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
  uri?: string
}

type SearchResult = {
  id: string
  name: string
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
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<SearchResult | null>(null)
  const [settingsLoading, setSettingsLoading] = useState(true)
  const [settingsSaving, setSettingsSaving] = useState(false)
  const [settingsMessage, setSettingsMessage] = useState<string | null>(null)
  const [settingsError, setSettingsError] = useState<string | null>(null)
  const [tokensReady, setTokensReady] = useState(false)
  const [clientId, setClientId] = useState('')
  const [clientSecret, setClientSecret] = useState('')
  const [downloadPath, setDownloadPath] = useState('')

  const tracks = useMemo(() => result?.tracks ?? [], [result])

  const loadSettings = async () => {
    setSettingsLoading(true)
    setSettingsError(null)
    setSettingsMessage(null)

    try {
      const response = await fetch(`${API_BASE_URL}/api/settings`)
      const data: SettingsResponse = await response.json()

      if (!response.ok) {
        setSettingsError('Unable to load settings from backend.')
        return
      }

      setClientId(data.spotify_client_id ?? '')
      setClientSecret(data.spotify_client_secret ?? '')
      setDownloadPath(data.download_path ?? '')
      setTokensReady(data.tokens_populated)

      if (!data.tokens_populated) {
        setActivePage('settings')
      }
    } catch {
      setSettingsError('Backend not reachable. Start python main.py first.')
    } finally {
      setSettingsLoading(false)
    }
  }

  useEffect(() => {
    void loadSettings()
  }, [])

  const formatDuration = (durationMs: number) => {
    const totalSeconds = Math.floor(durationMs / 1000)
    const minutes = Math.floor(totalSeconds / 60)
    const seconds = totalSeconds % 60
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  }

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    setResult(null)

    if (!tokensReady) {
      setError('Open Settings and add Spotify credentials before searching.')
      setActivePage('settings')
      return
    }

    if (!uri.trim()) {
      setError('Paste a Spotify track, playlist, album, or artist URL first.')
      return
    }

    setLoading(true)
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/search?uri=${encodeURIComponent(uri.trim())}`,
      )
      const data = await response.json()

      if (!response.ok) {
        setError(data?.error ?? 'Search failed. Check your backend logs.')
        return
      }

      setResult(data)
    } catch {
      setError('Unable to reach backend. Start the Python API on port 8000.')
    } finally {
      setLoading(false)
    }
  }

  const onSaveSettings = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSettingsSaving(true)
    setSettingsError(null)
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
        setSettingsError(data?.error ?? 'Failed to save settings.')
        return
      }

      setTokensReady(Boolean(data.tokens_populated))
      setSettingsMessage('Settings saved to config.json.')
      if (data.tokens_populated) {
        setActivePage('search')
      }
    } catch {
      setSettingsError('Unable to save settings. Is the backend running?')
    } finally {
      setSettingsSaving(false)
    }
  }

  return (
    <main className="app-shell">
      {activePage === 'search' && (
        <>
          <section className="container">
            <header className="hero">
              <h1>SpotiPod</h1>
              <p className="subhead">
                Enter a Spotify URL to fetch tracks and metadata.
              </p>
            </header>

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
                  className={loading ? 'is-loading' : ''}
                  disabled={loading}
                >
                  <img className="search-icon-img" src={enterIcon} alt="" />
                  <span className="spinner" aria-hidden="true"></span>
                </button>
              </div>
            </form>

            {!tokensReady && (
              <p className="status warn">
                Spotify credentials are missing. Open Settings to update config.json.
              </p>
            )}

            {error && <p className="status error">{error}</p>}

            {result && (
              <section className="result-card">
                <div className="result-header">
                  <h2>{result.name}</h2>
                  {result.uri && (
                    <a href={result.uri} target="_blank" rel="noreferrer">
                      Open in Spotify
                    </a>
                  )}
                </div>

                <div className="meta-grid">
                  <p>
                    <span>ID</span>
                    {result.id}
                  </p>
                  {result.owner && (
                    <p>
                      <span>Owner</span>
                      {result.owner}
                    </p>
                  )}
                  {result.artists && (
                    <p>
                      <span>Artists</span>
                      {result.artists}
                    </p>
                  )}
                  {typeof result.total_tracks === 'number' && (
                    <p>
                      <span>Total Tracks</span>
                      {result.total_tracks}
                    </p>
                  )}
                  <p>
                    <span>Track Results</span>
                    {tracks.length}
                  </p>
                </div>

                {tracks.length > 0 && (
                  <ol className="track-list">
                    {tracks.slice(0, 25).map((track) => (
                      <li key={track.id}>
                        <div>
                          <strong>{track.name}</strong>
                          <p>{track.artists}</p>
                        </div>
                        <span>{formatDuration(track.length)}</span>
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
        <section className="settings-card settings-container">
          <button
            type="button"
            className="settings-button back"
            onClick={() => setActivePage('search')}
            aria-label="Back to search"
          >
            <img className="back-icon-img" src={arrowIcon} alt="" />
          </button>
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

          {settingsError && <p className="status error">{settingsError}</p>}
          {settingsMessage && <p className="status success">{settingsMessage}</p>}
        </section>
      )}
    </main>
  )
}

export default App
