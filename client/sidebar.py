import streamlit as st

def draw_sidebar():
    with st.sidebar:
        try:
            st.image("assets/kbds_logo.png", use_container_width=True)
        except:
            st.markdown("### KBDS Compliance")
        st.divider()

        # 메뉴 버튼 및 세션 상태 업데이트
        if st.button("📊 현황 조회"): 
            st.session_state.menu = "현황 조회"
            st.rerun()

        if st.button("📁 대상자 관리"): 
            st.session_state.menu = "대상자 관리"
            st.rerun()

        if st.button("📈 콘텐츠 관리"): 
            st.session_state.menu = "콘텐츠 관리"
            st.rerun()
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.divider()
        
        if st.button("⚙️ 설정"): 
            st.session_state.menu = "문구편집"
            st.rerun()
 