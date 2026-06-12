// =========================================================================
// [폰트 설정]
// ★ 폰트 파일을 바꾸려면 아래 두 곳을 수정하세요:
//   1. FONT_FILE  : 실제 폰트 파일명 (예: 'NotoSansKR.woff', 'Pretendard.woff2')
//   2. FONT_FORMAT: 파일 형식에 맞게 변경 ('woff' 또는 'woff2')
//   폰트 파일은 renderer.js 와 같은 폴더에 위치해야 합니다.
// =========================================================================
(function injectFont() {
  const FONT_FILE   = 'OpenSans400.woff';  // ★ 폰트 파일명을 여기서 변경하세요
  const FONT_FORMAT = 'woff';              // ★ 폰트 형식을 여기서 변경하세요 (woff / woff2)
  const FONT_FAMILY = 'AppFont';

  const style = document.createElement('style');
  style.textContent = `
    @font-face {
      font-family: '${FONT_FAMILY}';
      src: url('${FONT_FILE}') format('${FONT_FORMAT}');
      font-weight: normal;
      font-style: normal;
    }
    body, button, input, label, div, span {
      font-family: '${FONT_FAMILY}', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
    }

    /* ★ 커스텀 라디오 버튼
       - 기본 테두리 굵기: 1.5px → 얇게/두껍게 하려면 이 값을 바꾸세요
       - 선택 시 내부 흰 테두리: border: 3px solid #ffffff
       - 선택 시 채움/외곽선 색: #FFBC00 */
    .custom-radio {
      appearance: none;
      -webkit-appearance: none;
      border-radius: 50%;
      border: 1.5px solid #aaaaaa;
      background: #ffffff;
      cursor: pointer;
      flex-shrink: 0;
    }
    .custom-radio:checked {
      background: #FFBC00;
      border: 3px solid #ffffff;
      outline: 2px solid #FFBC00;
    }

    /* ★ 라디오 동그라미↔텍스트 간격: gap 값을 바꾸세요 */
    .radio-label {
      gap: 8px;
      color: #1a1a1a;
    }

    /* =========================================================
       인앱 커스텀 모달 (네이티브 다이얼로그 대체)
       작업표시줄 노출 현상 완전 방지
       ========================================================= */
    #inapp-modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.45);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 99999;
    }
    #inapp-modal-box {
      background: #ffffff;
      border-radius: 10px;
      padding: 32px 36px 24px;
      min-width: 360px;
      max-width: 480px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.28);
      display: flex;
      flex-direction: column;
      gap: 18px;
    }
    #inapp-modal-title {
      font-size: 16px;
      font-weight: 700;
      color: #1a1a1a;
      margin: 0;
    }
    #inapp-modal-message {
      font-size: 14px;
      color: #333333;
      line-height: 1.6;
      white-space: pre-line;
      margin: 0;
    }
    #inapp-modal-buttons {
      display: flex;
      justify-content: flex-end;
      gap: 10px;
      margin-top: 4px;
    }
    .inapp-modal-btn {
      padding: 9px 28px;
      border-radius: 6px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      border: none;
      transition: opacity 0.15s;
    }
    .inapp-modal-btn:hover { opacity: 0.85; }
    .inapp-modal-btn-primary {
      background: #FFBC00;
      color: #1a1a1a;
    }
    .inapp-modal-btn-secondary {
      background: #e8e8e8;
      color: #444444;
    }
  `;
  document.head.appendChild(style);
})();

// =========================================================================
// [서버 및 환경 설정]
// =========================================================================
// const BASE_URL = 'http://10.201.2.93:8080';
const BASE_URL = 'http://192.168.62.94:8080';
// const BASE_URL = 'http://127.0.0.1:8080';

// =========================================================================
// 전역 상태
// =========================================================================
let empNoStr    = '';
let taskIdStr   = '';
let appSeqStr   = '';
let empNameStr  = '홍길동';
let dateStr     = '2026년 6월';
let taskTypeStr = '';

let userAnswers    = {};
let standardAnswers = {};
let currentTaskData = null;
let _dialogOpen    = false;  // 다이얼로그 열린 동안 resize 재렌더 차단

// =========================================================================
// 유틸리티
// =========================================================================
function terminateProgram() { window.electronAPI.terminate(); }
function showLoading(v)     { document.getElementById('loading-overlay').style.display = v ? 'flex' : 'none'; }
function showApp(v)         { document.getElementById('app-container').style.display   = v ? 'flex' : 'none'; }

