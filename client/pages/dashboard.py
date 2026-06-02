import streamlit as st
from datetime import datetime
from api_utils import fetch_emp_answers, fetch_compliance_tasks
from styles import KB_YELLOW, apply_dashboard_style
from common.toast import show_toast

def show_dashboard_page():
    apply_dashboard_style()

    # [타이틀 영역] 상단 새로고침 버튼 레이아웃 구조 정렬
    title_col, empty_col, btn_col1 = st.columns([2, 6.3, 0.8])
    
    with title_col:
        st.markdown('<div class="page-title">현황조회</div>', unsafe_allow_html=True)
        
    with btn_col1:
        if st.button("새로고침", use_container_width=True):
            show_toast("success", "데이터가 새로고침 되었습니다!")
            st.rerun()

    # --------------------------------------------------------------------------------
    # [박스 1]: ■ 준법 항목 선택 영역
    # --------------------------------------------------------------------------------
    with st.container():
        st.markdown('<div class="card-content-v2">', unsafe_allow_html=True)
        st.markdown('<div class="box-section-title">■ 준법 항목 선택</div>', unsafe_allow_html=True)
        
        # fetch_compliance_tasks 호출하여 실시간 DB 항목 조회
        status_code, task_list = fetch_compliance_tasks()
        
        # 방어 코드 및 셀렉트박스 표시용 딕셔너리 매핑
        task_options = {}
        if status_code == 200 and isinstance(task_list, list) and len(task_list) > 0:
            for task in task_list:
                task_options[task["task_id"]] = task["task_nm"]
        else:
            task_options[0] = "등록된 준법 항목이 없습니다."
        
        # 준법 항목 셀렉트 박스
        selected_task_id = st.selectbox(
            "준법 항목 선택",
            options=list(task_options.keys()),
            format_func=lambda x: task_options[x],
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # --------------------------------------------------------------------------------
    # 💡 [조회 방어 조건 추가]: 등록된 항목이 없거나 ID가 0이면 API를 호출하지 않고 종료
    # --------------------------------------------------------------------------------
    if selected_task_id == 0:
        st.info("등록된 준법 항목이 없습니다. 항목을 먼저 등록해 주세요.")
        return  # 함수를 여기서 종료하여 아래 API 호출 및 대시보드 렌더링을 차단합니다.

    # 정상적인 타스크 ID가 있을 때만 백엔드 서버 조회 수행
    df = fetch_emp_answers(task_id=selected_task_id)
    
    if not df.empty:
        # 데이터프레임 컬럼 구조: ["사원명", "사원번호", "IP", "답변여부", "답변일시"]
        total_count = len(df)
        done_count = len(df[df["답변여부"] == "완료"])
        pending_count = len(df[df["답변여부"] == "미완료"])
        today = datetime.now().strftime('%Y-%m-%d')
        today_done = len(df[(df["답변여부"] == "완료") & (df['답변일시'].fillna('').str.contains(today, na=False))])

        if "metric_filter" not in st.session_state:
            st.session_state.metric_filter = "전체"

        # --------------------------------------------------------------------------------
        # [박스 2]: [대시보드 통계] 영역
        # --------------------------------------------------------------------------------
        with st.container():
            st.markdown('<div class="card-content-v2">', unsafe_allow_html=True)
            
            m_col1, m_col2, m_col3 = st.columns(3, gap="small")
            invisible_style = """
            <style>
                div[data-testid="stHorizontalBlock"] div.stButton > button[key="click_all"],
                div[data-testid="stHorizontalBlock"] div.stButton > button[key="click_done"],
                div[data-testid="stHorizontalBlock"] div.stButton > button[key="click_pending"] {
                    position: absolute !important;
                    width: 100% !important;
                    height: 140px !important;
                    background-color: transparent !important;
                    color: transparent !important;
                    border: none !important;
                    cursor: pointer !important;
                    z-index: 10 !important;
                }
            </style>
            """

            with m_col1:
                st.markdown(invisible_style, unsafe_allow_html=True)
                if st.button("전체보기", key="click_all", use_container_width=True):
                    st.session_state.metric_filter = "전체"
                
                st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-card" style="width: 100%; cursor: pointer;">
                            <div class="metric-label">대상자 총원</div>
                            <div class="metric-value">{total_count} 명</div>
                            <div class="metric-sub">DB 등록 기준</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            with m_col2:
                st.markdown(invisible_style, unsafe_allow_html=True)
                if st.button("완료보기", key="click_done", use_container_width=True):
                    st.session_state.metric_filter = "완료"
                
                st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-card" style="width: 100%; cursor: pointer;">
                            <div class="metric-label">답변 완료</div>
                            <div class="metric-value" style="color: {KB_YELLOW};">{done_count} 명</div>
                            <div class="metric-sub" style="color: #4CAF50;">(오늘 +{today_done}명 완료)</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            with m_col3:
                st.markdown(invisible_style, unsafe_allow_html=True)
                if st.button("미동의보기", key="click_pending", use_container_width=True):
                    st.session_state.metric_filter = "미완료"
                
                st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-card" style="width: 100%; cursor: pointer;">
                            <div class="metric-label">미답변(진행중)</div>
                            <div class="metric-value" style="color: #FF4B4B;">{pending_count} 명</div>
                            <div class="metric-sub">미답변자 {pending_count}명</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)


        # --------------------------------------------------------------------------------
        # [박스 3]: [상세 목록] 영역
        # --------------------------------------------------------------------------------
        with st.container():
            st.markdown('<div class="card-content-v2">', unsafe_allow_html=True)
            col_search, col_filter = st.columns([3.6, 1], gap="small")
            
            with col_search:
                search = st.text_input("검색", placeholder="사원명, 사원번호 입력", label_visibility="collapsed")
            with col_filter:
                status_filter = st.selectbox("필터", ["전체", "완료", "미완료"], label_visibility="collapsed")
            
            f_df = df.copy()
            current_filter = status_filter
            if st.session_state.metric_filter != "전체" and status_filter == "전체":
                current_filter = st.session_state.metric_filter
            if current_filter != "전체":
                f_df = f_df[f_df["답변여부"] == current_filter]                
            if search:
                f_df = f_df[f_df['사원명'].astype(str).str.contains(search) | f_df['사원번호'].astype(str).str.contains(search)]

            st.markdown('<div style="margin-top: 10px;"></div>', unsafe_allow_html=True)
            st.data_editor(
                f_df,
                hide_index=True,
                use_container_width=True,
                column_config={
                        "사원명": st.column_config.Column(width="medium"),
                        "사원번호": st.column_config.Column(width="medium"),
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