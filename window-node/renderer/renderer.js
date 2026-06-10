// =========================================================================
// [서버 및 환경 설정]
// =========================================================================
const BASE_URL = 'http://192.168.62.94:8080';
// const BASE_URL = 'http://127.0.0.1:8080';

// =========================================================================
// 전역 상태
// =========================================================================
let empNoStr = '';
let taskIdStr = '';
let appSeqStr = '';
let empNameStr = '홍길동';
let dateStr = '2026년 6월';
let taskTypeStr = '';

// 자가점검용 데이터
let userAnswers = {};       // { qstn_cd: 'Y' | 'N' | '' }
let standardAnswers = {};   // { qstn_cd: 'Y' | 'N' }

// =========================================================================
// 유틸리티
// =========================================================================
function terminateProgram() {
  window.electronAPI.terminate();
}

function showLoading(visible) {
  document.getElementById('loading-overlay').style.display = visible ? 'flex' : 'none';
}

function showApp(visible) {
  document.getElementById('app-container').style.display = visible ? 'flex' : 'none';
}

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
    taskIdStr = String(taskData.task_id ?? '');
    appSeqStr = String(taskData.app_seq ?? '');
    taskTypeStr = taskData.task_type || 'ETHICS';

    // 자가점검 표준 응답 캐싱
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

// =========================================================================
// [타입 A] 윤리강령 서약서 화면
// =========================================================================
async function drawEthicsUI(taskData) {
  const container = document.getElementById('app-container');
  container.innerHTML = '';
  container.style.background = '#ffffff';

  const imgFilename = taskData.img_flnm || 'TEST_1.png';
  const imageUrl = `${BASE_URL}/images/${imgFilename}`;

  // wrapper
  const wrapper = document.createElement('div');
  wrapper.id = 'ethics-wrapper';

  // 배경 이미지 엘리먼트
  const bgImg = document.createElement('img');
  bgImg.id = 'ethics-bg-img';
  bgImg.alt = '윤리강령';

  // 이미지 로드 후 오버레이 세팅
  bgImg.onload = () => {
    setupEthicsElements(wrapper, bgImg);
  };

  bgImg.onerror = () => {
    // 서버 이미지 실패 시 로컬 파일로 폴백
    bgImg.src = 'TEST_1.png';
    bgImg.onerror = () => {
      terminateProgram();
    };
  };

  bgImg.src = imageUrl;

  wrapper.appendChild(bgImg);
  container.appendChild(wrapper);
}

