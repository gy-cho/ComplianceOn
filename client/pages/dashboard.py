import streamlit as st
from datetime import datetime
from api_utils import fetch_log_items, add_new_user, delete_users, fetch_compliance_items
from styles import KB_YELLOW, apply_dashboard_style
from common.toast import show_toast

# --- 직원 추가 팝업 함수 (기존 코드 100% 유지) ---
@st.dialog("직원 추가")
def show_add_user_dialog():
    new_user_name = st.text_input("이름", placeholder="이름을 입력하세요", label_visibility="collapsed")
    new_user_id = st.text_input("사번", placeholder="사번을 입력하세요", label_visibility="collapsed")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("취소", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("저장", type="primary", use_container_width=True):
            if new_user_name and new_user_id:
                # 💡 [참고] API 스펙에 맞추기 위해, 화면에 기재되지 않은 IP는 임시 공백("")으로 전달되도록 안전 조치
                code, res = add_new_user(new_user_id, new_user_name, "")
                st.success(res.get("message", "등록 성공"))
                st.rerun()
            else:
                st.error("이름과 사번을 모두 입력해주세요.")

def show_dashboard_page():
    apply_dashboard_style()

    # [타이틀 영역] 상단 버튼 레이아웃 구조 정렬 (기존 유지)
    title_col, empty_col, btn_col1, btn_col2 = st.columns([2, 5.5, 0.8, 0.8])
    
    with title_col:
        st.markdown('<div class="page-title">현황조회</div>', unsafe_allow_html=True)
        
    with btn_col1:
        if st.button("새로고침", use_container_width=True):
            show_toast("success", "test 되었습니다!")
            
    with btn_col2:
        if st.button("직원추가", type="primary", use_container_width=True):
            show_add_user_dialog()


    # --------------------------------------------------------------------------------
    # [박스 1]: ■ 준법 항목 선택 영역
    # --------------------------------------------------------------------------------
    with st.container():
        st.markdown('<div class="card-content-v2">', unsafe_allow_html=True)
        st.markdown('<div class="box-section-title">■ 준법 항목 선택</div>', unsafe_allow_html=True)
        
        # API 호출하여 실시간 DB 목록 조회
        status_code, task_items = fetch_compliance_items()
        
        # 정상적으로 데이터를 가져오지 못했거나 리스트가 비어있을 경우 방어 코드
        if status_code != 200 or not task_items:
            task_items = ["등록된 준법 항목이 없습니다."]
        
        # 준법 항목 셀렉트 박스 (하드코딩 배열 대신 API 결과 리스트 주입)
        compliance_item = st.selectbox(
            "준법 항목 선택",
            task_items,
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # 💡 [API 변경 대응] 새로 만들어진 API 구조를 기존 화면용 컬럼으로 이식
    df = fetch_log_items(compliance_item)
    
    if not df.empty:
        # 기존 코드의 변수 연산 정합성 유지 ("동의여부", "동의일시" 명칭 그대로 매핑)
        total_count = len(df)
        done_count = len(df[df["동의여부"] == "완료"])
        pending_count = len(df[df["동의여부"] == "미완료"])
        today = datetime.now().strftime('%Y-%m-%d')
        today_done = len(df[(df["동의여부"] == "완료") & (df['동의일시'].fillna('').str.contains(today, na=False))])

        if "metric_filter" not in st.session_state:
            st.session_state.metric_filter = "전체"

        # --------------------------------------------------------------------------------
        # [박스 2]: [대시보드 통계] 영역
        # --------------------------------------------------------------------------------
        with st.container():
            st.markdown('<div class="card-content-v2">', unsafe_allow_html=True)
            
            m_col1, m_col2, m_col3 = st.columns(3, gap="small")
            # 가로 블록 전체를 잡지 않고, 딱 타겟 버튼의 'key' 값만 저격하도록 변경합니다.
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
                            <div class="metric-label">동의 완료</div>
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
                            <div class="metric-label">미동의(진행중)</div>
                            <div class="metric-value" style="color: #FF4B4B;">{pending_count} 명</div>
                            <div class="metric-sub">미동의자 {pending_count}명</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)


        # --------------------------------------------------------------------------------
        # 구조 변경 [박스 3]: [상세 목록] 영역 (필터, 검색, 삭제 에디터 통합) (기존 유지)
        # --------------------------------------------------------------------------------
        with st.container():
            st.markdown('<div class="card-content-v2">', unsafe_allow_html=True)
            col_search, col_filter, col_del = st.columns([3, 1, 0.6], gap="small")
            
            with col_search:
                search = st.text_input("검색", placeholder="이름, 사번 입력", label_visibility="collapsed")
            with col_filter:
                status_filter = st.selectbox("필터", ["전체", "완료", "미완료"], label_visibility="collapsed")
            
            # 기존 데이터 필터링 로직 정합성 유지
            f_df = df.copy()
            current_filter = status_filter
            if st.session_state.metric_filter != "전체" and status_filter == "전체":
                current_filter = st.session_state.metric_filter
            if current_filter != "전체":
                f_df = f_df[f_df["동의여부"] == current_filter]                
            if search:
                f_df = f_df[f_df['이름'].astype(str).str.contains(search) | f_df['사번'].astype(str).str.contains(search)]

            # 체크박스 열 주입
            f_df.insert(0, "선택", False)

            # 에디터 렌더링 영역 (기존 테이블 비동기 삭제 제어 유지)
            st.markdown('<div style="margin-top: 10px;"></div>', unsafe_allow_html=True)
            edited_df = st.data_editor(
                f_df,
                hide_index=True,
                use_container_width=True,
                column_config={
                        "선택": st.column_config.CheckboxColumn(
                            "선택",
                            help="삭제할 직원을 선택하세요",
                            default=False,
                            width=40, # 픽셀 단위로 최소 크기 지정
                        ),
                        # 나머지 컬럼들이 남은 너비를 꽉 채우도록 비율(기본값 역할) 유도
                        "이름": st.column_config.Column(width="medium"),
                        "사번": st.column_config.Column(width="medium"),
                        "IP": st.column_config.Column(width="medium"),
                },
                disabled=["이름", "사번", "IP", "동의여부", "동의일시"], # 기존 컬럼 락 유지
                key="editor"
            )

            # 삭제 조건 계산 및 버튼 배치 적용
            selected_rows = edited_df[edited_df["선택"] == True]
            is_disabled = len(selected_rows) == 0

            with col_del:
                btn_label = f"{len(selected_rows)}명 삭제" if len(selected_rows) > 0 else "삭제"
                if st.button(btn_label, type="primary", use_container_width=True, disabled=is_disabled):
                    # 기존 컬럼명 '사번' 기준으로 정상 리스트화
                    code, res = delete_users(selected_rows["사번"].tolist())
                    if code == 200:
                        st.success(res.get("message", "삭제 성공"))
                        st.rerun()
                    else:
                        st.error(f"오류: {res.get('message', '삭제 중 오류가 발생했습니다.')}")
                        
            st.markdown('</div>', unsafe_allow_html=True)