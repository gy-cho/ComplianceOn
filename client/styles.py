import streamlit as st

KB_YELLOW = "#FFBC00"

def apply_custom_css():
    st.markdown(f"""
        <style>
        [data-testid="stSidebar"] {{
            background-color: #FFFFFF !important;
            border-right: 1px solid #EEF0F5;
        }}
        [data-testid="stSidebar"] .stButton button {{
            width: 100%;
            border: none;
            text-align: left;
            background-color: transparent;
            padding: 0.6rem 1rem;
            color: #4A4A4A !important;
            font-size: 1rem;
            font-weight: 500;
            transition: all 0.2s;
        }}
        [data-testid="stSidebar"] .stButton button:hover {{
            background-color: #F8F9FB !important;
            color: {KB_YELLOW} !important;
        }}
        [data-testid="stSidebarNav"] {{
            display: none;
        }}
        
        .metric-container {{
            display: flex;
            justify-content: space-between;
            gap: 15px;
            margin-bottom: 25px;
        }}
        .metric-card {{
            flex: 1;
            background-color: #ffffff;
            padding: 20px;
            border-radius: 12px;
            border-left: 6px solid {KB_YELLOW};
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            text-align: center;
        }}
        .metric-label {{ font-size: 0.95rem; color: #666666; font-weight: 600; margin-bottom: 8px; }}
        .metric-value {{ font-size: 2rem; font-weight: 800; color: #333333; }}
        .metric-sub {{ font-size: 0.8rem; color: #999999; margin-top: 6px; }}
        </style>
        """, unsafe_allow_html=True)
    

# 2. '준비중' 페이지 전용 스타일
def get_coming_soon_style():
    st.markdown(f"""
        <style>
        [data-testid="stAppViewContainer"], 
        [data-testid="stHeader"],
        .main .block-container {{
            background-color: #EEF0F5 !important; /* 이미지와 유사한 연한 회색 */
        }}
        .coming-soon-card {{
            background-color: #ffffff;
            border-radius: 12px;
            border: 1px solid #EEF0F5; /* 그림자 대신 아주 연한 선으로 경계 구분 */
            padding: 80px 40px;
            max-width: 700px;
            margin: 40px auto; /* 상단 여백 및 중앙 정렬 */
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
        }}
        .gif-icon {{
            width: 80px;
            height: 80px;
            margin-bottom: 30px;
        }}
        .main-text {{
            font-size: 28px;
            font-weight: 700;
            color: #2D3748;
            margin-bottom: 15px;
        }}
        .sub-text {{
            font-size: 16px;
            color: #718096;
            line-height: 1.6;
        }}
        </style>
        """, unsafe_allow_html=True)


def apply_dashboard_style():
    st.markdown(f"""
        <style>
        /* 1. 전체 배경색 */
        [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
            background-color: #EEF0F5 !important;
        }}

        /* 2. 제목 스타일 */
        .page-title {{
            font-size: 26px;
            font-weight: 700;
            color: #1F2937;
            margin-bottom: 25px;
        }}
        
        /* [중요] 신규 추가: 구조적 여백 버그를 방지하는 3단 분리형 카드 디자인 */
        div[data-testid="stLayoutWrapper"]:has(> div .card-content-v2) {{
            background-color: #ffffff !important;
            border-radius: 14px !important;
            border: 1px solid #E5E7EB !important;
            padding: 20px 22px !important; /* 패딩 균형 조정 */
            margin-bottom: 12px !important; /* 각 박스간 균일한 간격 설정 */
            box-shadow: 0 4px 6px rgba(0,0,0,0.015);
        }}

        /* 각 분리형 박스 타이틀 스타일 커스텀 */
        .box-section-title {{
            font-size: 1rem;
            font-weight: 700;
            color: #2D3748;
            margin-bottom: 14px;
            margin-top: -2px; /* 상단 빈 마진 보정 */
        }}

        /* 빈 마크다운 요소 히든 처리 */
        .card-content-v2 {{
            display: none;
        }}

        .metric-container {{
            display: flex;
            justify-content: space-between;
            gap: 15px;
            padding-top: 2px !important; 
        }}

        /* 지정한 key를 가진 버튼 컴포넌트 투명화 오버레이 처리 (기존 유지) */
        div[data-element-textbox="click_all"] button,
        div[data-element-textbox="click_done"] button,
        div[data-element-textbox="click_pending"] button,
        button[key="click_all"], 
        button[key="click_done"], 
        button[key="click_pending"] {{
            position: absolute !important;
            width: 100% !important;
            height: 140px !important; 
            z-index: 10 !important;
            background-color: transparent !important;
            color: transparent !important;
            border: none !important;
            cursor: pointer !important;
        }}

        .metric-card {{
            cursor: pointer !important;
        }}
        </style>
    """, unsafe_allow_html=True)