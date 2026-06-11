import streamlit as st
from sidebar import draw_sidebar
from styles import apply_custom_css
from pages.coming_soon import show_coming_soon

# 🌟 [수정] 공식 저장소 지원 라이브러리로 변경
from streamlit_cookies_manager import EncryptedCookieManager

# 페이지 함수 임포트
from pages.dashboard import show_dashboard_page
from pages.task_management import show_task_management_page
from pages.employee_management import show_employee_management_page

# 1. 페이지 설정 (중복 제거 통합)
st.set_page_config(
    page_title="KB Compliance Admin",
    layout="wide"
)

# 2. 전역 스타일 적용
apply_custom_css()

# =========================================================================
# 🔐 1. 시스템 로그인 로직 (EncryptedCookieManager 기반)
# =========================================================================
# 쿠키 암호화를 위한 비밀키 설정 (원하는 문자열로 자유롭게 변경 가능합니다)
cookies = EncryptedCookieManager(
    password="kb_compliance_admin_secret_cookie_key_123!"
)

# 스트림릿에서 쿠키 매니저가 정상적으로 로드될 때까지 잠시 대기 (필수 방어코드)
if not cookies.ready():
    st.stop()

# 브라우저 쿠키에서 로그인 여부 가져오기
cookie_logged_in = cookies.get("logged_in")

# 세션 상태 초기화 (쿠키가 'True' 문자열이면 로그인 유지)
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = True if cookie_logged_in == "True" else False

# 로그인되지 않은 상태일 때 (로그인 폼 렌더링 후 코드 실행 정지)
if not st.session_state["logged_in"]:
    # 화면 중앙 정렬을 위한 여백 컬럼
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        st.markdown("<br><br><br><br>", unsafe_allow_html=True)
        st.markdown('<h2 style="text-align: center;">🔐 시스템 로그인</h2>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 엔터키로 로그인되도록 form 사용
        with st.form(key="login_form"):
            username = st.text_input("아이디", placeholder="admin")
            password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
            
            submit_btn = st.form_submit_button("로그인", use_container_width=True)
            
            if submit_btn:
                # 하드코딩된 아이디/비밀번호 검증
                if username == "admin" and password == "kbdata1!":
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    
                    # 🌟 [핵심] 브라우저 쿠키에 로그인 유효 상태 저장 및 즉시 반영(save)
                    cookies["logged_in"] = "True"
                    cookies["username"] = username
                    cookies.save() 
                    
                    st.rerun() # 로그인 성공 시 화면을 새로고침하여 메인 화면으로 이동
                else:
                    st.error("아이디 또는 비밀번호가 일치하지 않습니다.")
                    
    # 💡 로그인이 완료되지 않았다면, 아래 메인 코드가 실행되지 않도록 여기서 완전히 멈춤
    st.stop()


# 💡 [참고] 추후 사이드바 등에서 로그아웃 버튼을 구현하실 때 아래처럼 사용하시면 됩니다.
# if st.sidebar.button("로그아웃"):
#     cookies["logged_in"] = "False"
#     cookies.save()
#     st.session_state["logged_in"] = False
#     st.rerun()

# 3. 세션 상태 초기화
if 'menu' not in st.session_state:
    st.session_state.menu = "현황 조회"

# 4. 사이드바 구성 실행 (🌟 생성해둔 cookies 매니저 객체를 주입합니다)
draw_sidebar(cookies=cookies)

# 5. 페이지 라우팅 로직
if st.session_state.menu == "현황 조회":
    show_dashboard_page()

elif st.session_state.menu == "준법 TASK":
    show_task_management_page()

elif st.session_state.menu == "직원 관리":
    show_employee_management_page()

else:
    # 아직 구현되지 않은 페이지들은 기존 common_pages 함수 호출
    show_coming_soon(st.session_state.menu)

# streamlit run admin.py