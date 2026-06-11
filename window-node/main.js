const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');

// Windows 레지스트리에서 AuthID 읽기
function getAuthIdFromRegistry() {
  // Windows 전용: regedit 방식으로 레지스트리 읽기
  // winreg 패키지 없이 child_process로 처리
  const { execSync } = require('child_process');
  const keyPath = 'HKLM\\SOFTWARE\\Geni\\Genian';

  try {
    // 64비트 뷰로 레지스트리 쿼리
    const result = execSync(
      `reg query "${keyPath}" /v AuthID /reg:64`,
      { encoding: 'utf8', timeout: 3000 }
    );
    // 결과 파싱: "    AuthID    REG_SZ    값"
    const match = result.match(/AuthID\s+REG_SZ\s+(.+)/);
    if (match) {
      return match[1].trim();
    }
    return null;
  } catch (e) {
    console.error('레지스트리 읽기 실패:', e.message);
    return null;
  }
}

let mainWindow = null;

async function createWindow(empNo) {
  mainWindow = new BrowserWindow({
    // 처음엔 숨겨두고 데이터 로드 후 표시 (Python의 root.withdraw()와 동일)
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

  // 다이얼로그 표시 시 fullscreen 해제 및 하단 바 노출 방지
  mainWindow.setAlwaysOnTop(true, 'screen-saver');
  mainWindow.setFullScreenable(false);

  await mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));

  // 렌더러에 사번 전달 후 데이터 조회 지시
  mainWindow.webContents.send('init', { empNo });
}

app.whenReady().then(async () => {
  // 1. 사번 가져오기
  const authId = getAuthIdFromRegistry();
  if (!authId) {
    console.error('사번 가져오기 실패! 프로그램을 종료합니다.');
    app.exit(0);
    return;
  }

  // 2. 창 생성 (숨김 상태)
  await createWindow(authId);
});

// =========================================================================
// IPC 핸들러 - 렌더러 프로세스와 통신
// =========================================================================

// 창 표시 (데이터 조회 성공 후 렌더러가 요청)
ipcMain.on('show-window', () => {
  if (mainWindow) {
    mainWindow.show();
    mainWindow.focus();
  }
});

// 프로그램 강제 종료
ipcMain.on('terminate', () => {
  app.exit(0);
});

app.on('window-all-closed', () => {
  app.exit(0);
});