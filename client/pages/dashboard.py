import streamlit as st
import pandas as pd
from datetime import datetime

# api_utils 및 기타 모듈 임포트
from api_utils import fetch_emp_answers, fetch_compliance_tasks, fetch_emp_detail_answers
from styles import KB_YELLOW, apply_dashboard_style
from common.toast import show_toast
from pages.detail_page import show_emp_detail_page # 상세 페이지 import

# =========================================================================
# 💡 하단 필터 상태를 변경하는 콜백 함수 (버튼 클릭 시 동작)
# =========================================================================
def update_status_filter(new_status):
    st.session_state.status_filter = new_status

def show_dashboard_page():
    # 🌟 페이지 전환을 위한 상태 초기화
    if "current_page" not in st.session_state:
        st.session_state.current_page = "main"

    # 🌟 상세 페이지로 전환 시 해당 함수 호출
    if st.session_state.current_page == "detail":
        show_emp_detail_page()
        return
        
    apply_dashboard_style()

    # 🌟 API 중복 호출 방지용 추적 필드 초기화 (최초 1회만 실행)
    if "last_logged_emp_no" not in st.session_state:
        st.session_state.last_logged_emp_no = None

    # [타이틀 영역] 상단 새로고침 버튼 레이아웃 구조 정렬
    title_col, empty_col, btn_col1 = st.columns([2, 6.3, 0.8])
    
    with title_col:
        st.markdown('<div class="page-title">현황 조회</div>', unsafe_allow_html=True)
        
    with btn_col1:
        if st.button("", icon=":material/refresh:", help="새로고침", use_container_width=True):
            show_toast("success", "데이터가 새로고침 되었습니다!")
            st.session_state.last_logged_emp_no = None
            st.rerun()

    # --------------------------------------------------------------------------------
    # [박스 1]: ■ 준법 항목 선택 영역
    # --------------------------------------------------------------------------------
    with st.container():
        st.markdown('<div class="card-content-v2">', unsafe_allow_html=True)
        col_sel = st.columns([1], gap="small")[0]
        
        with col_sel:
            st.markdown('<div class="box-section-title">■ 준법 항목 및 적용일 선택</div>', unsafe_allow_html=True)
            inner_col1, inner_col2 = st.columns([2.5, 1], gap="small")
            
            status_code, task_list = fetch_compliance_tasks()
            selected_task_id = 0
            selected_app_seq = None
            
            if status_code == 200 and isinstance(task_list, list) and len(task_list) > 0:
                task_dict = {task["task_id"]: task for task in task_list}
                
                with inner_col1:
                    selected_task_id = st.selectbox(
                        "준법 항목 선택",
                        options=list(task_dict.keys()),
                        format_func=lambda x: task_dict[x].get("task_nm", "이름 없음"),
                        label_visibility="collapsed"
                    )
                
                current_task = task_dict.get(selected_task_id, {})
                app_dt_list = current_task.get("task_app_dt", [])
                
                with inner_col2:
                    if app_dt_list:
                        seq_to_date = {0: "전체"} 
                        for item in app_dt_list:
                            raw_date = item.get("task_app_dt", "")
                            display_text = f"{raw_date} ({item['app_seq']}회차)"
                            seq_to_date[item["app_seq"]] = display_text
                        
                        sorted_seqs = sorted(list(seq_to_date.keys()))
                        selected_app_seq = st.selectbox(
                            "적용일 선택",
                            options=sorted_seqs,
                            format_func=lambda x: seq_to_date[x],
                            label_visibility="collapsed"
                        )
                    else:
                        st.info("할당된 적용일 없음")
            else:
                st.info("등록된 준법 항목이 없습니다.")
        
        st.markdown('</div>', unsafe_allow_html=True)

    if selected_task_id == 0 or selected_app_seq is None:
        return  

    current_selection_key = f"{selected_task_id}_{selected_app_seq}"
    if "prev_selection_key" not in st.session_state or st.session_state.prev_selection_key != current_selection_key:
        st.session_state.prev_selection_key = current_selection_key
        st.session_state.last_logged_emp_no = None

    raw_df = fetch_emp_answers(task_id=selected_task_id, app_seq=selected_app_seq)

    print("\n================ [가공 전 원본 API 데이터 로그] ================")
    if raw_df is not None:
        print(f"데이터 타입: {type(raw_df)} / 데이터 행 수: {len(raw_df)}")
    else:
        print("API 결과: None")
    print("=================================================================\n")
    
    if raw_df is not None and not raw_df.empty:
        total_count = len(raw_df)
        done_count = len(raw_df[raw_df["emp_main_ans_yn"].isin(["Y", True])])
        pending_count = len(raw_df[raw_df["emp_main_ans_yn"].isin(["N", False])])
        
        today = datetime.now().strftime('%Y-%m-%d')
        today_done = len(raw_df[
            (raw_df["emp_main_ans_yn"].isin(["Y", True])) & 
            (raw_df['ans_dt'].fillna('').str.contains(today, na=False))
        ])

        if "status_filter" not in st.session_state:
            st.session_state.status_filter = "전체"

        # --------------------------------------------------------------------------------
        # [박스 2]: [대시보드 통계] 영역 
        # --------------------------------------------------------------------------------
        with st.container():
            m_col1, m_col2, m_col3 = st.columns(3, gap="small")
            
            card_style = """
            <style>
                .metric-card {
                    height: 110px;
                    padding: 15px;
                    border-radius: 10px;
                    border: 1px solid #e0e0e0;
                    background-color: #ffffff;
                    box-sizing: border-box;
                    margin-bottom: 10px;
                }
            </style>
            """
            st.markdown(card_style, unsafe_allow_html=True)

            with m_col1:
                st.markdown(f"""
                    <div class="metric-card">
                        <div style="color: #666; font-size: 14px; font-weight: 600;">대상자 총원</div>
                        <div style="font-size: 24px; font-weight: bold; margin-top: 5px;">{total_count} 명</div>
                        <div style="color: #999; font-size: 12px; margin-top: 5px;">DB 등록 기준</div>
                    </div>
                """, unsafe_allow_html=True)
                st.button("전체 대상자 보기", key="click_all", use_container_width=True, on_click=update_status_filter, args=("전체",))

            with m_col2:
                st.markdown(f"""
                    <div class="metric-card">
                        <div style="color: #666; font-size: 14px; font-weight: 600;">답변 완료</div>
                        <div style="color: {KB_YELLOW}; font-size: 24px; font-weight: bold; margin-top: 5px;">{done_count} 명</div>
                        <div style="color: #4CAF50; font-size: 12px; margin-top: 5px;">(오늘 +{today_done}명 완료)</div>
                    </div>
                """, unsafe_allow_html=True)
                st.button("답변 완료자 보기", key="click_done", use_container_width=True, on_click=update_status_filter, args=("완료",))

            with m_col3:
                st.markdown(f"""
                    <div class="metric-card">
                        <div style="color: #666; font-size: 14px; font-weight: 600;">미답변(진행중)</div>
                        <div style="color: #FF4B4B; font-size: 24px; font-weight: bold; margin-top: 5px;">{pending_count} 명</div>
                        <div style="color: #999; font-size: 12px; margin-top: 5px;">미답변자 {pending_count}명</div>
                    </div>
                """, unsafe_allow_html=True)
                st.button("미답변자 보기", key="click_pending", use_container_width=True, on_click=update_status_filter, args=("미완료",))

        # --------------------------------------------------------------------------------
        # [박스 3]: [상세 목록] 영역
        # --------------------------------------------------------------------------------
        with st.container():
            st.markdown('<div class="card-content-v2">', unsafe_allow_html=True)
            col_search, col_filter = st.columns([3.6, 1], gap="small")
            
            with col_search:
                search = st.text_input("검색", placeholder="이름, 사원번호 입력", label_visibility="collapsed")
            with col_filter:
                status_filter = st.selectbox(
                    "필터", 
                    ["전체", "완료", "미완료"], 
                    key="status_filter", 
                    label_visibility="collapsed"
                )
            
            f_df = raw_df.copy()
            
            if "prev_status_filter" not in st.session_state or st.session_state.prev_status_filter != status_filter:
                st.session_state.prev_status_filter = status_filter
                st.session_state.last_logged_emp_no = None
            
            if status_filter != "전체":
                target_code = "Y" if status_filter == "완료" else "N"
                f_df = f_df[f_df["emp_main_ans_yn"].isin([target_code, True if target_code == "Y" else False])]                
            
            if search:
                f_df = f_df[
                    f_df['emp_nm'].astype(str).str.contains(search) | 
                    f_df['emp_no'].astype(str).str.contains(search)
                ]

            st.markdown('<div style="margin-top: 10px;"></div>', unsafe_allow_html=True)
            
            display_df = pd.DataFrame()
            if not f_df.empty:
                display_df["이름"] = f_df["emp_nm"].astype(str) + " (" + f_df["emp_no"].astype(str) + ")"
                task_name = f_df["task_nm"].astype(str) if "task_nm" in f_df.columns else "준법 항목"
                app_seq_val = f_df["app_seq"].astype(str) if "app_seq" in f_df.columns else "-"
                app_dt_val = f_df["task_app_dt"].astype(str) if "task_app_dt" in f_df.columns else "-"
                display_df["준법명"] = task_name + "(" + app_seq_val + "회차) - " + app_dt_val
                display_df["IP"] = f_df["ip"] if "ip" in f_df.columns else "-"
                display_df["답변여부"] = f_df["emp_main_ans_yn"].map({'Y': '완료', True: '완료', 'N': '미완료', False: '미완료'}).fillna('미완료')
                display_df["정상답변여부"] = f_df["emp_ans_agr_yn"].map({'Y': '정상', True: '정상', 'N': '비정상', False: '비정상'}).fillna('비정상')
                display_df.loc[display_df["답변여부"] != '완료', "정상답변여부"] = '-'
                display_df["답변일시"] = f_df["ans_dt"] if "ans_dt" in f_df.columns else "-"
                display_df = display_df[["이름", "준법명", "IP", "답변여부", "정상답변여부", "답변일시"]]
            else:
                display_df = pd.DataFrame(columns=["이름", "준법명", "IP", "답변여부", "정상답변여부", "답변일시"])

            st.dataframe(
                display_df,
                hide_index=True,
                use_container_width=True,
                on_select="rerun",
                key="df_selection"
            )

            selection = st.session_state.get("df_selection")
            
            if selection and "rows" in selection["selection"] and selection["selection"]["rows"]:
                selected_idx = selection["selection"]["rows"][0]
                
                if selected_idx < len(f_df):
                    target_row = f_df.iloc[selected_idx]
                    emp_no = str(target_row["emp_no"])
                    ans_yn = str(target_row["emp_main_ans_yn"]) 
                    
                    if ans_yn in ["Y", "True", True]:
                        # 🌟 페이지 전환을 위해 파라미터 저장 후 current_page 변경
                        st.session_state.detail_params = {
                            "task_id": target_row.get("task_id", selected_task_id),
                            "app_seq": target_row.get("app_seq", selected_app_seq),
                            "emp_no": emp_no,
                            "emp_nm": str(target_row.get("emp_nm", "Unknown"))
                        }
                        st.session_state.current_page = "detail"
                        st.rerun()
                    else:
                        show_toast("info", "해당 사원은 아직 답변을 완료하지 않았습니다.")
                        st.session_state.last_logged_emp_no = None
            else:
                st.session_state.last_logged_emp_no = None

            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("선택된 준법 항목에 해당하는 답변 로그 데이터가 존재하지 않습니다.")