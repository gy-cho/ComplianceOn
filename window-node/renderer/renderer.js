// =========================================================================
// [서버 및 환경 설정]
// =========================================================================
const BASE_URL = 'http://10.201.2.93:8080';
// const BASE_URL = 'http://192.168.62.94:8080';
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

// =========================================================================
// 유틸리티
// =========================================================================
function terminateProgram() { window.electronAPI.terminate(); }
function showLoading(v)     { document.getElementById('loading-overlay').style.display = v ? 'flex' : 'none'; }
function showApp(v)         { document.getElementById('app-container').style.display   = v ? 'flex' : 'none'; }

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
  container.style.background = '#ffffff';

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

  // 요소 묶음: 이미지 하단 83% 지점
  const elemDiv = document.createElement('div');
  elemDiv.style.cssText = `
    position:absolute;
    left:50%; top:${Math.round(renderH * 0.83)}px;
    transform:translateX(-50%);
    display:flex; flex-direction:column; align-items:center;
    gap:${Math.round(6 * scale)}px;
    pointer-events:all;
  `;

  const fs     = Math.max(11, Math.round(13 * scale));
  const btnW   = Math.round(240 * scale);
  const btnH   = Math.round(40  * scale);

  // 체크박스 행
  const checkRow = document.createElement('label');
  checkRow.className = 'ethics-checkbox-row';
  checkRow.style.gap = `${Math.round(8 * scale)}px`;

  const checkbox = document.createElement('input');
  checkbox.type  = 'checkbox';
  checkbox.id    = 'ethics-agree-checkbox';
  checkbox.style.cssText = `
    width:${Math.round(18*scale)}px; height:${Math.round(18*scale)}px;
    cursor:pointer; accent-color:#FFBC00;
  `;

  const checkLabel = document.createElement('span');
  checkLabel.className   = 'ethics-checkbox-label';
  checkLabel.style.fontSize = `${fs}px`;
  checkLabel.textContent = "본인은 상기의 '윤리강령' 내용을 확인하였으며, 이를 준수할 것을 다짐합니다.";

  checkRow.appendChild(checkbox);
  checkRow.appendChild(checkLabel);

  const dateEl = document.createElement('p');
  dateEl.className   = 'ethics-date-text';
  dateEl.style.fontSize = `${fs}px`;
  dateEl.textContent = dateStr;

  const empEl = document.createElement('p');
  empEl.className   = 'ethics-emp-text';
  empEl.style.fontSize = `${fs}px`;
  empEl.textContent = `직원번호 : ${empNoStr}       서명 : ${empNameStr}`;

  const submitBtn = document.createElement('button');
  submitBtn.className   = 'submit-btn ethics-submit-btn disabled';
  submitBtn.textContent = '확인 및 업무 시작';
  submitBtn.style.cssText = `
    width:${btnW}px; height:${btnH}px;
    font-size:${fs}px;
    margin-top:${Math.round(4*scale)}px;
    pointer-events:all;
  `;

  checkbox.addEventListener('change', () => {
    submitBtn.classList.toggle('disabled', !checkbox.checked);
    submitBtn.classList.toggle('active',    checkbox.checked);
  });
  submitBtn.addEventListener('click', () => {
    if (submitBtn.classList.contains('active')) onAgree();
  });

  elemDiv.appendChild(checkRow);
  elemDiv.appendChild(dateEl);
  elemDiv.appendChild(empEl);
  elemDiv.appendChild(submitBtn);
  overlay.appendChild(elemDiv);
  wrapper.appendChild(overlay);
}