// =========================================================================
// 인앱 커스텀 모달 — 네이티브 dialog 대체
// 윈도우 포커스를 전혀 변경하지 않아 작업표시줄 노출 현상이 없습니다.
// =========================================================================

/**
 * 모달을 표시하고 사용자 응답을 Promise로 반환합니다.
 * @param {string} title   - 제목
 * @param {string} message - 본문 (개행 \n 지원)
 * @param {'ok'|'yesno'} type - 버튼 종류
 * @returns {Promise<boolean>} ok/예 → true, 아니오 → false
 */
function showInappModal(title, message, type = 'ok') {
  return new Promise(resolve => {
    // 기존 모달 제거
    const old = document.getElementById('inapp-modal-backdrop');
    if (old) old.remove();

    const backdrop = document.createElement('div');
    backdrop.id = 'inapp-modal-backdrop';

    const box = document.createElement('div');
    box.id = 'inapp-modal-box';

    const titleEl = document.createElement('p');
    titleEl.id = 'inapp-modal-title';
    titleEl.textContent = title;

    const msgEl = document.createElement('p');
    msgEl.id = 'inapp-modal-message';
    msgEl.textContent = message;

    const btnRow = document.createElement('div');
    btnRow.id = 'inapp-modal-buttons';

    const close = (result) => {
      backdrop.remove();
      resolve(result);
    };

    if (type === 'yesno') {
      const noBtn = document.createElement('button');
      noBtn.className = 'inapp-modal-btn inapp-modal-btn-secondary';
      noBtn.textContent = '아니오';
      noBtn.addEventListener('click', () => close(false));

      const yesBtn = document.createElement('button');
      yesBtn.className = 'inapp-modal-btn inapp-modal-btn-primary';
      yesBtn.textContent = '예';
      yesBtn.addEventListener('click', () => close(true));

      btnRow.appendChild(noBtn);
      btnRow.appendChild(yesBtn);
    } else {
      const okBtn = document.createElement('button');
      okBtn.className = 'inapp-modal-btn inapp-modal-btn-primary';
      okBtn.textContent = '확인';
      okBtn.addEventListener('click', () => close(true));
      btnRow.appendChild(okBtn);
    }

    box.appendChild(titleEl);
    box.appendChild(msgEl);
    box.appendChild(btnRow);
    backdrop.appendChild(box);
    document.body.appendChild(backdrop);

    // 첫 번째 버튼에 포커스 (키보드 Enter 지원)
    btnRow.querySelector('button')?.focus();
  });
}

// =========================================================================
// 공통: contain 방식 이미지 피팅 계산
//  - 이미지 비율 유지, 한 축이 윈도우에 꽉 참, 상하 또는 좌우 여백 없음
// =========================================================================
function calcImageFit(naturalW, naturalH) {
  const winW  = window.innerWidth;
  const winH  = window.innerHeight;
  const scale = Math.min(winW / naturalW, winH / naturalH);
  const renderW = Math.round(naturalW * scale);
  const renderH = Math.round(naturalH * scale);
  const offsetX = Math.round((winW  - renderW) / 2);
  const offsetY = Math.round((winH  - renderH) / 2);
  return { scale, renderW, renderH, offsetX, offsetY };
}

// =========================================================================
// [타입 A] 윤리강령 서약서 화면
// =========================================================================
async function drawEthicsUI(taskData) {
  const container = document.getElementById('app-container');
  container.innerHTML = '';
  container.style.background = '#000000';

  const imgFilename = taskData.img_flnm || 'TEST_1.png';
  const imageUrl    = `${BASE_URL}/images/${imgFilename}`;

  const wrapper = document.createElement('div');
  wrapper.id = 'ethics-wrapper';
  wrapper.style.cssText = 'position:relative;width:100vw;height:100vh;overflow:hidden;';

  const bgImg = document.createElement('img');
  bgImg.id  = 'ethics-bg-img';
  bgImg.alt = '윤리강령';
  bgImg.style.cssText = `
    position:absolute; top:50%; left:50%;
    transform:translate(-50%,-50%);
    max-width:100%; max-height:100%;
    width:auto; height:auto; display:block;
  `;

  bgImg.onload  = () => setupEthicsElements(wrapper, bgImg);
  bgImg.onerror = () => {
    bgImg.src     = 'TEST_1.png';
    bgImg.onerror = () => terminateProgram();
  };
  bgImg.src = imageUrl;

  wrapper.appendChild(bgImg);
  container.appendChild(wrapper);
}

