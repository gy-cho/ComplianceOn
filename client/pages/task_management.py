import streamlit as st
import pandas as pd
from datetime import datetime, date
from api_utils import (
    fetch_compliance_tasks, 
    fetch_question_pool, 
    fetch_task_questions,
    create_compliance_task,
    update_compliance_task,
    delete_compliance_task,
    fetch_all_used_dates,
    fetch_task_dates
)
from styles import KB_YELLOW, apply_task_management_style
from common.toast import show_toast

def show_task_management_page():
    apply_task_management_style()

    # 내부 상태 초기화
    if "task_page_mode" not in st.session_state:
        st.session_state.task_page_mode = "list"
    if "selected_task_data" not in st.session_state:
        st.session_state.selected_task_data = None

    selectData = [ {"id": "ETHICS", "name": "윤리강령"}, {"id": "SELF_CHECK", "name": "자가점검"} ]
        
    # 날짜 다중 선택용 가상 임시 바구니 세션
    if "temp_app_dates" not in st.session_state:
        st.session_state.temp_app_dates = []

    # =========================================================================
    # 1. TASK 목록 화면
    # =========================================================================
    if st.session_state.task_page_mode == "list":
        title_col, empty_col, btn_col = st.columns([2, 6.3, 0.8])
        with title_col:
            st.markdown('<div class="page-title">준법 TASK 목록</div>', unsafe_allow_html=True)
        with btn_col:
            if st.button("등록", use_container_width=True, type="primary"):
                st.session_state.temp_app_dates = []  
                st.session_state.task_page_mode = "create"
                st.rerun()

        with st.container():
            st.markdown('<div class="card-content-v2">', unsafe_allow_html=True)
            st.markdown('<div class="box-section-title">■ 등록된 준법 TASK 현황 목록</div>', unsafe_allow_html=True)
            
            status_code, task_list = fetch_compliance_tasks()
            
            if status_code == 200 and isinstance(task_list, list) and len(task_list) > 0:
                df = pd.DataFrame(task_list)
                df_view = df[["task_id", "task_nm", "task_type", "rcrn_yn", "pbls_yn"]].copy()
                df_view.columns = ["TASK ID", "TASK명", "유형", "반복여부", "게시여부"]
                
                # 💡 추가: 출력용 데이터프레임에서만 ETHICS를 윤리강령으로 치환
                df_view["유형"] = df_view["유형"].replace({"ETHICS": "윤리강령"})
                df_view["유형"] = df_view["유형"].replace({"SELF_CHECK": "자가점검"})

                event = st.dataframe(
                    df_view, use_container_width=True, hide_index=True,
                    on_select="rerun", selection_mode="single-row",
                    column_order=["TASK명", "유형", "반복여부", "게시여부"]
                )
                
                if event.selection and len(event.selection.rows) > 0:
                    selected_row_idx = event.selection.rows[0]
                    target_task = task_list[selected_row_idx]
                    st.session_state.selected_task_data = target_task
                    
                    db_dates = fetch_task_dates(target_task.get("task_id"))
                    st.session_state.temp_app_dates = [d["task_app_dt"] for d in db_dates]
                    
                    st.session_state.task_page_mode = "detail"
                    st.rerun()
            else:
                st.info("등록된 준법 관리 TASK 항목이 존재하지 않습니다.")
            st.markdown('</div>', unsafe_allow_html=True)

    # =========================================================================
    # 2. TASK 등록 화면
    # =========================================================================
    elif st.session_state.task_page_mode == "create":
        st.markdown('<div class="page-title">새 준법 TASK 등록</div>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="card-content-v2">', unsafe_allow_html=True)
            st.markdown('<div class="box-section-title">■ 기본 정보 및 정책 설정</div>', unsafe_allow_html=True)
            
            task_nm = st.text_input("TASK 명", placeholder="예: 2026년 하반기 정보보안 서약 관리")
            
            c_col1, c_col2, c_col3 = st.columns(3)

            with c_col1:
                task_type = st.selectbox(
                    "TASK 유형 선택", 
                    ["ETHICS", "SELF_CHECK"],
                    format_func=lambda x: next((item["name"] for item in selectData if item["id"] == x), x)
                )
            with c_col2:
                rcrn_yn = st.radio("정기 반복 여부", ["N", "Y"], horizontal=True)
            with c_col3:
                pbls_yn = st.radio("즉시 게시 여부", ["Y", "N"], horizontal=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="card-content-v2">', unsafe_allow_html=True)
            st.markdown('<div class="box-section-title">■ TASK 적용일 설정</div>', unsafe_allow_html=True)
            
            used_dates = fetch_all_used_dates()
            if used_dates:
                formatted_used_dates = ", ".join([f"`{d}`" for d in sorted(used_dates)])
                st.warning(f"⚠️ **선택 불가 안내**: 다음 날짜들은 이미 다른 TASK에서 사용 중이므로 지정할 수 없습니다.\n> {formatted_used_dates}")
            else:
                st.caption("TASK를 대상 PC에 배포하거나 강제 노출할 날짜들을 추가하세요. (과거 날짜 제외)")
            
            date_in_col, date_btn_col = st.columns([8, 2])
            with date_in_col:
                picked_date = st.date_input("적용일 추가 선택", min_value=date.today(), label_visibility="collapsed")
            with date_btn_col:
                if st.button("날짜 추가", use_container_width=True):
                    str_date = picked_date.strftime("%Y-%m-%d")
                    if str_date in used_dates:
                        show_toast("error", "이미 다른 TASK에서 사용 중인 날짜입니다.")
                    elif str_date in st.session_state.temp_app_dates:
                        show_toast("warning", "이미 현재 목록에 추가된 날짜입니다.")
                    else:
                        st.session_state.temp_app_dates.append(str_date)
                        st.rerun()
            
            if st.session_state.temp_app_dates:
                dt_df = pd.DataFrame({"선택된 적용일": st.session_state.temp_app_dates})
                dt_df.insert(0, "삭제", False)
                edited_dt_df = st.data_editor(
                    dt_df, use_container_width=True, hide_index=True,
                    column_config={"삭제": st.column_config.CheckboxColumn(width="small")}
                )
                del_indices = edited_dt_df[edited_dt_df["삭제"] == True].index
                if len(del_indices) > 0:
                    st.session_state.temp_app_dates = [v for i, v in enumerate(st.session_state.temp_app_dates) if i not in del_indices]
                    st.rerun()
            else:
                st.info("선택된 적용일이 없습니다. 날짜를 추가해 주세요.")
            st.markdown('</div>', unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="card-content-v2">', unsafe_allow_html=True)
            st.markdown('<div class="box-section-title">■ 상세 본문 및 문항 매핑 설정</div>', unsafe_allow_html=True)
            
            task_cn = ""
            selected_qstn_cds = []
            if task_type == "ETHICS":
                task_cn = st.text_area("서약 내용", placeholder="임직원 강제 팝업용 서약 문구를 입력하세요.", height=180)
            elif task_type == "SELF_CHECK":
                _, pool_data = fetch_question_pool()
                options = [f"[{q['qstn_cd']}] {q['qstn_nm']} - {q['qstn_cn']}" for q in pool_data]
                selected_options = st.multiselect("점검 문항 선택", options=options)
                selected_qstn_cds = [opt.split(']')[0].replace('[', '') for opt in selected_options]
            st.markdown('</div>', unsafe_allow_html=True)

        # 💡 [등록 화면 하단 제어 바] st.error 제거하고 show_toast로 변경 완료
        ctrl_col1, ctrl_col2, ctrl_space = st.columns([1.5, 1.5, 7])
        with ctrl_col1:
            if st.button("등록", type="primary", use_container_width=True):
                if not task_nm.strip():
                    show_toast("error", "TASK 명을 입력해 주세요.")
                elif not st.session_state.temp_app_dates:
                    show_toast("error", "최소 1개 이상의 적용 날짜를 추가하셔야 합니다.")
                elif task_type == "ETHICS" and not task_cn.strip():
                    show_toast("error", "서약 본문 내용을 입력해 주세요.")
                elif task_type == "SELF_CHECK" and not selected_qstn_cds:
                    show_toast("error", "최소 1개 이상의 질문 문항을 매핑해야 합니다.")
                else:
                    payload = {
                        "task_nm": task_nm, "task_type": task_type,
                        "task_cn": task_cn if task_type == "ETHICS" else None,
                        "rcrn_yn": rcrn_yn, "pbls_yn": pbls_yn,
                        "selected_qstn_cds": selected_qstn_cds if task_type == "SELF_CHECK" else [],
                        "app_dates": st.session_state.temp_app_dates
                    }
                    if create_compliance_task(payload) == 200:
                        show_toast("success", "새로운 준법 제어 TASK가 DB에 등록되었습니다.")
                        st.session_state.task_page_mode = "list"
                        st.rerun()
                    else:
                        show_toast("error", "서버 저장 처리 중 통신 오류가 발생했습니다.")
        with ctrl_col2:
            if st.button("취소", use_container_width=True):
                st.session_state.task_page_mode = "list"
                st.rerun()

    # =========================================================================
    # 3. TASK 상세 및 편집 화면
    # =========================================================================
    elif st.session_state.task_page_mode == "detail":
        task_info = st.session_state.selected_task_data
        st.markdown('<div class="page-title">준법 TASK 상세 정보 수정</div>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="card-content-v2">', unsafe_allow_html=True)
            st.markdown('<div class="box-section-title">■ 기본 정보 및 정책 설정</div>', unsafe_allow_html=True)
            edit_nm = st.text_input("TASK 명", value=task_info.get("task_nm"))
            
            d_col1, d_col2, d_col3 = st.columns(3)
            with d_col1:
                current_type = task_info.get("task_type")
                display_type = next((item["name"] for item in selectData if item["id"] == current_type), current_type)
                st.text_input("TASK 유형", value=display_type, disabled=True)
            with d_col2:
                current_type = task_info.get("task_type")
                display_type = next((item["name"] for item in selectData if item["id"] == current_type), current_type)
                st.text_input("정기 반복 여부", value=task_info.get("rcrn_yn", "N"), disabled=True)
            with d_col3:
                edit_pbls = st.radio("게시 상태 전환", ["Y", "N"], index=0 if task_info.get("pbls_yn") == "Y" else 1, horizontal=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="card-content-v2">', unsafe_allow_html=True)
            st.markdown('<div class="box-section-title">■ TASK 적용일 편집</div>', unsafe_allow_html=True)
            
            used_dates = fetch_all_used_dates()
            other_used_dates = [d for d in used_dates if d not in st.session_state.temp_app_dates]
            
            if other_used_dates:
                formatted_other_dates = ", ".join([f"`{d}`" for d in sorted(other_used_dates)])
                st.warning(f"⚠️ **선택 불가 안내**: 다음 날짜들은 이미 다른 TASK에서 사용 중이므로 지정할 수 없습니다.\n> {formatted_other_dates}")
            else:
                st.caption("TASK 적용 날짜 관리 (추가 등록 또는 체크 해제를 통한 삭제 처리가 가능합니다)")
            
            u_date_in, u_date_btn = st.columns([8, 2])
            with u_date_in:
                edit_picked_date = st.date_input("추가 적용일 선택", min_value=date.today(), label_visibility="collapsed")
            with u_date_btn:
                if st.button("날짜 추가", key="edit_date_add_btn", use_container_width=True):
                    str_ed_date = edit_picked_date.strftime("%Y-%m-%d")
                    if str_ed_date in other_used_dates:
                        show_toast("error", "이미 다 TASK에서 사용 중인 날짜입니다.")
                    elif str_ed_date in st.session_state.temp_app_dates:
                        show_toast("warning", "이미 현재 목록에 추가된 날짜입니다.")
                    else:
                        st.session_state.temp_app_dates.append(str_ed_date)
                        st.rerun()
            
            if st.session_state.temp_app_dates:
                edit_dt_df = pd.DataFrame({"선택된 적용일": st.session_state.temp_app_dates})
                edit_dt_df.insert(0, "삭제", False)
                edited_grid = st.data_editor(
                    edit_dt_df, use_container_width=True, hide_index=True,
                    column_config={"삭제": st.column_config.CheckboxColumn(width="small")},
                    key="edit_date_grid_editor"
                )
                del_ed_indices = edited_grid[edited_grid["삭제"] == True].index
                if len(del_ed_indices) > 0:
                    st.session_state.temp_app_dates = [v for i, v in enumerate(st.session_state.temp_app_dates) if i not in del_ed_indices]
                    st.rerun()
            else:
                st.info("할당된 적용일이 없습니다. 날짜를 할당해 주세요.")
            st.markdown('</div>', unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="card-content-v2">', unsafe_allow_html=True)
            st.markdown('<div class="box-section-title">■ 상세 본문 및 문항 매핑 현황</div>', unsafe_allow_html=True)
            if task_info.get("task_type") == "ETHICS":
                edit_cn = st.text_area("서약 내용", value=task_info.get("task_cn", ""), height=180)
            elif task_info.get("task_type") == "SELF_CHECK":
                st.caption("본 준법 자가점검 TASK에 포함되어 있는 질문 문항 목록입니다.")
                mapped_cds = fetch_task_questions(task_info.get("task_id"))
                if mapped_cds:
                    _, pool_data = fetch_question_pool()
                    pool_df = pd.DataFrame(pool_data)
                    if not pool_df.empty:
                        selected_qstns_df = pool_df[pool_df["qstn_cd"].isin(mapped_cds)].copy()
                        selected_qstns_df.columns = ["질문 코드", "질문명", "질문 상세 내용"]
                        st.dataframe(selected_qstns_df, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # 💡 [상세 화면 하단 제어 바] st.error 제거하고 show_toast로 변경 완료
        b_col1, b_col2, b_col3, b_space = st.columns([1.5, 1.5, 1.5, 5.5])
        with b_col1:
            if st.button("저장", type="primary", use_container_width=True):
                if not st.session_state.temp_app_dates:
                    show_toast("error", "최소 하나 이상의 적용 날짜가 유지되어야 합니다.")
                elif not edit_nm.strip():
                    show_toast("error", "TASK 명은 비워둘 수 없습니다.")
                elif task_info.get("task_type") == "ETHICS" and not edit_cn.strip():
                    show_toast("error", "서약 본문 내용은 비워둘 수 없습니다.")
                else:
                    payload = {
                        "task_id": int(task_info.get("task_id")),
                        "task_nm": edit_nm,
                        "pbls_yn": edit_pbls,
                        "task_cn": edit_cn if task_info.get("task_type") == "ETHICS" else None,
                        "app_dates": st.session_state.temp_app_dates
                    }
                    if update_compliance_task(payload) == 200:
                        show_toast("success", "준법 제어 변경사항이 갱신되었습니다.")
                        st.session_state.task_page_mode = "list"
                        st.rerun()
                    else:
                        show_toast("error", "수정 요청 처리 중 에러가 발생했습니다.")
        with b_col2:
            if st.button("삭제", use_container_width=True):
                if delete_compliance_task(task_info.get("task_id")) == 200:
                    show_toast("success", "해당 관리 TASK가 삭제되었습니다.")
                    st.session_state.task_page_mode = "list"
                    st.rerun()
                else:
                    show_toast("error", "삭제 요청 처리 중 에러가 발생했습니다.")
        with b_col3:
            if st.button("목록으로", use_container_width=True):
                st.session_state.task_page_mode = "list"
                st.rerun()