const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('spotiPod', {
  platform: process.platform,
});
