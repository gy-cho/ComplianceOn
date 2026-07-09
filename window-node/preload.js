const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  onInit:     (cb) => ipcRenderer.on('init', (_e, data) => cb(data)),
  showWindow: ()   => ipcRenderer.send('show-window'),
  terminate:  ()   => ipcRenderer.send('terminate'),

  // ★ 디버그 로그: renderer → main으로 로그 전달
  log: (msg)       => ipcRenderer.send('log', msg),

  dialogInfo:    (title, message) => ipcRenderer.invoke('dialog-info',    { title, message }),
  dialogWarning: (title, message) => ipcRenderer.invoke('dialog-warning', { title, message }),
  dialogError:   (title, message) => ipcRenderer.invoke('dialog-error',   { title, message }),
  dialogYesNo:   (title, message) => ipcRenderer.invoke('dialog-yesno',   { title, message }),
});