function setupEthicsElements(wrapper, bgImg) {
  const ex = wrapper.querySelector('#ethics-overlay');
  if (ex) ex.remove();

  const { scale, renderW, renderH, offsetX, offsetY } = calcImageFit(bgImg.naturalWidth, bgImg.naturalHeight);

  // 오버레이: 이미지 실제 렌더 영역에 정확히 겹침
  const overlay = document.createElement('div');
  overlay.id = 'ethics-overlay';
  overlay.style.cssText = `
    position:absolute;
    top:${offsetY}px; left:${offsetX}px;
    width:${renderW}px; height:${renderH}px;
    pointer-events:none;
  `;

  // 버튼 좌표: 자가점검과 동일한 방식 (bgImg 실제 원본 크기 기준)
  const natW = bgImg.naturalWidth  || 3508;
  const natH = bgImg.naturalHeight || 2480;
  // 흰색 카드 비율 (자가점검 배경과 동일 레이아웃 가정: right=96.5%, bottom=96.5%, w=93%, h=70%)
  const E_CARD_RIGHT_R  = 0.965;
  const E_CARD_BOTTOM_R = 0.965;
  const E_CARD_W_R      = 0.930;
  const E_CARD_H_R      = 0.700;
  const eBtnCenterX_orig = natW * E_CARD_RIGHT_R  - natW * E_CARD_W_R  * 0.060;
  const eBtnCenterY_orig = natH * E_CARD_BOTTOM_R - natH * E_CARD_H_R  * 0.060;
  const eBtnW_orig       = natW * E_CARD_W_R * 0.090;
  const eBtnH_orig       = natH * E_CARD_H_R * 0.055;

  const eBtnCenterX = Math.round(eBtnCenterX_orig * scale);
  const eBtnCenterY = Math.round(eBtnCenterY_orig * scale);
  const eBtnW       = Math.round(eBtnW_orig       * scale);
  const eBtnH       = Math.round(eBtnH_orig       * scale);
  const fs          = Math.max(12, Math.round(32 * scale));

  const submitBtn = document.createElement('button');
  submitBtn.className   = 'submit-btn ethics-submit-btn active';
  submitBtn.textContent = '확인';
  submitBtn.style.cssText = `
    position:absolute;
    left:${eBtnCenterX - Math.round(eBtnW/2)}px;
    top:${eBtnCenterY  - Math.round(eBtnH/2)}px;
    width:${eBtnW}px; height:${eBtnH}px;
    font-size:${fs}px;
    border-radius:${Math.round(8*scale)}px;
    pointer-events:all;
  `;

  submitBtn.addEventListener('click', () => {
    if (submitBtn.classList.contains('active')) onAgree();
  });

  overlay.appendChild(submitBtn);
  wrapper.appendChild(overlay);
}

// =========================================================================
// [타입 B] 자가점검 설문지 화면
// =========================================================================
function drawSelfCheckUI(taskData) {
  const container = document.getElementById('app-container');
  container.innerHTML = '';
  container.style.background = '#000000';

  const qstnList = (taskData.qstn_list || []).slice(0, 3);

  const wrapper = document.createElement('div');
  wrapper.id = 'selfcheck-wrapper';
  wrapper.style.cssText = 'position:relative;width:100vw;height:100vh;overflow:hidden;';

  const bgImg = document.createElement('img');
  bgImg.id  = 'selfcheck-bg-img';
  bgImg.alt = '자가점검';
  bgImg.style.cssText = `
    position:absolute; top:50%; left:50%;
    transform:translate(-50%,-50%);
    max-width:100%; max-height:100%;
    width:auto; height:auto; display:block;
  `;
  bgImg.src = 'img_self_check_bg.png';

  bgImg.onerror = async () => {
    await showInappModal('오류', '자가점검 배경 이미지(img_self_check_bg.png)를 찾을 수 없습니다.');
    terminateProgram();
  };
  bgImg.onload = () => buildSelfCheckOverlay(wrapper, bgImg, qstnList);

  wrapper.appendChild(bgImg);
  container.appendChild(wrapper);
}

