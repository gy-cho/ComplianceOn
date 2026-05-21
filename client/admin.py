import streamlit as st
from sidebar import draw_sidebar
from styles import apply_custom_css
from pages.coming_soon import show_coming_soon

# 페이지 함수 임포트
from pages.dashboard import show_dashboard_page
from pages.content_management import show_content_management

# 1. 페이지 설정
st.set_page_config(
    page_title="KB Compliance Admin",
    layout="wide"
)

# 2. 전역 스타일 적용
apply_custom_css()

# 3. 세션 상태 초기화
if 'menu' not in st.session_state:
    st.session_state.menu = "현황 조회"

# 4. 사이드바 구성 실행
draw_sidebar()

# 5. 페이지 라우팅 로직
if st.session_state.menu == "현황 조회":
    show_dashboard_page()

elif st.session_state.menu == "콘텐츠 관리":
    show_content_management()

else:
    # 아직 구현되지 않은 페이지들은 기존 common_pages 함수 호출
    show_coming_soon(st.session_state.menu)