function setupEthicsElements(wrapper, bgImg) {
  // 기존 오버레이 제거 후 재생성
  const existingOverlay = wrapper.querySelector('#ethics-overlay');
  if (existingOverlay) existingOverlay.remove();

  const imgH = bgImg.clientHeight;
  const imgTop = bgImg.getBoundingClientRect().top - wrapper.getBoundingClientRect().top;

  // 오버레이 컨테이너
  const overlay = document.createElement('div');
  overlay.id = 'ethics-overlay';
  overlay.style.cssText = `
    position: absolute;
    top: ${imgTop}px;
    left: 50%;
    transform: translateX(-50%);
    width: ${bgImg.clientWidth}px;
    height: ${imgH}px;
    pointer-events: none;
  `;

  // 요소 묶음 wrapper (세로 위치: 83% 지점 기준)
  const elemDiv = document.createElement('div');
  elemDiv.style.cssText = `
    position: absolute;
    left: 50%;
    top: ${imgH * 0.83}px;
    transform: translateX(-50%);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    pointer-events: all;
  `;

  // --- 체크박스 행 ---
  const checkRow = document.createElement('label');
  checkRow.className = 'ethics-checkbox-row';

  const checkbox = document.createElement('input');
  checkbox.type = 'checkbox';
  checkbox.id = 'ethics-agree-checkbox';

  const checkLabel = document.createElement('span');
  checkLabel.className = 'ethics-checkbox-label';
  checkLabel.textContent = "본인은 상기의 '윤리강령' 내용을 확인하였으며, 이를 준수할 것을 다짐합니다.";

  checkRow.appendChild(checkbox);
  checkRow.appendChild(checkLabel);

  // --- 날짜 텍스트 ---
  const dateEl = document.createElement('p');
  dateEl.className = 'ethics-date-text';
  dateEl.textContent = dateStr;

  // --- 사번 / 서명 텍스트 ---
  const empEl = document.createElement('p');
  empEl.className = 'ethics-emp-text';
  empEl.textContent = `직원번호 : ${empNoStr}       서명 : ${empNameStr}`;

  // --- 제출 버튼 ---
  const submitBtn = document.createElement('button');
  submitBtn.className = 'submit-btn ethics-submit-btn disabled';
  submitBtn.textContent = '확인 및 업무 시작';
  submitBtn.style.cssText = `
    width: 240px;
    height: 40px;
    font-size: 13px;
    margin-top: 4px;
    pointer-events: all;
  `;

  // 체크박스 이벤트
  checkbox.addEventListener('change', () => {
    if (checkbox.checked) {
      submitBtn.classList.remove('disabled');
      submitBtn.classList.add('active');
    } else {
      submitBtn.classList.remove('active');
      submitBtn.classList.add('disabled');
    }
  });

  // 제출 버튼 클릭
  submitBtn.addEventListener('click', () => {
    if (submitBtn.classList.contains('active')) {
      onAgree();
    }
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

  // 배경 이미지
  const bgImg = document.createElement('img');
  bgImg.id = 'selfcheck-bg-img';
  bgImg.alt = '자가점검';
  bgImg.src = 'img_self_check_bg.png';

  bgImg.onerror = async () => {
    await window.electronAPI.dialogError(
      '오류',
      '자가점검 배경 이미지(img_self_check_bg.png)를 찾을 수 없습니다.'
    );
    terminateProgram();
  };

  bgImg.onload = () => {
    buildSelfCheckOverlay(wrapper, bgImg, qstnList);
  };

  wrapper.appendChild(bgImg);
  container.appendChild(wrapper);
}

function buildSelfCheckOverlay(wrapper, bgImg, qstnList) {
  const boxHeight = bgImg.clientHeight;
  const boxWidth  = bgImg.clientWidth;
  const naturalH  = bgImg.naturalHeight;
  const naturalW  = bgImg.naturalWidth;

  // -----------------------------------------------------------------------
  // 스케일 비율 (렌더 크기 / 원본 크기)
  // 기존 이미지 원본 해상도 기준으로 비율 계산
  // -----------------------------------------------------------------------
  const scaleH = boxHeight / naturalH;
  const scaleW = boxWidth  / naturalW;

  // -----------------------------------------------------------------------
  // [핵심 수치] 기존 이미지 레이아웃 기준 좌표값 (원본 px 기준)
  //
  //  이미지 구조 (원본 약 1280×960 기준 추정):
  //  ┌─────────────────────────────────────────────────────┐
  //  │  KB금융그룹 로고 헤더                                │  ~0~60px
  //  │  법규준수 자가점검 타이틀 + 우측 일러스트           │  ~60~220px
  //  │  안녕하세요 카드 + 점검 주기/소요시간/총문항 칩     │  ~220~350px
  //  │  점검 항목 라벨                                     │  ~350~400px
  //  ├─────────────────────────────────────────────────────┤
  //  │  [질문 1] ─────────────────────────── [예] [아니오] │  ~400~490px
  //  │  [질문 2] ─────────────────────────── [예] [아니오] │  ~490~580px
  //  │  [질문 3] ─────────────────────────── [예] [아니오] │  ~580~670px
  //  │                                                     │
  //  ├─────────────────────────────────────────────────────┤
  //  │  하단 안내 문구 (좌측)          [제출(확인)] 버튼   │  ~900~960px
  //  └─────────────────────────────────────────────────────┘
  //
  //  아래 수치는 원본 이미지 px 기준입니다.
  //  실제 이미지 해상도에 따라 startY_orig 값을 조정하세요.
  // -----------------------------------------------------------------------

  // 질문 목록 시작 Y (원본 px): "점검 항목" 라벨 아래 첫 질문 시작점
  const startY_orig  = 418;
  // 질문 간 세로 간격 (원본 px)
  const yGap_orig    = 92;
  // 질문 텍스트 왼쪽 여백 (원본 px)
  const textLeftX_orig = 78;
  // "예" 라디오 버튼 X 위치 (원본 px, 우측에서)
  const radioYesX_orig = naturalW - 195;
  // "아니오" 라디오 버튼 X 위치 (원본 px, 우측에서)
  const radioNoX_orig  = naturalW - 118;
  // 구분선 좌우 여백 (원본 px)
  const linePadding_orig = 60;
  // 구분선 Y 오프셋 (질문 currentY 기준, 원본 px)
  const dividerOffset_orig = 78;

  // 실제 렌더 좌표로 변환
  const startY      = Math.round(startY_orig  * scaleH);
  const yGap        = Math.round(yGap_orig    * scaleH);
  const textLeftX   = Math.round(textLeftX_orig * scaleW);
  const radioYesX   = Math.round(radioYesX_orig * scaleW);
  const radioNoX    = Math.round(radioNoX_orig  * scaleW);
  const linePadding = Math.round(linePadding_orig * scaleW);
  const dividerOffset = Math.round(dividerOffset_orig * scaleH);

  // 오버레이 컨테이너
  const overlay = document.createElement('div');
  overlay.id = 'selfcheck-overlay';
  overlay.style.cssText = `
    position: absolute;
    top: 0; left: 0;
    width: ${boxWidth}px;
    height: ${boxHeight}px;
    pointer-events: none;
  `;

  // userAnswers 초기화
  userAnswers = {};
  qstnList.forEach((qstn) => {
    userAnswers[qstn.qstn_cd] = '';
  });

  // -----------------------------------------------------------------------
  // 각 질문 렌더링
  // -----------------------------------------------------------------------
  qstnList.forEach((qstn, idx) => {
    const qCd     = qstn.qstn_cd;
    const qTitle  = qstn.qstn_nm  || '';
    const qContent= qstn.qstn_cn  || '';
    const currentY = startY + idx * yGap;

    const displayTitle = qTitle
      ? `${String(idx + 1).padStart(2, '0')}. ${qTitle}`
      : `${String(idx + 1).padStart(2, '0')}. 자가점검 항목`;

    // -- 제목 --
    const titleEl = document.createElement('div');
    titleEl.className = 'question-title';
    titleEl.textContent = displayTitle;
    titleEl.style.cssText = `
      position: absolute;
      top: ${currentY}px;
      left: ${textLeftX}px;
      font-size: ${Math.max(11, Math.round(13 * scaleH))}px;
      pointer-events: none;
    `;

    // -- 내용 --
    const contentEl = document.createElement('div');
    contentEl.className = 'question-content';
    contentEl.textContent = qContent;
    contentEl.style.cssText = `
      position: absolute;
      top: ${currentY + Math.round(20 * scaleH)}px;
      left: ${textLeftX}px;
      max-width: ${Math.round(boxWidth * 0.65)}px;
      font-size: ${Math.max(10, Math.round(11 * scaleH))}px;
      pointer-events: none;
    `;

    // -- 라디오 버튼 그룹 --
    const radioGroup = document.createElement('div');
    radioGroup.className = 'radio-group';
    radioGroup.style.cssText = `
      position: absolute;
      top: ${currentY + Math.round(18 * scaleH)}px;
      left: ${radioYesX}px;
      display: flex;
      gap: ${Math.round(14 * scaleW)}px;
      align-items: center;
      pointer-events: all;
    `;

    // 예 라디오
    const yesLabel = document.createElement('label');
    yesLabel.className = 'radio-label yes-label';
    yesLabel.style.fontSize = `${Math.max(10, Math.round(12 * scaleH))}px`;

    const yesRadio = document.createElement('input');
    yesRadio.type = 'radio';
    yesRadio.name = `question_${qCd}`;
    yesRadio.value = 'Y';
    yesRadio.style.accentColor = '#FFBC00';
    yesRadio.addEventListener('change', () => {
      if (yesRadio.checked) {
        userAnswers[qCd] = 'Y';
        checkSelfCheckComplete(submitBtn);
      }
    });
    yesLabel.appendChild(yesRadio);
    yesLabel.appendChild(document.createTextNode(' 예'));

    // 아니오 라디오
    const noLabel = document.createElement('label');
    noLabel.className = 'radio-label no-label';
    noLabel.style.fontSize = `${Math.max(10, Math.round(12 * scaleH))}px`;

    const noRadio = document.createElement('input');
    noRadio.type = 'radio';
    noRadio.name = `question_${qCd}`;
    noRadio.value = 'N';
    noRadio.style.accentColor = '#E53E3E';
    noRadio.addEventListener('change', () => {
      if (noRadio.checked) {
        userAnswers[qCd] = 'N';
        checkSelfCheckComplete(submitBtn);
      }
    });
    noLabel.appendChild(noRadio);
    noLabel.appendChild(document.createTextNode(' 아니오'));

    radioGroup.appendChild(yesLabel);
    radioGroup.appendChild(noLabel);

    // -- 구분선 --
    const divider = document.createElement('div');
    divider.className = 'question-divider';
    divider.style.cssText = `
      position: absolute;
      top: ${currentY + dividerOffset}px;
      left: ${linePadding}px;
      width: ${boxWidth - linePadding * 2}px;
      pointer-events: none;
    `;

    overlay.appendChild(titleEl);
    overlay.appendChild(contentEl);
    overlay.appendChild(radioGroup);
    overlay.appendChild(divider);
  });

  // -----------------------------------------------------------------------
  // 제출(확인) 버튼
  //  기존 이미지 기준: 우측 하단 고정 위치
  //  원본 기준: X = naturalW - 145, Y = naturalH - 42 (버튼 중심)
  // -----------------------------------------------------------------------
  const btnCenterX_orig = naturalW - 145;
  const btnCenterY_orig = naturalH - 42;
  const btnW_orig = 152;
  const btnH_orig = 52;

  const btnCenterX = Math.round(btnCenterX_orig * scaleW);
  const btnCenterY = Math.round(btnCenterY_orig * scaleH);
  const btnW = Math.round(btnW_orig * scaleW);
  const btnH = Math.round(btnH_orig * scaleH);

  const submitBtn = document.createElement('button');
  submitBtn.className = 'submit-btn disabled';
  submitBtn.id = 'selfcheck-submit-btn';
  submitBtn.textContent = '제출(확인)';
  submitBtn.style.cssText = `
    position: absolute;
    left: ${btnCenterX - btnW / 2}px;
    top:  ${btnCenterY - btnH / 2}px;
    width:  ${btnW}px;
    height: ${btnH}px;
    font-size: ${Math.max(11, Math.round(14 * scaleH))}px;
    border-radius: 8px;
    pointer-events: all;
  `;

  submitBtn.addEventListener('click', () => {
    if (submitBtn.classList.contains('active')) {
      onAgree();
    }
  });

  overlay.appendChild(submitBtn);
  wrapper.appendChild(overlay);
}

// 기존: checkSelfCheckComplete(submitBtn, btnLabel)
// 변경: checkSelfCheckComplete(submitBtn)
function checkSelfCheckComplete(submitBtn) {
  const allAnswered = Object.values(userAnswers).every((v) => v !== '');

  if (allAnswered) {
    submitBtn.classList.remove('disabled');
    submitBtn.classList.add('active');
  } else {
    submitBtn.classList.remove('active');
    submitBtn.classList.add('disabled');
  }
}


// =========================================================================
// 제출 처리 (on_agree)
// =========================================================================
async function onAgree() {
  const submitUrl = `${BASE_URL}/submit-compliance`;

  // 1. 정상응답 준수 여부 검증
  let isAllCorrect = true;
  if (taskTypeStr === 'SELF_CHECK') {
    for (const [qCd, userAns] of Object.entries(userAnswers)) {
      const correctAns = standardAnswers[qCd] || 'Y';
      if (userAns !== correctAns) {
        isAllCorrect = false;
        break;
      }
    }

    // 2. 오답 항목 있으면 재확인 팝업
    if (!isAllCorrect) {
      const confirmed = await window.electronAPI.dialogYesNo(
        '자가점검 재확인',
        '보안 지침에 위배되는 답변 항목이 존재합니다.\n이대로 점검 결과를 제출하시겠습니까?'
      );
      if (!confirmed) return; // 아니오 선택 시 제출 유보
    }
  }

  // 3. 최종 동의 여부 플래그
  const finalAgrYn = isAllCorrect ? 'Y' : 'N';

  // 4. 페이로드 구성
  const payload = {
    task_id: /^\d+$/.test(taskIdStr) ? parseInt(taskIdStr, 10) : null,
    app_seq: /^\d+$/.test(appSeqStr) ? parseInt(appSeqStr, 10) : null,
    emp_no: empNoStr,
    emp_main_ans_yn: 'Y',
    emp_ans_agr_yn: finalAgrYn,
    answers: [],
  };

  if (taskTypeStr === 'SELF_CHECK') {
    payload.answers = Object.entries(userAnswers).map(([qCd, ans]) => ({
      qstn_cd: qCd,
      emp_ans_yn: ans,
    }));
  }

  // 5. 서버 전송
  try {
    const response = await fetch(submitUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(3000),
    });

    const resData = await response.json().catch(() => ({}));

    if (response.status === 200) {
      await window.electronAPI.dialogInfo(
        '알림',
        resData.message || '준법 프로그램 수행 기록이 정상적으로 저장되었습니다.'
      );
      terminateProgram();
    } else if ([400, 404, 500].includes(response.status)) {
      await window.electronAPI.dialogWarning(
        '제출 실패',
        resData.message || '알 수 없는 오류'
      );
      terminateProgram();
    } else {
      await window.electronAPI.dialogError(
        '오류',
        `정의되지 않은 서버 응답 에러가 발생했습니다.\nStatus Code: ${response.status}`
      );
      terminateProgram();
    }
  } catch (e) {
    await window.electronAPI.dialogError(
      '네트워크 오류',
      `서버에 서약 데이터를 전송하지 못했습니다.\n네트워크 연결 상태를 재확인해 주세요.\n\n에러: ${e.message}`
    );
    terminateProgram();
  }
}

// =========================================================================
// 진입점: Electron 메인 프로세스로부터 초기화 이벤트 수신
// =========================================================================
window.electronAPI.onInit(async ({ empNo }) => {
  empNoStr = empNo;

  // 데이터 조회
  const taskData = await fetchTaskAndInit();

  // 데이터 없으면 즉시 종료 (Python의 4번 단계와 동일)
  if (!taskData) {
    terminateProgram();
    return;
  }

  // 로딩 숨기고 앱 표시 + 창 화면에 나타내기
  showLoading(false);
  showApp(true);
  window.electronAPI.showWindow();

  // UI 그리기
  if (taskTypeStr === 'ETHICS') {
    await drawEthicsUI(taskData);
  } else if (taskTypeStr === 'SELF_CHECK') {
    drawSelfCheckUI(taskData);
  }
});
