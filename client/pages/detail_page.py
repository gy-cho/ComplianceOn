import streamlit as st
from api_utils import fetch_emp_detail_answers
from styles import apply_task_management_style # 스타일 import 추가

def show_emp_detail_page():
    # 1. 스타일 적용
    apply_task_management_style()
    
    # 저장해둔 파라미터 가져오기
    params = st.session_state.get("detail_params", {})
    
    # 2. 상단 타이틀 영역 (flex 기반 한 줄 정렬)
    title_col, btn_col = st.columns([8, 2])
    with title_col:
        st.markdown('<div class="page-title">상세 답변 내역</div>', unsafe_allow_html=True)
    with btn_col:
        if st.button("목록으로"):
            st.session_state.current_page = "main"
            st.rerun()

    # 3. 사원 정보 카드 박스
    with st.container():
        st.markdown('<div class="card-content-v2">', unsafe_allow_html=True)
        st.markdown(f'<div class="box-section-title">■ {params.get("emp_nm")} ({params.get("emp_no")}) 상세 정보</div>', unsafe_allow_html=True)
        
        # API 호출
        with st.spinner("상세 데이터를 불러오는 중..."):
            detail_data = fetch_emp_detail_answers(
                params['task_id'], params['app_seq'], params['emp_no']
            )

        # 데이터 오류 처리
        if not detail_data or not isinstance(detail_data, list):
            st.error("데이터를 조회할 수 없습니다. 다시 시도해 주세요.")
            st.markdown('</div>', unsafe_allow_html=True)
            return

        # 4. 질문/답변 리스트 카드
        for idx, item in enumerate(detail_data, 1):
            ans_raw = item.get("emp_ans_yn", "미답변")
            
            # 스타일링 분기
            if ans_raw == "Y":
                ans_display = "🟢 준수 (Y)"; bg_color = "#F1F8E9"; border_color = "#4CAF50"
            elif ans_raw == "N":
                ans_display = "🔴 미준수 (N)"; bg_color = "#FFEBEE"; border_color = "#FF4B4B"
            else:
                ans_display = f"⚪ {ans_raw}"; bg_color = "#FAFAFA"; border_color = "#CCCCCC"

            st.markdown(
                f"""
                <div style="
                    background-color: {bg_color}; 
                    border: 1px solid #E0E0E0;
                    padding: 16px; 
                    border-radius: 8px; 
                    margin-bottom: 12px;
                ">
                    <div style="font-weight: 600; font-size: 14px; color: #424242; margin-bottom: 10px;">
                        Q{idx}. {item.get('qstn_cn', '질문 내용이 없습니다.')}
                    </div>
                    <div style="font-weight: 800; font-size: 15px; color: {border_color};">
                        {ans_display}
                    </div>
                </div>
                """, unsafe_allow_html=True
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