function buildSelfCheckOverlay(wrapper, bgImg, qstnList) {
  const ex = wrapper.querySelector('#selfcheck-overlay');
  if (ex) ex.remove();

  const naturalW = bgImg.naturalWidth;   // 3508
  const naturalH = bgImg.naturalHeight;  // 2480

  const { scale, renderW, renderH, offsetX, offsetY } = calcImageFit(naturalW, naturalH);

  // -----------------------------------------------------------------------
  // 원본 이미지(3508×2480) 기준 좌표값
  // (측정값: 흰색 카드 top=658, bottom=2394, left=125, right=3384)
  // -----------------------------------------------------------------------
  const CARD_TOP    = 658;
  const CARD_BOTTOM = 2394;
  const CARD_LEFT   = 125;
  const CARD_RIGHT  = 3384;
  const CARD_W      = CARD_RIGHT - CARD_LEFT;   // 3259
  const CARD_H      = CARD_BOTTOM - CARD_TOP;   // 1736

  // 질문 영역: 카드 내 22%~85% 구간에 3개 질문 배치
  // ★ 항목 위치 조정: CARD_H * 0.22 의 숫자를 바꾸면 항목 전체가 위아래로 이동합니다.
  //   (작게 → 위로, 크게 → 아래로)
  const startY_orig       = CARD_TOP  + CARD_H * 0.22;  // ≈1039
  const yGap_orig         = CARD_H    * 0.183;           // ≈318  (질문 간 간격)
  const textLeftX_orig    = CARD_LEFT + CARD_W * 0.030;  // ≈223  (텍스트 좌측 여백)
  // ★ 예/아니오 오른쪽 여백: 0.095 → 값을 크게 하면 왼쪽으로 이동(여백 증가)
  const radioYesX_orig    = CARD_RIGHT - CARD_W * 0.130; // 오른쪽 여백 확대
  // ★ 구분선 좌우 여백: 0.08 → 값을 크게 하면 여백 증가
  const linePadding_orig  = CARD_W    * 0.07;            // 구분선 좌우 여백 확대
  const dividerOffset_orig = yGap_orig * 0.80;           // ≈254  (구분선 Y 오프셋)

  // 제출 버튼: 카드 우측 하단
  const btnCenterX_orig = CARD_RIGHT - CARD_W * 0.060;  // ≈3188
  const btnCenterY_orig = CARD_BOTTOM - CARD_H * 0.060; // ≈2325
  const btnW_orig       = CARD_W * 0.090;               // ≈293
  const btnH_orig       = CARD_H * 0.055;               // ≈95

  // 렌더 좌표로 변환
  const startY         = Math.round(startY_orig        * scale);
  const yGap           = Math.round(yGap_orig          * scale);
  const textLeftX      = Math.round(textLeftX_orig     * scale);
  const radioYesX      = Math.round(radioYesX_orig     * scale);
  const linePadding    = Math.round(linePadding_orig   * scale);
  const dividerOffset  = Math.round(dividerOffset_orig * scale);
  const btnCenterX     = Math.round(btnCenterX_orig    * scale);
  const btnCenterY     = Math.round(btnCenterY_orig    * scale);
  const btnW           = Math.round(btnW_orig          * scale);
  const btnH           = Math.round(btnH_orig          * scale);

  // 폰트 크기: 전반적으로 키움 (기존 대비 약 30% 증가)
  const titleFontSize   = Math.max(14, Math.round(42 * scale));   // 37 → 48
  const contentFontSize = Math.max(14, Math.round(42 * scale));   // 32 → 42
  const radioFontSize   = Math.max(14, Math.round(38 * scale));   // 30 → 38
  const btnFontSize     = Math.max(14, Math.round(38 * scale));   // 32 → 38

  // 카드 상단 타이틀 (이미지의 "고객에 대한 윤리" 위치: 카드 top~30% 구간 중앙)
  const cardTitleFontSize = Math.max(18, Math.round(60 * scale));
  const cardTitleX = Math.round((CARD_LEFT + CARD_W * 0.5) * scale);
  const cardTitleY = Math.round((CARD_TOP  + CARD_H * 0.07) * scale);

  // 오버레이: 이미지 실제 렌더 영역에 정확히 겹침
  const overlay = document.createElement('div');
  overlay.id = 'selfcheck-overlay';
  overlay.style.cssText = `
    position:absolute;
    top:${offsetY}px; left:${offsetX}px;
    width:${renderW}px; height:${renderH}px;
    pointer-events:none;
  `;

  // -----------------------------------------------------------------------
  // 카드 상단 타이틀 (이미지의 "고객에 대한 윤리" 위치/디자인과 동일)
  // -----------------------------------------------------------------------
  const cardTitleEl = document.createElement('div');
  cardTitleEl.className = 'selfcheck-card-title';
  cardTitleEl.textContent = qstnList[0]?.qstn_nm || '자가점검';
  cardTitleEl.style.cssText = `
    position:absolute;
    top:${cardTitleY}px;
    left:${cardTitleX}px;
    transform:translateX(-50%);
    font-size:${cardTitleFontSize}px;
    font-weight:700;
    color:#967446;
    letter-spacing:0.05em;
    pointer-events:none;
    white-space:nowrap;
  `;
  overlay.appendChild(cardTitleEl);

  // userAnswers 초기화
  userAnswers = {};
  qstnList.forEach(q => { userAnswers[q.qstn_cd] = ''; });

  // -----------------------------------------------------------------------
  // 자가점검 확인 버튼
  // -----------------------------------------------------------------------
  const submitBtn = document.createElement('button');
  submitBtn.className   = 'submit-btn disabled';
  submitBtn.id          = 'selfcheck-submit-btn';
  submitBtn.textContent = '확인';
  submitBtn.style.cssText = `
    position:absolute;
    left:${btnCenterX - Math.round(btnW/2)}px;
    top:${btnCenterY  - Math.round(btnH/2)}px;
    width:${btnW}px; height:${btnH}px;
    font-size:${btnFontSize}px;
    border-radius:${Math.round(8*scale)}px;
    pointer-events:all;
  `;
  submitBtn.addEventListener('click', () => {
    if (submitBtn.classList.contains('active')) onAgree();
  });

  // -----------------------------------------------------------------------
  // 각 질문 렌더링
  // -----------------------------------------------------------------------
  qstnList.forEach((qstn, idx) => {
    const qCd      = qstn.qstn_cd;
    const qTitle   = qstn.qstn_nm || '';
    const qContent = qstn.qstn_cn || '';
    const currentY = startY + idx * yGap;

    const displayTitle = `${String(idx+1).padStart(2,'0')}.`;

    // 제목 (번호만)
    const titleEl = document.createElement('div');
    titleEl.className = 'question-title';
    titleEl.dataset.qcd = qCd;
    titleEl.textContent = displayTitle;
    titleEl.style.cssText = `
      position:absolute;
      top:${currentY}px; left:${textLeftX}px;
      font-size:${titleFontSize}px;
      font-weight:700;
      color:#1a1a1a;
      pointer-events:none;
    `;

    // 내용 (qstn_cn) — 번호와 동일한 폰트 크기·굵기·색상
    const contentEl = document.createElement('div');
    contentEl.className = 'question-content';
    contentEl.dataset.qcd = qCd;
    contentEl.textContent = qContent;
    contentEl.style.cssText = `
      position:absolute;
      top:${currentY}px;
      left:${textLeftX + Math.round(titleFontSize * 2.2)}px;
      max-width:${Math.round(renderW * 0.60)}px;
      font-size:${titleFontSize}px;
      font-weight:700;
      color:#1a1a1a;
      pointer-events:none;
    `;

    // 라디오 그룹
    const radioGroup = document.createElement('div');
    radioGroup.className = 'radio-group';
    radioGroup.dataset.qcd = qCd;
    radioGroup.style.cssText = `
      position:absolute;
      top:${currentY}px;
      left:${radioYesX}px;
      display:flex;
      gap:${Math.round(20*scale)}px;
      align-items:center;
      pointer-events:all;
    `;

    // 예 라디오
    const yesLabel = document.createElement('label');
    yesLabel.className   = 'radio-label yes-label';
    yesLabel.style.cssText = `
      font-size:${radioFontSize}px;
      display:inline-flex; align-items:center;
      width:${Math.round(160*scale)}px;
      white-space:nowrap;
    `;
    const yesRadio = document.createElement('input');
    yesRadio.type      = 'radio';
    yesRadio.name      = `question_${qCd}`;
    yesRadio.value     = 'Y';
    yesRadio.className = 'custom-radio';
    yesRadio.style.cssText = `
      width:${Math.round(32*scale)}px; height:${Math.round(32*scale)}px;
    `;
    yesRadio.addEventListener('change', () => {
      if (yesRadio.checked) { userAnswers[qCd] = 'Y'; checkSelfCheckComplete(submitBtn); }
    });
    const yesText = document.createElement('span');
    yesText.textContent = '예';
    yesLabel.appendChild(yesRadio);
    yesLabel.appendChild(yesText);

    // 아니오 라디오
    const noLabel = document.createElement('label');
    noLabel.className   = 'radio-label no-label';
    noLabel.style.cssText = `
      font-size:${radioFontSize}px;
      display:inline-flex; align-items:center;
      width:${Math.round(160*scale)}px;
      white-space:nowrap;
    `;
    const noRadio = document.createElement('input');
    noRadio.type      = 'radio';
    noRadio.name      = `question_${qCd}`;
    noRadio.value     = 'N';
    noRadio.className = 'custom-radio';
    noRadio.style.cssText = `
      width:${Math.round(32*scale)}px; height:${Math.round(32*scale)}px;
    `;
    noRadio.addEventListener('change', () => {
      if (noRadio.checked) { userAnswers[qCd] = 'N'; checkSelfCheckComplete(submitBtn); }
    });
    const noText = document.createElement('span');
    noText.textContent = '아니오';
    noLabel.appendChild(noRadio);
    noLabel.appendChild(noText);

    radioGroup.appendChild(yesLabel);
    radioGroup.appendChild(noLabel);

    // 구분선
    const divider = document.createElement('div');
    divider.className = 'question-divider';
    divider.dataset.qcd = qCd;
    divider.style.cssText = `
      position:absolute;
      top:${currentY + dividerOffset}px;
      left:${linePadding}px;
      width:${renderW - linePadding*2}px;
      pointer-events:none;
    `;

    overlay.appendChild(titleEl);
    overlay.appendChild(contentEl);
    overlay.appendChild(radioGroup);
    overlay.appendChild(divider);
  });

  overlay.appendChild(submitBtn);
  wrapper.appendChild(overlay);
}

