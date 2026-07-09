const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs   = require('fs');

// =========================================================================
// 디버그 로그 (문제 발생 시 원인 파악용)
// 로그 파일 위치: C:\Users\사용자명\AppData\Roaming\kb-compliance-app\debug.log
// =========================================================================
const logFile = path.join(app.getPath('userData'), 'debug.log');
function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  try { fs.appendFileSync(logFile, line); } catch(e) {}
  console.log(msg);
}

// Windows 레지스트리에서 AuthID 읽기
function getAuthIdFromRegistry() {
  const { execSync } = require('child_process');
  const keyPath = 'HKLM\\SOFTWARE\\Geni\\Genian';

  // 64비트 먼저 시도, 실패 시 32비트 시도
  for (const reg of ['/reg:64', '/reg:32']) {
    try {
      const result = execSync(
        `reg query "${keyPath}" /v AuthID ${reg}`,
        { encoding: 'utf8', timeout: 3000 }
      );
      const match = result.match(/AuthID\s+REG_SZ\s+(.+)/);
      if (match) {
        log(`레지스트리 읽기 성공 (${reg}): ${match[1].trim()}`);
        return match[1].trim();
      }
    } catch (e) {
      log(`레지스트리 읽기 실패 (${reg}): ${e.message}`);
    }
  }
  return null;
}

let mainWindow = null;

async function createWindow(empNo) {
  log('createWindow 시작');
  mainWindow = new BrowserWindow({
    show: false,
    fullscreen: true,
    alwaysOnTop: true,
    frame: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.setAlwaysOnTop(true, 'screen-saver');
  mainWindow.setFullScreenable(false);

  await mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));
  log('index.html 로드 완료');

  // renderer 프로세스 오류 감지
  mainWindow.webContents.on('did-fail-load', (e, code, desc) => {
    log(`[main] did-fail-load: ${code} ${desc}`);
  });
  mainWindow.webContents.on('render-process-gone', (e, details) => {
    log(`[main] render-process-gone: ${JSON.stringify(details)}`);
  });
  mainWindow.webContents.on('preload-error', (e, preloadPath, error) => {
    log(`[main] preload-error: ${preloadPath} - ${error}`);
  });
  mainWindow.webContents.on('console-message', (e, level, message) => {
    log(`[renderer console] ${message}`);
  });

  mainWindow.webContents.send('init', { empNo });
  log(`init 전송 완료 (empNo: ${empNo})`);
}

app.whenReady().then(async () => {
  log('=== 앱 시작 ===');
  log(`userData 경로: ${app.getPath('userData')}`);

  const authId = getAuthIdFromRegistry();
  if (!authId) {
    log('사번 가져오기 실패 → 앱 종료');
    app.exit(0);
    return;
  }

  log(`사번 확인 완료: ${authId}`);
  await createWindow(authId);
});

// =========================================================================
// IPC 핸들러
// =========================================================================
ipcMain.on('show-window', () => {
  log('show-window 수신');
  if (mainWindow) {
    mainWindow.show();
    mainWindow.focus();
  }
});

// renderer에서 보내는 로그를 파일에 기록
ipcMain.on('log', (_e, msg) => {
  log(msg);
});

ipcMain.on('terminate', () => {
  log('terminate 수신 → 앱 종료');
  app.exit(0);
});

app.on('window-all-closed', () => {
  app.exit(0);
});
