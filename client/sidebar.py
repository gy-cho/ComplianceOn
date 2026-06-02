import streamlit as st

def draw_sidebar():
    with st.sidebar:
        try:
            st.image("assets/kbds_logo.png", use_container_width=True)
        except:
            st.markdown("### KBDS Compliance")
        st.divider()

        # 메뉴 버튼 및 세션 상태 업데이트 (진입 시 모드 초기화 포함)
        if st.button("📊 현황 조회"): 
            st.session_state.menu = "현황 조회"
            st.rerun()

        if st.button("📁 직원 관리"): 
            st.session_state.menu = "직원 관리"
            st.rerun()

        if st.button("📈 콘텐츠 관리"): 
            st.session_state.menu = "콘텐츠 관리"
            # 💡 핵심: 메뉴 클릭 시 해당 페이지의 내부 뷰 모드를 항상 목록('list')으로 강제 초기화
            st.session_state.task_page_mode = "list"
            st.session_state.selected_task_data = None
            st.session_state.temp_app_dates = []
            st.rerun()
        
        st.markdown("<br><br>", unsafe_allow_html=True)