// =========================================================================
// checkSelfCheckComplete
// =========================================================================
function checkSelfCheckComplete(submitBtn) {
  const allAnswered = Object.values(userAnswers).every(v => v !== '');
  submitBtn.classList.toggle('active',   allAnswered);
  submitBtn.classList.toggle('disabled', !allAnswered);
}

// =========================================================================
// 윈도우 리사이즈 시 오버레이 재계산 (디바운스 100ms)
// =========================================================================
let _resizeTimer = null;
window.addEventListener('resize', () => {
  if (_dialogOpen) return;  // 다이얼로그 열린 동안은 재렌더 완전 차단
  clearTimeout(_resizeTimer);
  _resizeTimer = setTimeout(() => {
    if (!currentTaskData) return;
    if (taskTypeStr === 'ETHICS') {
      const wrapper = document.getElementById('ethics-wrapper');
      const bgImg   = document.getElementById('ethics-bg-img');
      if (wrapper && bgImg && bgImg.complete) setupEthicsElements(wrapper, bgImg);
    } else if (taskTypeStr === 'SELF_CHECK') {
      const wrapper  = document.getElementById('selfcheck-wrapper');
      const bgImg    = document.getElementById('selfcheck-bg-img');
      // 체크 상태 유지: DOM을 새로 그리지 않고 좌표만 재계산
      if (wrapper && bgImg && bgImg.complete) repositionSelfCheckOverlay(bgImg);
    }
  }, 100);
});