// =========================================================================
// [타입 B] 자가점검 설문지 화면
// =========================================================================
function drawSelfCheckUI(taskData) {
  const container = document.getElementById('app-container');
  container.innerHTML = '';
  container.style.background = '#F4F4F4';

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
    await window.electronAPI.dialogError('오류', '자가점검 배경 이미지(img_self_check_bg.png)를 찾을 수 없습니다.');
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

  // 질문 영역: 카드 내 30%~85% 구간에 3개 질문 배치
  const startY_orig       = CARD_TOP  + CARD_H * 0.30;  // ≈1179
  const yGap_orig         = CARD_H    * 0.183;           // ≈318  (질문 간 간격)
  const textLeftX_orig    = CARD_LEFT + CARD_W * 0.030;  // ≈223  (텍스트 좌측 여백)
  const radioYesX_orig    = CARD_RIGHT - CARD_W * 0.095; // ≈3049 ("예" 라디오 X)
  const linePadding_orig  = CARD_W    * 0.02;            // ≈65   (구분선 좌우 여백)
  const dividerOffset_orig = yGap_orig * 0.80;           // ≈254  (구분선 Y 오프셋)

  // 제출 버튼: 카드 우측 하단
  const btnCenterX_orig = CARD_RIGHT - CARD_W * 0.060;  // ≈3188
  const btnCenterY_orig = CARD_BOTTOM - CARD_H * 0.040; // ≈2325
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

  // 폰트 크기: 윈도우 기준 목표 크기를 scale로 역산
  // 목표: 질문 제목 16px, 질문 내용 14px, 라디오 13px (1920×1080 기준)
  const titleFontSize   = Math.max(12, Math.round(37 * scale));   // 원본 37px → 렌더 16px@1920
  const contentFontSize = Math.max(11, Math.round(32 * scale));
  const radioFontSize   = Math.max(11, Math.round(30 * scale));
  const btnFontSize     = Math.max(12, Math.round(32 * scale));

  // 오버레이: 이미지 실제 렌더 영역에 정확히 겹침
  const overlay = document.createElement('div');
  overlay.id = 'selfcheck-overlay';
  overlay.style.cssText = `
    position:absolute;
    top:${offsetY}px; left:${offsetX}px;
    width:${renderW}px; height:${renderH}px;
    pointer-events:none;
  `;

  // userAnswers 초기화
  userAnswers = {};
  qstnList.forEach(q => { userAnswers[q.qstn_cd] = ''; });

  // -----------------------------------------------------------------------
  // 제출 버튼
  // -----------------------------------------------------------------------
  const submitBtn = document.createElement('button');
  submitBtn.className   = 'submit-btn disabled';
  submitBtn.id          = 'selfcheck-submit-btn';
  submitBtn.textContent = '제출(확인)';
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

    const displayTitle = qTitle
      ? `${String(idx+1).padStart(2,'0')}. ${qTitle}`
      : `${String(idx+1).padStart(2,'0')}. 자가점검 항목`;

    // 제목
    const titleEl = document.createElement('div');
    titleEl.className = 'question-title';
    titleEl.textContent = displayTitle;
    titleEl.style.cssText = `
      position:absolute;
      top:${currentY}px; left:${textLeftX}px;
      font-size:${titleFontSize}px;
      pointer-events:none;
    `;

    // 내용
    const contentEl = document.createElement('div');
    contentEl.className = 'question-content';
    contentEl.textContent = qContent;
    contentEl.style.cssText = `
      position:absolute;
      top:${currentY + Math.round(titleFontSize * 1.6)}px;
      left:${textLeftX}px;
      max-width:${Math.round(renderW * 0.62)}px;
      font-size:${contentFontSize}px;
      pointer-events:none;
    `;

    // 라디오 그룹
    const radioGroup = document.createElement('div');
    radioGroup.className = 'radio-group';
    radioGroup.style.cssText = `
      position:absolute;
      top:${currentY + Math.round(titleFontSize * 1.4)}px;
      left:${radioYesX}px;
      display:flex;
      gap:${Math.round(20*scale)}px;
      align-items:center;
      pointer-events:all;
    `;

    // 예 라디오
    const yesLabel = document.createElement('label');
    yesLabel.className   = 'radio-label yes-label';
    yesLabel.style.fontSize = `${radioFontSize}px`;
    const yesRadio = document.createElement('input');
    yesRadio.type  = 'radio';
    yesRadio.name  = `question_${qCd}`;
    yesRadio.value = 'Y';
    yesRadio.style.cssText = `
      width:${Math.round(18*scale)}px; height:${Math.round(18*scale)}px;
      accent-color:#FFBC00; cursor:pointer;
    `;
    yesRadio.addEventListener('change', () => {
      if (yesRadio.checked) { userAnswers[qCd] = 'Y'; checkSelfCheckComplete(submitBtn); }
    });
    yesLabel.appendChild(yesRadio);
    yesLabel.appendChild(document.createTextNode(' 예'));

    // 아니오 라디오
    const noLabel = document.createElement('label');
    noLabel.className   = 'radio-label no-label';
    noLabel.style.fontSize = `${radioFontSize}px`;
    const noRadio = document.createElement('input');
    noRadio.type  = 'radio';
    noRadio.name  = `question_${qCd}`;
    noRadio.value = 'N';
    noRadio.style.cssText = `
      width:${Math.round(18*scale)}px; height:${Math.round(18*scale)}px;
      accent-color:#E53E3E; cursor:pointer;
    `;
    noRadio.addEventListener('change', () => {
      if (noRadio.checked) { userAnswers[qCd] = 'N'; checkSelfCheckComplete(submitBtn); }
    });
    noLabel.appendChild(noRadio);
    noLabel.appendChild(document.createTextNode(' 아니오'));

    radioGroup.appendChild(yesLabel);
    radioGroup.appendChild(noLabel);

    // 구분선
    const divider = document.createElement('div');
    divider.className = 'question-divider';
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
      const qstnList = (currentTaskData.qstn_list || []).slice(0, 3);
      if (wrapper && bgImg && bgImg.complete) buildSelfCheckOverlay(wrapper, bgImg, qstnList);
    }
  }, 100);
});

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
      const confirmed = await window.electronAPI.dialogYesNo(
        '자가점검 재확인',
        '보안 지침에 위배되는 답변 항목이 존재합니다.\n이대로 점검 결과를 제출하시겠습니까?'
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
      await window.electronAPI.dialogInfo('알림', resData.message || '준법 프로그램 수행 기록이 정상적으로 저장되었습니다.');
      terminateProgram();
    } else if ([400, 404, 500].includes(response.status)) {
      await window.electronAPI.dialogWarning('제출 실패', resData.message || '알 수 없는 오류');
      terminateProgram();
    } else {
      await window.electronAPI.dialogError('오류', `정의되지 않은 서버 응답 에러가 발생했습니다.\nStatus Code: ${response.status}`);
      terminateProgram();
    }
  } catch (e) {
    await window.electronAPI.dialogError('네트워크 오류', `서버에 서약 데이터를 전송하지 못했습니다.\n\n에러: ${e.message}`);
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
