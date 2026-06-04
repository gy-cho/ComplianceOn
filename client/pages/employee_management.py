import streamlit as st
import pandas as pd
from api_utils import fetch_all_employees, add_new_employee, delete_employees  # 제공해주신 API 연동
from common.toast import show_toast
from styles import apply_employee_style


def show_employee_management_page():
    apply_employee_style()

    if "toast_queue" in st.session_state and st.session_state.toast_queue:
        toast_data = st.session_state.toast_queue
        show_toast(toast_data["type"], toast_data["msg"])
        
        # 메시지를 한 번 띄운 후에는 반복해서 뜨지 않도록 세션에서 삭제합니다.
        del st.session_state.toast_queue

    # 삭제 확인 팝업 상태 및 선택 데이터 관리를 위한 세션 초기화
    if "show_delete_confirm" not in st.session_state:
        st.session_state.show_delete_confirm = False
    if "selected_emp_nos" not in st.session_state:
        st.session_state.selected_emp_nos = []

    # [타이틀 영역] 상단 제어 버튼 구조 정렬
    title_col, empty_col, btn_col1, btn_col2 = st.columns([2, 5.0, 1.5, 1.5])
    
    with title_col:
        st.markdown('<div class="page-title">직원 관리</div>', unsafe_allow_html=True)
        
    with btn_col1:
        # Streamlit 최신 기능인 st.dialog를 사용해 모달 팝업창을 띄웁니다.
        if st.button("직원 추가", use_container_width=True, type="primary"):
            open_registration_modal()
            
    with btn_col2:
        if st.button("선택 삭제", use_container_width=True):
            # 대시보드 그리드에서 체크된 상태값 수집 확인
            if "emp_grid_editor" in st.session_state and st.session_state.emp_grid_editor:
                selected_rows = st.session_state.emp_grid_editor.get("edited_rows", {})
                
                # 체크박스 변경사항 추적해서 True인 것만 필터링
                current_list = fetch_all_employees()
                to_delete = []
                for idx, change in selected_rows.items():
                    if change.get("선택", False):
                        to_delete.append(current_list[int(idx)]["emp_no"])
                
                if to_delete:
                    st.session_state.selected_emp_nos = to_delete
                    st.session_state.show_delete_confirm = True
                else:
                    show_toast("info", "삭제할 직원을 먼저 체크해 주세요.")
            else:
                show_toast("info", "삭제할 직원을 선택해 주세요.")

    # --------------------------------------------------------------------------------
    # ⚠️ 팝업창 2: 삭제 최종 확인 모달 블록 (화면 중단에 조건부 노출)
    # --------------------------------------------------------------------------------
    if st.session_state.show_delete_confirm:
        show_delete_confirm_dialog()

    # --------------------------------------------------------------------------------
    # [박스 1]: 직원 목록 조회 영역 (체크박스 활성화 그리드)
    # --------------------------------------------------------------------------------
    with st.container():
        st.markdown('<div class="card-content-v2">', unsafe_allow_html=True)
        st.markdown('<div class="box-section-title">■ 준법 관리 대상 사용자 목록</div>', unsafe_allow_html=True)
        
        emp_data = fetch_all_employees()
        
        if emp_data:
            df = pd.DataFrame(emp_data)
            
            # 다중 체크박스 선택 구현을 위해 가상 컬럼 추가
            df.insert(0, "선택", False)
            df.columns = ["선택", "사원번호", "사원명", "IP 주소"]
            
            # 데이터 에디터 바인딩 및 체크박스 필드만 수정 가능하도록 오픈
            st.data_editor(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "선택": st.column_config.CheckboxColumn(width="small", help="삭제할 직원을 선택하세요"),
                    "사원번호": st.column_config.Column(width="medium", disabled=True),
                    "사원명": st.column_config.Column(width="medium", disabled=True),
                    "IP 주소": st.column_config.Column(width="large", disabled=True),
                },
                key="emp_grid_editor"
            )
        else:
            st.info("등록된 관리 대상 직원이 없습니다. 신규 직원을 추가해 주세요.")
            
        st.markdown('</div>', unsafe_allow_html=True)

# =========================================================================
# 📑 팝업창 1: 직원 신규 등록 모달 함수
# =========================================================================
@st.dialog("직원 등록")
def open_registration_modal():
    st.write("새로운 준법 관리 대상 사원 정보를 입력하세요.")
    
    reg_emp_no = st.text_input("사원번호", placeholder="예: 20261002")
    reg_emp_nm = st.text_input("사원명", placeholder="예: 홍길동")
    reg_ip = st.text_input("IP 주소", placeholder="예: 10.211.X.X")
    
    st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)
    
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        if st.button("등록", type="primary", use_container_width=True):
            if not reg_emp_no.strip() or not reg_emp_nm.strip() or not reg_ip.strip():
                # 💡 직접 띄우지 않고 세션에 예약 (팝업을 유지해야 하므로 그냥 예약 후 rerun)
                st.session_state.toast_queue = {"type": "error", "msg": "모든 필드를 정확히 입력해 주세요."}
                st.rerun()
            else:
                status_code, response = add_new_employee(reg_emp_no, reg_emp_nm, reg_ip)
                if status_code in [200, 201]:
                    success_msg = response.get('message', f"{reg_emp_nm} 사원이 성공적으로 등록되었습니다.")
                    # 💡 성공 시 메인 화면에 띄우도록 세션에 저장
                    st.session_state.toast_queue = {"type": "success", "msg": success_msg}
                    st.rerun()
                else:
                    st.session_state.toast_queue = {"type": "error", "msg": f"등록 실패: {response.get('message', '통신 오류')}"}
                    st.rerun()
    with m_col2:
        if st.button("닫기", use_container_width=True):
            st.rerun()


# =========================================================================
# 📑 팝업창 2: 직원 삭제 확인 모달 함수
# =========================================================================
@st.dialog("직원 삭제 확인")
def show_delete_confirm_dialog():
    count = len(st.session_state.selected_emp_nos)
    st.write(f"선택한 {count}명의 직원을 정말 삭제하시겠습니까?")
    st.caption("삭제된 직원은 준법 TASK 대상자 목록에서 제외됩니다.")
    
    st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)
    
    d_col1, d_col2 = st.columns(2)
    with d_col1:
        if st.button("최종 확인 및 삭제", type="primary", use_container_width=True):
            status_code, response = delete_employees(st.session_state.selected_emp_nos)
            if status_code == 200:
                st.session_state.toast_queue = {"type": "success", "msg": "선택한 직원 정보가 정상적으로 삭제되었습니다."}
                st.session_state.show_delete_confirm = False
                st.session_state.selected_emp_nos = []
                st.rerun()
            else:
                st.session_state.toast_queue = {"type": "error", "msg": f"삭제 처리 실패: {response.get('message', '오류 발생')}"}
                st.rerun()
    with d_col2:
        if st.button("취소", use_container_width=True):
            st.session_state.show_delete_confirm = False
            st.session_state.selected_emp_nos = []
            st.rerun()