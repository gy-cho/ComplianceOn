import pandas as pd
import requests
import streamlit as st

# 백엔드 서버 베이스 URL (환경에 맞게 수정)
BASE_URL = "http://127.0.0.1:8000"

import pandas as pd
import requests
import streamlit as st

BASE_URL = "http://127.0.0.1:8000"
def fetch_log_items(task_title: str = None):
    """
    서버로부터 로그 데이터를 가져와서, 기존 대시보드 UI가 기대하는
    ['이름', '사번', 'IP', '동의여부', '동의일시'] 구조로 완벽히 매핑하여 반환합니다.
    """
    url = f"{BASE_URL}/get-all-logs"
    
    # 💡 [변경 포인트] 선택된 준법 항목 제목이 인자로 들어오면 params 딕셔너리에 매핑합니다.
    params = {}
    if task_title:
        params["task_title"] = task_title

    try:
        # 💡 GET 요청 시 params 인자를 추가하여 서버로 파라미터를 넘겨줍니다.
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # 데이터가 없을 때 기존 대시보드가 에러 나지 않도록 기본 컬럼 정의
            if not data:
                return pd.DataFrame(columns=["이름", "사번", "IP", "동의여부", "동의일시"])
            
            df = pd.DataFrame(data)
            
            # 💡 [핵심 해결 포인트] 새로운 백엔드 응답 키값을 기존 대시보드 UI 컬럼명으로 1:1 매핑
            df = df[["user_name", "user_id", "client_ip", "is_completed", "completed_at"]]
            df.columns = ["이름", "사번", "IP", "동의여부", "동의일시"]
            
            # 기존 대시보드가 기대하는 완료/미완료 문자열 포맷으로 변환
            df["동의여부"] = df["동의여부"].map({True: '완료', False: '미완료'})
            
            return df[["이름", "사번", "IP", "동의여부", "동의일시"]]
        else:
            st.error("서버에서 데이터를 가져오지 못했습니다.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"서버 연결 오류: {e}")
        return pd.DataFrame()
    

def add_new_user(user_id, user_name, ip_address):
    """
    [변경 포인트 2] 사명 변경(user_id/user_name) 및 필수 고정 IP 주소를 파라미터에 추가하여 전송합니다.
    """
    url = f"{BASE_URL}/add-user"
    payload = {
        "user_id": user_id, 
        "user_name": user_name, 
        "ip_address": ip_address
    }
    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code, response.json()
    except Exception as e:
        return 500, {"message": str(e)}
    
    
def delete_users(user_ids: list):
    """
    선택된 사번 리스트를 서버에 전달하여 마스터 명단에서 삭제를 요청합니다.
    """
    url = f"{BASE_URL}/delete-users"
    # [변경 포인트 3] 서버의 새로운 JSON 스펙 스펙인 {"user_ids": [...]} 에 맞춤
    payload = {"user_ids": user_ids}
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code, response.json()
    except Exception as e:
        return 500, {"message": str(e)}
    


def fetch_compliance_items():
    """
    서버로부터 DB에 등록된 준법 항목(compliance_tasks)의 제목 목록을 가져옵니다.
    """
    url = f"{BASE_URL}/get-compliance-items"
    
    try:
        # GET 요청으로 서버에 등록된 준법 목록 조회
        response = requests.get(url, timeout=5)
        
        # 정상적으로 데이터를 가져왔다면 상태코드와 파싱된 JSON 리스트 반환
        return response.status_code, response.json()
    except Exception as e:
        # 기존 예시와 동일하게 예외 발생 시 500 코드와 에러 메시지 반환
        return 500, {"message": str(e)}