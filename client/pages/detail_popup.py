import streamlit as st

@st.dialog("사원 상세 답변 로그", width="large")
def show_emp_detail_popup(detail_data, emp_nm, emp_no):
    """
    API에서 리턴된 문항별 답변 리스트 데이터를 팝업 형태로 랜더링하는 함수
    """
    # 👤 상단 사원 기본 정보 영역
    st.markdown(f"### 👤 {emp_nm} 사원 정보")
    st.caption(f"**사원번호:** {emp_no}")
    
    # 예외 방어 조건
    if not detail_data or not isinstance(detail_data, list):
        st.warning("조회된 상세 로그 데이터가 없거나 올바른 형식이 아닙니다.")
        return

    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

    for idx, item in enumerate(detail_data, 1):
        # API에서 내려오는 'Y' / 'N' 값 추출
        ans_raw = item.get("emp_ans_yn", "미답변")
        
        # 답변 값에 따른 UI 스타일 분기 (Y = 녹색, N = 빨간색)
        if ans_raw == "Y":
            ans_display = "🟢 준수 (Y)"
            bg_color = "#E8F5E9"  # 연한 녹색 배경
            border_color = "#4CAF50"
        elif ans_raw == "N":
            ans_display = "🔴 미준수 (N)"
            bg_color = "#FFEBEE"  # 연한 빨간색 배경
            border_color = "#FF4B4B"
        else:
            ans_display = f"⚪ {ans_raw}"
            bg_color = "#F5F5F5"
            border_color = "#CCCCCC"

        # 카드 형태로 문항과 답변 배치
        st.markdown(
            f"""
            <div style="
                background-color: {bg_color}; 
                border-left: 5px solid {border_color}; 
                padding: 15px; 
                border-radius: 4px; 
                margin-bottom: 12px;
            ">
                <div style="font-weight: bold; font-size: 14px; color: #333333; margin-bottom: 6px;">
                    Q{idx}. {item.get('qstn_cn', '질문 내용이 없습니다.')}
                </div>
                <div style="font-weight: bold; font-size: 15px; color: {border_color};">
                    {ans_display}
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

    # 🚪 하단 닫기 버튼 영역
    if st.button("닫기", use_container_width=True):
        st.rerun()  # 단순히 rerun만 하여 st.dialog 팝업을 닫습니다.