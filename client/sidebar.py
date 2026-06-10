import streamlit as st

def draw_sidebar(cookies=None):
    """
    사이드바를 렌더링하고 메뉴 이동 및 로그아웃을 제어합니다.
    버튼 좌측 정렬 CSS 및 로그아웃 버튼 하단 고정 레이아웃이 적용되었습니다.
    """
    with st.sidebar:
        # 🌟 [신규 CSS 주입]: 사이드바 내부의 모든 버튼 텍스트를 강제로 좌측 정렬합니다.
        st.markdown("""
            <style>
                /* 사이드바 안의 모든 버튼 서식을 왼쪽 정렬로 강제 전환 */
                section[data-testid="stSidebar"] .stButton > button {
                    justify-content: flex-start !important;
                    text-align: left !important;
                    padding-left: 15px !important;
                }
                
                /* 로그아웃 버튼 하단 고정을 위해 마커 바로 뒤의 버튼 컨테이너를 타겟팅 */
                section[data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.sidebar-logout-marker) {
                    display: none !important;
                }
                section[data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.sidebar-logout-marker) + div[data-testid="stElementContainer"] {
                    position: absolute;
                    bottom: 20px;
                    inset-inline: 10px;
                    width: auto;
                }
            </style>
        """, unsafe_allow_html=True)

        # 상단 로고 영역
        try:
            st.image("assets/kbds_logo.png", use_container_width=False)
        except:
            st.markdown("### KBDS Compliance")
        st.divider()

        # -------------------------------------------------------------------------
        # 📁 상단 메뉴 버튼 영역 (이제 모두 깔끔하게 왼쪽 정렬됩니다)
        # -------------------------------------------------------------------------
        if st.button("📊 현황 조회", use_container_width=True): 
            st.session_state.menu = "현황 조회"
            st.session_state.current_page = "main"
            if "df_selection" in st.session_state:
                del st.session_state.df_selection
            st.rerun()

        if st.button("📁 직원 관리", use_container_width=True): 
            st.session_state.menu = "직원 관리"
            st.rerun()

        if st.button("📈 준법 TASK", use_container_width=True): 
            st.session_state.menu = "준법 TASK"
            st.session_state.task_page_mode = "list"
            st.session_state.selected_task_data = None
            st.session_state.temp_app_dates = []
            st.rerun()
        
        # -------------------------------------------------------------------------
        # 🔐 [개선] 최하단 로그아웃 버튼 영역 (HTML 컨테이너 박스로 묶어 바닥에 고정)
        # -------------------------------------------------------------------------
        # 공백 컴포넌트로 간격을 벌려주어 일반 메뉴와 겹침을 방지합니다.
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        
        # 마커 컴포넌트 삽입 (CSS에서 이 마커의 다음 형제 요소를 bottom 고정함)
        st.markdown('<span class="sidebar-logout-marker"></span>', unsafe_allow_html=True)
            
        if st.button("🔐로그아웃", use_container_width=True, help="클릭 시 로그인 화면으로 돌아갑니다."):
            # 1. 쿠키 초기화 및 저장
            if cookies is not None:
                cookies["logged_in"] = "False"
                cookies["username"] = ""
                cookies.save()
            
            # 2. 스트림릿 세션 상태 초기화 및 튕겨내기
            st.session_state["logged_in"] = False
            if "username" in st.session_state:
                del st.session_state["username"]
                
            # 기본 정렬 메뉴 리셋
            st.session_state.menu = "현황 조회"
            st.rerun()