// =========================================================================
// 자가점검 오버레이 재배치 (resize 전용 — DOM 유지, 좌표만 업데이트)
// 체크박스 DOM을 건드리지 않으므로 선택 상태가 그대로 유지됩니다.
// =========================================================================
function repositionSelfCheckOverlay(bgImg) {
  const overlay = document.getElementById('selfcheck-overlay');
  if (!overlay || !currentTaskData) return;

  const naturalW = bgImg.naturalWidth;
  const naturalH = bgImg.naturalHeight;
  const { scale, renderW, renderH, offsetX, offsetY } = calcImageFit(naturalW, naturalH);

  const CARD_TOP    = 658;
  const CARD_BOTTOM = 2394;
  const CARD_LEFT   = 125;
  const CARD_RIGHT  = 3384;
  const CARD_W      = CARD_RIGHT - CARD_LEFT;
  const CARD_H      = CARD_BOTTOM - CARD_TOP;

  const startY_orig        = CARD_TOP  + CARD_H * 0.22;
  const yGap_orig          = CARD_H    * 0.183;
  const textLeftX_orig     = CARD_LEFT + CARD_W * 0.030;
  const radioYesX_orig     = CARD_RIGHT - CARD_W * 0.130;
  const linePadding_orig   = CARD_W    * 0.07;
  const dividerOffset_orig = yGap_orig * 0.80;
  const btnCenterX_orig    = CARD_RIGHT - CARD_W * 0.060;
  const btnCenterY_orig    = CARD_BOTTOM - CARD_H * 0.060;
  const btnW_orig          = CARD_W * 0.090;
  const btnH_orig          = CARD_H * 0.055;
  const cardTitleX_orig    = CARD_LEFT + CARD_W * 0.5;
  const cardTitleY_orig    = CARD_TOP  + CARD_H * 0.07;

  const startY        = Math.round(startY_orig        * scale);
  const yGap          = Math.round(yGap_orig          * scale);
  const textLeftX     = Math.round(textLeftX_orig     * scale);
  const radioYesX     = Math.round(radioYesX_orig     * scale);
  const linePadding   = Math.round(linePadding_orig   * scale);
  const dividerOffset = Math.round(dividerOffset_orig * scale);
  const btnCenterX    = Math.round(btnCenterX_orig    * scale);
  const btnCenterY    = Math.round(btnCenterY_orig    * scale);
  const btnW          = Math.round(btnW_orig          * scale);
  const btnH          = Math.round(btnH_orig          * scale);
  const cardTitleX    = Math.round(cardTitleX_orig    * scale);
  const cardTitleY    = Math.round(cardTitleY_orig    * scale);

  const titleFontSize     = Math.max(14, Math.round(42 * scale));
  const radioFontSize     = Math.max(14, Math.round(38 * scale));
  const btnFontSize       = Math.max(14, Math.round(38 * scale));
  const cardTitleFontSize = Math.max(18, Math.round(60 * scale));

  // 오버레이 컨테이너 위치/크기
  overlay.style.cssText = `
    position:absolute;
    top:${offsetY}px; left:${offsetX}px;
    width:${renderW}px; height:${renderH}px;
    pointer-events:none;
  `;

  // 카드 타이틀
  const titleEl = overlay.querySelector('.selfcheck-card-title');
  if (titleEl) {
    titleEl.style.top       = `${cardTitleY}px`;
    titleEl.style.left      = `${cardTitleX}px`;
    titleEl.style.fontSize  = `${cardTitleFontSize}px`;
  }

  // 확인 버튼
  const submitBtn = overlay.querySelector('#selfcheck-submit-btn');
  if (submitBtn) {
    submitBtn.style.left      = `${btnCenterX - Math.round(btnW/2)}px`;
    submitBtn.style.top       = `${btnCenterY  - Math.round(btnH/2)}px`;
    submitBtn.style.width     = `${btnW}px`;
    submitBtn.style.height    = `${btnH}px`;
    submitBtn.style.fontSize  = `${btnFontSize}px`;
    submitBtn.style.borderRadius = `${Math.round(8*scale)}px`;
  }

  // 각 질문 요소 (번호·내용·라디오그룹·구분선)
  const qstnList = (currentTaskData.qstn_list || []).slice(0, 3);
  qstnList.forEach((qstn, idx) => {
    const currentY = startY + idx * yGap;
    const qCd = qstn.qstn_cd;

    const qTitleEl = overlay.querySelector(`.question-title[data-qcd="${qCd}"]`);
    if (qTitleEl) {
      qTitleEl.style.top      = `${currentY}px`;
      qTitleEl.style.left     = `${textLeftX}px`;
      qTitleEl.style.fontSize = `${titleFontSize}px`;
    }

    const qContentEl = overlay.querySelector(`.question-content[data-qcd="${qCd}"]`);
    if (qContentEl) {
      qContentEl.style.top      = `${currentY}px`;
      qContentEl.style.left     = `${textLeftX + Math.round(titleFontSize * 2.2)}px`;
      qContentEl.style.fontSize = `${titleFontSize}px`;
    }

    const radioGroup = overlay.querySelector(`.radio-group[data-qcd="${qCd}"]`);
    if (radioGroup) {
      radioGroup.style.top  = `${currentY}px`;
      radioGroup.style.left = `${radioYesX}px`;
      radioGroup.style.gap  = `${Math.round(20*scale)}px`;
      // 라디오 크기
      radioGroup.querySelectorAll('.custom-radio').forEach(r => {
        r.style.width  = `${Math.round(32*scale)}px`;
        r.style.height = `${Math.round(32*scale)}px`;
      });
      // 라벨 너비
      radioGroup.querySelectorAll('.radio-label').forEach(l => {
        l.style.width     = `${Math.round(160*scale)}px`;
        l.style.fontSize  = `${radioFontSize}px`;
      });
    }

    const dividerEl = overlay.querySelector(`.question-divider[data-qcd="${qCd}"]`);
    if (dividerEl) {
      dividerEl.style.top   = `${currentY + dividerOffset}px`;
      dividerEl.style.left  = `${linePadding}px`;
      dividerEl.style.width = `${renderW - linePadding*2}px`;
    }
  });
}

