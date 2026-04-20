const { app, BrowserWindow, shell } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

const isDev = !app.isPackaged;
let backendProcess = null;

function spawnBackendProcess(command, onFailure) {
  const projectRoot = path.resolve(__dirname, '..', '..');
  const child = spawn(command, ['main.py'], {
    cwd: projectRoot,
    shell: false,
    detached: false,
    stdio: 'inherit',
  });

  child.on('error', onFailure);
  return child;
}

function startBackend() {
  if (backendProcess) {
    return;
  }

  const projectRoot = path.resolve(__dirname, '..', '..');
  const venvPython = path.join(projectRoot, '.venv', 'bin', 'python');

  backendProcess = spawnBackendProcess(venvPython, (error) => {
    if (error.code !== 'ENOENT') {
      return;
    }

    backendProcess = spawnBackendProcess('python3', (py3Error) => {
      if (py3Error.code !== 'ENOENT') {
        return;
      }

      backendProcess = spawnBackendProcess('python', () => {
        backendProcess = null;
      });
    });
  });

  backendProcess.on('exit', () => {
    backendProcess = null;
  });
}

function stopBackend() {
  if (!backendProcess) {
    return;
  }

  backendProcess.kill();
  backendProcess = null;
}

function createMainWindow() {
  const mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 960,
    minHeight: 600,
    title: 'SpotiPod',
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http://') || url.startsWith('https://')) {
      void shell.openExternal(url);
      return { action: 'deny' };
    }

    return { action: 'allow' };
  });

  mainWindow.webContents.on('will-navigate', (event, url) => {
    const currentUrl = mainWindow.webContents.getURL();
    if (url === currentUrl) {
      return;
    }

    if (url.startsWith('http://') || url.startsWith('https://')) {
      event.preventDefault();
      void shell.openExternal(url);
    }
  });

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools({ mode: 'detach' });
    return;
  }

  mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
}

app.whenReady().then(() => {
  startBackend();
  createMainWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    stopBackend();
    app.quit();
  }
});

app.on('before-quit', () => {
  stopBackend();
});
