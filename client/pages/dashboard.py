import streamlit as st
import pandas as pd

from datetime import datetime
from api_utils import fetch_emp_answers, fetch_compliance_tasks
from styles import KB_YELLOW, apply_dashboard_style
from common.toast import show_toast

# =========================================================================
# 💡 [신규 추가] 하단 필터 상태를 변경하는 콜백 함수 (버튼 클릭 시 동작)
# =========================================================================
def update_status_filter(new_status):
    st.session_state.status_filter = new_status

def show_dashboard_page():
        
    apply_dashboard_style()

    # [타이틀 영역] 상단 새로고침 버튼 레이아웃 구조 정렬
    title_col, empty_col, btn_col1 = st.columns([2, 6.3, 0.8])
    
    with title_col:
        st.markdown('<div class="page-title">현황조회</div>', unsafe_allow_html=True)
        
    with btn_col1:
        if st.button("", icon=":material/refresh:", help="새로고침", use_container_width=True):
            show_toast("success", "데이터가 새로고침 되었습니다!")
            st.rerun()

    # --------------------------------------------------------------------------------
    # [박스 1]: ■ 준법 항목 선택 영역
    # --------------------------------------------------------------------------------
    with st.container():
        st.markdown('<div class="card-content-v2">', unsafe_allow_html=True)
        
        col_sel = st.columns([1], gap="small")[0]
        
        with col_sel:
            st.markdown('<div class="box-section-title">■ 준법 항목 및 적용일 선택</div>', unsafe_allow_html=True)
            
            # 두 셀렉트 박스를 같은 행에 나란히 배치하기 위해 내부를 2개로 분할
            inner_col1, inner_col2 = st.columns([2.5, 1], gap="small")
            
            # fetch_compliance_tasks 호출
            status_code, task_list = fetch_compliance_tasks()
            
            selected_task_id = 0
            selected_app_seq = None
            
            if status_code == 200 and isinstance(task_list, list) and len(task_list) > 0:
                task_dict = {task["task_id"]: task for task in task_list}
                
                # [첫 번째 드롭다운] 왼쪽 내부 컬럼에 배치
                with inner_col1:
                    selected_task_id = st.selectbox(
                        "준법 항목 선택",
                        options=list(task_dict.keys()),
                        format_func=lambda x: task_dict[x].get("task_nm", "이름 없음"),
                        label_visibility="collapsed"
                    )
                
                current_task = task_dict.get(selected_task_id, {})
                app_dt_list = current_task.get("task_app_dt", [])
                
                # [두 번째 드롭다운] 오른쪽 내부 컬럼에 배치
                with inner_col2:
                    if app_dt_list:
                        seq_to_date = {0: "전체"} 
                        for item in app_dt_list:
                            raw_date = item.get("task_app_dt", "")
                            clean_date = raw_date
                            display_text = f"{clean_date} ({item['app_seq']}회차)"
                            seq_to_date[item["app_seq"]] = display_text
                        
                        sorted_seqs = sorted(list(seq_to_date.keys()))
                        
                        selected_app_seq = st.selectbox(
                            "적용일 선택",
                            options=sorted_seqs,
                            format_func=lambda x: seq_to_date[x],
                            label_visibility="collapsed"
                        )
                    else:
                        st.info("할당된 적용일 없음")
            else:
                st.info("등록된 준법 항목이 없습니다.")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # --------------------------------------------------------------------------------
    # [조회 방어 조건 및 API 호출]
    # --------------------------------------------------------------------------------
    if selected_task_id == 0 or selected_app_seq is None:
        return  

    # 🌟 api_utils로부터 순수 원본 뼈대 데이터프레임을 받아옵니다.
    raw_df = fetch_emp_answers(task_id=selected_task_id, app_seq=selected_app_seq)
    
    if raw_df is not None and not raw_df.empty:
        # 🌟 [통계 집계]: 화면단에서 순수 필드 데이터 기반으로 수치 연산 수행
        total_count = len(raw_df)
        done_count = len(raw_df[raw_df["emp_main_ans_yn"].isin(["Y", True])])
        pending_count = len(raw_df[raw_df["emp_main_ans_yn"].isin(["N", False])])
        
        today = datetime.now().strftime('%Y-%m-%d')
        # ans_dt가 null일 경우 방어 처리하며 오늘 완료자 계산
        today_done = len(raw_df[
            (raw_df["emp_main_ans_yn"].isin(["Y", True])) & 
            (raw_df['ans_dt'].fillna('').str.contains(today, na=False))
        ])

        if "status_filter" not in st.session_state:
            st.session_state.status_filter = "전체"

        # --------------------------------------------------------------------------------
        # [박스 2]: [대시보드 통계] 영역 (기존 오버레이 CSS 및 디자인 스펙 100% 동일)
        # --------------------------------------------------------------------------------
        with st.container():
            m_col1, m_col2, m_col3 = st.columns(3, gap="small")
            
            card_style = """
            <style>
                .metric-card {
                    height: 110px;
                    padding: 15px;
                    border-radius: 10px;
                    border: 1px solid #e0e0e0;
                    background-color: #ffffff;
                    box-sizing: border-box;
                    margin-bottom: 10px; /* 카드와 버튼 사이의 여백 */
                }
            </style>
            """
            st.markdown(card_style, unsafe_allow_html=True)

            with m_col1:
                st.markdown(f"""
                    <div class="metric-card">
                        <div style="color: #666; font-size: 14px; font-weight: 600;">대상자 총원</div>
                        <div style="font-size: 24px; font-weight: bold; margin-top: 5px;">{total_count} 명</div>
                        <div style="color: #999; font-size: 12px; margin-top: 5px;">DB 등록 기준</div>
                    </div>
                """, unsafe_allow_html=True)
                # 🌟 콜백 연동 아규먼트를 화면 필터 코드 규칙과 매핑 ("전체")
                st.button("전체 대상자 보기", key="click_all", use_container_width=True, on_click=update_status_filter, args=("전체",))

            with m_col2:
                st.markdown(f"""
                    <div class="metric-card">
                        <div style="color: #666; font-size: 14px; font-weight: 600;">답변 완료</div>
                        <div style="color: {KB_YELLOW}; font-size: 24px; font-weight: bold; margin-top: 5px;">{done_count} 명</div>
                        <div style="color: #4CAF50; font-size: 12px; margin-top: 5px;">(오늘 +{today_done}명 완료)</div>
                    </div>
                """, unsafe_allow_html=True)
                # 🌟 콜백 연동 아규먼트를 화면 필터 코드 규칙과 매핑 ("완료")
                st.button("답변 완료자 보기", key="click_done", use_container_width=True, on_click=update_status_filter, args=("완료",))

            with m_col3:
                st.markdown(f"""
                    <div class="metric-card">
                        <div style="color: #666; font-size: 14px; font-weight: 600;">미답변(진행중)</div>
                        <div style="color: #FF4B4B; font-size: 24px; font-weight: bold; margin-top: 5px;">{pending_count} 명</div>
                        <div style="color: #999; font-size: 12px; margin-top: 5px;">미답변자 {pending_count}명</div>
                    </div>
                """, unsafe_allow_html=True)
                # 🌟 콜백 연동 아규먼트를 화면 필터 코드 규칙과 매핑 ("미완료")
                st.button("미답변자 보기", key="click_pending", use_container_width=True, on_click=update_status_filter, args=("미완료",))


        # --------------------------------------------------------------------------------
        # [박스 3]: [상세 목록] 영역
        # --------------------------------------------------------------------------------
        with st.container():
            st.markdown('<div class="card-content-v2">', unsafe_allow_html=True)
            col_search, col_filter = st.columns([3.6, 1], gap="small")
            
            with col_search:
                search = st.text_input("검색", placeholder="이름, 사원번호 입력", label_visibility="collapsed")
            with col_filter:
                # 🌟 Selectbox UI 동기화 옵션 값을 기존 한글 구조인 ["전체", "완료", "미완료"] 그대로 유지
                status_filter = st.selectbox(
                    "필터", 
                    ["전체", "완료", "미완료"], 
                    key="status_filter", 
                    label_visibility="collapsed"
                )
            
            f_df = raw_df.copy()
            
            # 🌟 필터링 조건 분기 (원본 데이터 상태에 매칭)
            if status_filter != "전체":
                target_code = "Y" if status_filter == "완료" else "N"
                f_df = f_df[f_df["emp_main_ans_yn"].isin([target_code, True if target_code == "Y" else False])]                
            
            # 이름(emp_nm) 혹은 사번(emp_no) 유연하게 다중 타겟 텍스트 와일드카드 필터링 적용
            if search:
                f_df = f_df[
                    f_df['emp_nm'].astype(str).str.contains(search) | 
                    f_df['emp_no'].astype(str).str.contains(search)
                ]

            st.markdown('<div style="margin-top: 10px;"></div>', unsafe_allow_html=True)
            
            # 🌟 [최종 화면단 포맷팅 파이프라인 수립 구역]
            display_df = pd.DataFrame()
            
            if not f_df.empty:
                # 1. 이름 (사번) 가로 병합 처리
                display_df["이름"] = f_df["emp_nm"].astype(str) + " (" + f_df["emp_no"].astype(str) + ")"
                
                # 2. 준법명 명칭 조립 및 방어 코드 적용
                task_name = f_df["task_nm"].astype(str) if "task_nm" in f_df.columns else "준법 항목"
                app_seq_val = f_df["app_seq"].astype(str) if "app_seq" in f_df.columns else "-"
                app_dt_val = f_df["task_app_dt"].astype(str) if "task_app_dt" in f_df.columns else "-"
                display_df["준법명"] = task_name + "(" + app_seq_val + "회차) - " + app_dt_val
                
                # 3. IP 정보 매핑
                display_df["IP"] = f_df["ip"] if "ip" in f_df.columns else "-"
                
                # 4. 답변여부 한글 치환 고도화 (불리언 및 코드값 완전 수용)
                display_df["답변여부"] = f_df["emp_main_ans_yn"].map({'Y': '완료', True: '완료', 'N': '미완료', False: '미완료'}).fillna('미완료')
                
                # 5. 정상답변여부 한글 치환 고도화 및 미완료자 하이픈 처리
                display_df["정상답변여부"] = f_df["emp_ans_agr_yn"].map({'Y': '정상', True: '정상', 'N': '비정상', False: '비정상'}).fillna('비정상')
                display_df.loc[display_df["답변여부"] != '완료', "정상답변여부"] = '-'
                
                # 6. 완료 일시 바인딩
                display_df["답변일시"] = f_df["ans_dt"] if "ans_dt" in f_df.columns else "-"
                
                # 기존 렌더링 명칭 및 정렬 순서 그대로 칼럼 동기화
                display_df = display_df[["이름", "준법명", "IP", "답변여부", "정상답변여부", "답변일시"]]
            else:
                # 검색 데이터가 전혀 없을 때 빈 헤더 그리드 유지를 위한 빈 뼈대 생성
                display_df = pd.DataFrame(columns=["이름", "준법명", "IP", "답변여부", "정상답변여부", "답변일시"])

            st.data_editor(
                display_df,
                hide_index=True,
                use_container_width=True,
                column_config={
                        "이름": st.column_config.Column(width="medium"),
                        "사원번호": st.column_config.Column(width="medium"), # 기존 스펙 유지 보완
                        "IP": st.column_config.Column(width="medium"),
                        "답변여부": st.column_config.Column(width="small"),
                        "답변일시": st.column_config.Column(width="medium"),
                },
                disabled=True,
                key="editor"
            )
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("선택된 준법 항목에 해당하는 답변 로그 데이터가 존재하지 않습니다.")