// =========================================================================
// 제출 처리
// =========================================================================
async function onAgree() {
  const submitUrl = `${BASE_URL}/submit-compliance`;
  let isAllCorrect = true;

  if (taskTypeStr === 'SELF_CHECK') {
    for (const [qCd, userAns] of Object.entries(userAnswers)) {
      if (userAns !== (standardAnswers[qCd] || 'Y')) { isAllCorrect = false; break; }
    }
    if (!isAllCorrect) {
      const confirmed = await showInappModal(
        '자가점검 재확인',
        '보안 지침에 위배되는 답변 항목이 존재합니다.\n이대로 점검 결과를 제출하시겠습니까?',
        'yesno'
      );
      if (!confirmed) return;
    }
  }

  const payload = {
    task_id: /^\d+$/.test(taskIdStr) ? parseInt(taskIdStr, 10) : null,
    app_seq: /^\d+$/.test(appSeqStr) ? parseInt(appSeqStr, 10) : null,
    emp_no: empNoStr,
    emp_main_ans_yn: 'Y',
    emp_ans_agr_yn:  isAllCorrect ? 'Y' : 'N',
    answers: [],
  };

  if (taskTypeStr === 'SELF_CHECK') {
    payload.answers = Object.entries(userAnswers).map(([qCd, ans]) => ({
      qstn_cd: qCd, emp_ans_yn: ans,
    }));
  }

  try {
    const response = await fetch(submitUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(3000),
    });
    const resData = await response.json().catch(() => ({}));

    if (response.status === 200) {
      await showInappModal('알림', resData.message || '준법 프로그램 수행 기록이 정상적으로 저장되었습니다.');
      terminateProgram();
    } else if ([400, 404, 500].includes(response.status)) {
      await showInappModal('제출 실패', resData.message || '알 수 없는 오류');
      terminateProgram();
    } else {
      await showInappModal('오류', `정의되지 않은 서버 응답 에러가 발생했습니다.\nStatus Code: ${response.status}`);
      terminateProgram();
    }
  } catch (e) {
    await showInappModal('네트워크 오류', `서버에 서약 데이터를 전송하지 못했습니다.\n\n에러: ${e.message}`);
    terminateProgram();
  }
}

