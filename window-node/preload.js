const { contextBridge, ipcRenderer } = require('electron');

// 렌더러에서 안전하게 사용할 수 있는 API를 노출
contextBridge.exposeInMainWorld('electronAPI', {
  // 초기화 이벤트 수신 (사번 전달받기)
  onInit: (callback) => {
    ipcRenderer.on('init', (_event, data) => callback(data));
  },

  // 창 표시
  showWindow: () => ipcRenderer.send('show-window'),

  // 프로그램 종료
  terminate: () => ipcRenderer.send('terminate'),

  // 다이얼로그
  dialogInfo: (title, message) =>
    ipcRenderer.invoke('dialog-info', { title, message }),
  dialogWarning: (title, message) =>
    ipcRenderer.invoke('dialog-warning', { title, message }),
  dialogError: (title, message) =>
    ipcRenderer.invoke('dialog-error', { title, message }),
  dialogYesNo: (title, message) =>
    ipcRenderer.invoke('dialog-yesno', { title, message }),
});
