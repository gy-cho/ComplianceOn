import pandas as pd
import requests
import streamlit as st

BASE_URL = "http://192.168.62.94:8080"
# BASE_URL = "http://127.0.0.1:8080"

def fetch_emp_answers(task_id: int = None, app_seq: int = None):
    """
    서버로부터 직원별 답변(TB_COMP_EMP_ANS) 로그 데이터를 가져와서,
    대시보드 UI용 구조인 ['사원명', '사원번호', 'IP', '답변여부', '답변일시'] 프레임으로 매핑하여 반환합니다.
    """
    url = f"{BASE_URL}/get-all-answers"
    
    params = {}
    if task_id is not None:
        params["task_id"] = task_id
    if app_seq is not None:
        params["app_seq"] = app_seq

    try:
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # [방어 코드] 서버 에러 메시지 처리 및 빈 데이터 처리
            if not data or (isinstance(data, dict) and "error" in data):
                if isinstance(data, dict) and "error" in data:
                    st.error(f"서버 내부 오류: {data['error']}")
                return pd.DataFrame(columns=["이름", "준법명", "IP", "답변여부", "정상답변여부", "답변일시"])
            
            df = pd.DataFrame(data)

            if "emp_nm" in df.columns:
                df["emp_nm"] = df["emp_nm"] + " (" + df["emp_no"].astype(str) + ")"

            if "task_nm" in df.columns:
                df["task_nm"] = df["task_nm"] + "(" + df["app_seq"].astype(str) + "회차)" + " - " + df["task_app_dt"].astype(str)
            
            # [안정성 보장] DB 테이블 컬럼 기준 매핑 키 체크 (JOIN된 사원 마스터 정보 포함 스펙 가정)
            expected_keys = ["emp_nm", "task_nm", "ip", "emp_main_ans_yn", "emp_ans_agr_yn", "ans_dt"]
            for key in expected_keys:
                if key not in df.columns:
                    df[key] = None
            
            # 필요한 컬럼만 추출 및 한글 치환
            df = df[expected_keys]
            df.columns = ["이름", "준법명", "IP", "답변여부", "정상답변여부", "답변일시"]
            
            # 'Y'/'N' 혹은 True/False 값에 관계없이 안전하게 대시보드용 한글 문자열로 변환
            df["답변여부"] = df["답변여부"].map({'Y': '완료', True: '완료', 'N': '미완료', False: '미완료'}).fillna('미완료')
            
            df["정상답변여부"] = df["정상답변여부"].map({'Y': '정상', True: '정상', 'N': '비정상', False: '비정상'}).fillna('비정상')
            df.loc[df["답변여부"] != '완료', "정상답변여부"] = '-'
            
            return df
        else:
            st.error(f"서버 응답 실패 (Status Code: {response.status_code})")
            return pd.DataFrame(columns=["이름", "준법명", "IP", "답변여부", "정상답변여부", "답변일시"])
            
    except Exception as e:
        st.error(f"서버 연결 오류: {e}")
        return pd.DataFrame(columns=["이름", "준법명", "IP", "답변여부", "정상답변여부", "답변일시"])


# employee_management.py 내부 통신 스크립트가 정상 동작합니다.
def fetch_all_employees():
    url = f"{BASE_URL}/get-all-employees"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()  # 자바에서 던져준 배열이 그대로 들어옵니다.
        return []
    except Exception:
        return []

def add_new_employee(emp_no: str, emp_nm: str, ip: str):
    """
    준법 관리 대상 사용자 테이블(TB_EMP)에 새로운 사원을 추가합니다.
    """
    url = f"{BASE_URL}/add-employee"
    payload = {
        "emp_no": emp_no, 
        "emp_nm": emp_nm, 
        "ip": ip
    }
    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code, response.json()
    except Exception as e:
        return 500, {"message": str(e)}
    
    
def delete_employees(emp_nos: list):
    """
    선택된 사원번호(EMP_NO) 리스트를 서버에 전달하여 TB_EMP 테이블에서 삭제(또는 DEL_YN='Y' 처리)를 요청합니다.
    """
    url = f"{BASE_URL}/delete-employees"
    payload = {"emp_nos": emp_nos}
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code, response.json()
    except Exception as e:
        return 500, {"message": str(e)}
    

def fetch_compliance_tasks():
    """서버로부터 준법 항목 마스터 테이블의 태스크 목록을 가져옵니다."""
    url = f"{BASE_URL}/get-compliance-tasks"
    try:
        response = requests.get(url, timeout=5)
        return response.status_code, response.json()
    except Exception as e:
        return 500, {"message": str(e)}

def fetch_question_pool():
    """TB_COMP_QSTN_POOL 마스터 테이블에서 질문 리스트를 가져옵니다."""
    url = f"{BASE_URL}/get-question-pool"
    try:
        response = requests.get(url, timeout=5)
        return response.status_code, response.json()
    except Exception as e:
        return 500, []

def fetch_task_questions(task_id):
    """특정 TASK ID에 링크 맵핑된 질문 코드 리스트를 배열로 가져옵니다."""
    url = f"{BASE_URL}/get-task-questions?taskId={task_id}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

def create_compliance_task(payload):
    """새로운 준법 통제 TASK 항목을 데이터베이스에 적재 요청합니다."""
    url = f"{BASE_URL}/create-compliance-task"
    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code
    except Exception:
        return 500

def update_compliance_task(payload):
    """기존 준법 마스터 정보 데이터를 변경 수정 반영합니다."""
    url = f"{BASE_URL}/update-compliance-task"
    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code
    except Exception:
        return 500

def delete_compliance_task(task_id):
    """지정한 준법 관리 TASK를 논리(소프트) 삭제 처리합니다."""
    url = f"{BASE_URL}/delete-compliance-task?taskId={task_id}"
    try:
        response = requests.post(url, timeout=5)
        return response.status_code
    except Exception:
        return 500
    

def fetch_all_used_dates():
    """타 TASK에서 이미 점유 중인 적용일 목록을 반환합니다."""
    try:
        response = requests.get(f"{BASE_URL}/get-all-used-dates", timeout=5)
        return response.json() if response.status_code == 200 else []
    except Exception:
        return []

def fetch_task_dates(task_id):
    """해당 TASK에 등록된 적용일 리스트를 조회합니다."""
    try:
        response = requests.get(f"{BASE_URL}/get-task-dates?taskId={task_id}", timeout=5)
        return response.json() if response.status_code == 200 else []
    except Exception:
        return []
    
def fetch_task_images():
    """서버로부터 TASK에 등록된 이미지 파일들의 URL 리스트를 가져옵니다."""
    try:
        response = requests.get(f"{BASE_URL}/get-img-pool", timeout=5)
        return response.json() if response.status_code == 200 else []
    except Exception:
        return []