// =========================================================================
// 진입점
// =========================================================================
window.electronAPI.onInit(async ({ empNo }) => {
  empNoStr = empNo;

  const taskData = await fetchTaskAndInit();
  if (!taskData) { terminateProgram(); return; }

  currentTaskData = taskData;
  showLoading(false);
  showApp(true);
  window.electronAPI.showWindow();

  if (taskTypeStr === 'ETHICS') {
    await drawEthicsUI(taskData);
  } else if (taskTypeStr === 'SELF_CHECK') {
    drawSelfCheckUI(taskData);
  }
});

// =========================================================================
// 서버 통신: 태스크 조회
// =========================================================================
async function fetchTaskAndInit() {
  const url = `${BASE_URL}/get-task-qstn?emp_no=${empNoStr}`;
  try {
    const response = await fetch(url, { signal: AbortSignal.timeout(3000) });
    if (!response.ok) return null;
    const results = await response.json();
    if (!results || results.length === 0) return null;

    const taskData = results[0];
    taskIdStr   = String(taskData.task_id  ?? '');
    appSeqStr   = String(taskData.app_seq  ?? '');
    taskTypeStr = taskData.task_type || 'ETHICS';

    if (taskTypeStr === 'SELF_CHECK' && Array.isArray(taskData.qstn_list)) {
      for (const qstn of taskData.qstn_list) {
        standardAnswers[qstn.qstn_cd] = qstn.qstn_std_ans_yn || 'Y';
      }
    }
    return taskData;
  } catch (e) {
    console.error('태스크 조회 실패:', e);
    return null;
  }
}