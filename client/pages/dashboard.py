import streamlit as st
import pandas as pd

from datetime import datetime
from api_utils import fetch_emp_answers, fetch_compliance_tasks
from styles import KB_YELLOW, apply_dashboard_style
from common.toast import show_toast

def show_dashboard_page():
        
    apply_dashboard_style()

    # =====================================================================
    # 💡 [신규 추가] HTML 카드(a 태그)를 클릭했을 때 넘어온 파라미터를 읽어 필터에 적용
    # =====================================================================
    if "status_click" in st.query_params:
        st.session_state.status_filter = st.query_params["status_click"]
        # 파라미터를 읽은 후 URL을 깔끔하게 유지하기 위해 삭제 (다음 동작 시 충돌 방지)
        del st.query_params["status_click"]
    # =====================================================================

    # [타이틀 영역] 상단 새로고침 버튼 레이아웃 구조 정렬
    title_col, empty_col, btn_col1 = st.columns([2, 6.3, 0.8])
    
    with title_col:
        st.markdown('<div class="page-title">현황조회</div>', unsafe_allow_html=True)
        
    with btn_col1:
        if st.button("", icon=":material/refresh:", help="새로고침", use_container_width=True):
            show_toast("success", "데이터가 새로고침 되었습니다!")
            st.rerun()

    # --------------------------------------------------------------------------------
    # [박스 1]: ■ 준법 항목 선택 영역
    # --------------------------------------------------------------------------------
    with st.container():
        st.markdown('<div class="card-content-v2">', unsafe_allow_html=True)
        
        col_sel = st.columns([1], gap="small")[0]
        
        with col_sel:
            st.markdown('<div class="box-section-title">■ 준법 항목 및 적용일 선택</div>', unsafe_allow_html=True)
            
            # 💡 [핵심] 두 셀렉트 박스를 같은 행에 나란히 배치하기 위해 내부를 2개로 분할
            inner_col1, inner_col2 = st.columns([2.5, 1], gap="small")
            
            # fetch_compliance_tasks 호출
            status_code, task_list = fetch_compliance_tasks()
            
            selected_task_id = 0
            selected_app_seq = None
            
            if status_code == 200 and isinstance(task_list, list) and len(task_list) > 0:
                task_dict = {task["task_id"]: task for task in task_list}
                
                # 💡 [첫 번째 드롭다운] 왼쪽 내부 컬럼에 배치
                with inner_col1:
                    selected_task_id = st.selectbox(
                        "준법 항목 선택",
                        options=list(task_dict.keys()),
                        format_func=lambda x: task_dict[x].get("task_nm", "이름 없음"),
                        label_visibility="collapsed"
                    )
                
                current_task = task_dict.get(selected_task_id, {})
                app_dt_list = current_task.get("task_app_dt", [])
                
                # 💡 [두 번째 드롭다운] 오른쪽 내부 컬럼에 배치
                with inner_col2:
                    if app_dt_list:
                        seq_to_date = {0: "전체"} 
                        for item in app_dt_list:
                            raw_date = item.get("task_app_dt", "")
                            clean_date = raw_date.split("T")[0] if "T" in raw_date else raw_date
                            display_text = f"{clean_date} ({item['app_seq']}회차)"
                            seq_to_date[item["app_seq"]] = display_text
                        
                        sorted_seqs = sorted(list(seq_to_date.keys()))
                        
                        selected_app_seq = st.selectbox(
                            "적용일 선택",
                            options=sorted_seqs,
                            format_func=lambda x: seq_to_date[x],
                            label_visibility="collapsed"
                        )
                    else:
                        # 해당 항목에 등록된 적용일이 없을 경우 레이아웃이 깨지지 않게 안내 메시지 노출
                        st.info("할당된 적용일 없음")
            else:
                st.info("등록된 준법 항목이 없습니다.")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # --------------------------------------------------------------------------------
    # 💡 [조회 방어 조건 및 API 호출]: 선택된 TASK와 날짜(SEQ)가 모두 있어야 API 호출
    # --------------------------------------------------------------------------------
    if selected_task_id == 0 or selected_app_seq is None:
        return  # 항목이나 날짜가 없으면 아래 대시보드 표를 그리지 않고 종료

    # 💡 핵심: api_utils.py의 fetch_emp_answers 함수에 task_id와 app_seq를 함께 전달
    df = fetch_emp_answers(task_id=selected_task_id, app_seq=selected_app_seq)
    
    if not df.empty:
        # 데이터프레임 컬럼 구조: ["사원명", "사원번호", "IP", "답변여부", "답변일시"]
        total_count = len(df)
        done_count = len(df[df["답변여부"] == "완료"])
        pending_count = len(df[df["답변여부"] == "미완료"])
        today = datetime.now().strftime('%Y-%m-%d')
        today_done = len(df[(df["답변여부"] == "완료") & (df['답변일시'].fillna('').str.contains(today, na=False))])

        if "status_filter" not in st.session_state:
            st.session_state.status_filter = "전체"

        # --------------------------------------------------------------------------------
        # [박스 2]: [대시보드 통계] 영역 (st.button 없이 순수 st.markdown a 태그 활용)
        # --------------------------------------------------------------------------------
        with st.container():
            st.markdown('<div class="card-content-v2">', unsafe_allow_html=True)
            
            m_col1, m_col2, m_col3 = st.columns(3, gap="small")
            
            # 💡 [핵심 CSS] a 태그의 기본 파란색 밑줄 디자인을 제거하고, hover 시 입체감만 부여
            hover_style = """
            <style>
                a.custom-card-link {
                    text-decoration: none !important;
                    color: inherit !important;
                    display: block !important;
                }
                .metric-card {
                    transition: transform 0.2s, box-shadow 0.2s !important;
                }
                a.custom-card-link:hover .metric-card {
                    box-shadow: 0 4px 15px rgba(0,0,0,0.15) !important;
                    transform: translateY(-3px) !important;
                }
            </style>
            """
            st.markdown(hover_style, unsafe_allow_html=True)

            with m_col1:
                # 💡 a 태그의 href="?status_click=전체" 가 버튼 역할을 대신합니다.
                st.markdown(f"""
                    <a href="?status_click=전체" target="_self" class="custom-card-link">
                        <div class="metric-container">
                            <div class="metric-card" style="width: 100%; cursor: pointer;">
                                <div class="metric-label">대상자 총원</div>
                                <div class="metric-value">{total_count} 명</div>
                                <div class="metric-sub">DB 등록 기준</div>
                            </div>
                        </div>
                    </a>
                """, unsafe_allow_html=True)

            with m_col2:
                # 💡 a 태그의 href="?status_click=완료" 가 버튼 역할을 대신합니다.
                st.markdown(f"""
                    <a href="?status_click=완료" target="_self" class="custom-card-link">
                        <div class="metric-container">
                            <div class="metric-card" style="width: 100%; cursor: pointer;">
                                <div class="metric-label">답변 완료</div>
                                <div class="metric-value" style="color: {KB_YELLOW};">{done_count} 명</div>
                                <div class="metric-sub" style="color: #4CAF50;">(오늘 +{today_done}명 완료)</div>
                            </div>
                        </div>
                    </a>
                """, unsafe_allow_html=True)

            with m_col3:
                # 💡 a 태그의 href="?status_click=미완료" 가 버튼 역할을 대신합니다.
                st.markdown(f"""
                    <a href="?status_click=미완료" target="_self" class="custom-card-link">
                        <div class="metric-container">
                            <div class="metric-card" style="width: 100%; cursor: pointer;">
                                <div class="metric-label">미답변(진행중)</div>
                                <div class="metric-value" style="color: #FF4B4B;">{pending_count} 명</div>
                                <div class="metric-sub">미답변자 {pending_count}명</div>
                            </div>
                        </div>
                    </a>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)


        # --------------------------------------------------------------------------------
        # [박스 3]: [상세 목록] 영역
        # --------------------------------------------------------------------------------
        with st.container():
            st.markdown('<div class="card-content-v2">', unsafe_allow_html=True)
            col_search, col_filter = st.columns([3.6, 1], gap="small")
            
            with col_search:
                search = st.text_input("검색", placeholder="사원명, 사원번호 입력", label_visibility="collapsed")
            with col_filter:
                # key를 지정하여 세션 상태와 Selectbox UI를 동기화
                status_filter = st.selectbox(
                    "필터", 
                    ["전체", "완료", "미완료"], 
                    key="status_filter", 
                    label_visibility="collapsed"
                )
            
            f_df = df.copy()
            
            # Selectbox의 결과값(status_filter)만으로 필터링 수행
            if status_filter != "전체":
                f_df = f_df[f_df["답변여부"] == status_filter]                
            
            if search:
                f_df = f_df[f_df['사원명'].astype(str).str.contains(search) | f_df['사원번호'].astype(str).str.contains(search)]

            st.markdown('<div style="margin-top: 10px;"></div>', unsafe_allow_html=True)
            st.data_editor(
                f_df,
                hide_index=True,
                use_container_width=True,
                column_config={
                        "사원명": st.column_config.Column(width="medium"),
                        "사원번호": st.column_config.Column(width="medium"),
                        "IP": st.column_config.Column(width="medium"),
                        "답변여부": st.column_config.Column(width="small"),
                        "답변일시": st.column_config.Column(width="medium"),
                },
                disabled=True,
                key="editor"
            )
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("선택된 준법 항목에 해당하는 답변 로그 데이터가 존재하지 않습니다.")
        