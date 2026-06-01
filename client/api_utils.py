import pandas as pd
import requests
import streamlit as st

# 백엔드 서버 베이스 URL (환경에 맞게 수정)

import pandas as pd
import requests
import streamlit as st

BASE_URL = "http://localhost:8080"
def fetch_log_items(task_title: str = None):
    """
    서버로부터 로그 데이터를 가져와서, 기존 대시보드 UI가 기대하는
    ['이름', '사번', 'IP', '동의여부', '동의일시'] 구조로 완벽히 매핑하여 반환합니다.
    """
    url = f"{BASE_URL}/get-all-logs"
    
    params = {}
    if task_title:
        params["task_title"] = task_title

    try:
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # 💡 [방어 코드] 서버에서 에러 메시지 딕셔너리({"error": "..."})를 리턴했거나 데이터가 비어있을 때 처리
            if not data or (isinstance(data, dict) and "error" in data):
                if isinstance(data, dict) and "error" in data:
                    st.error(f"서버 내부 오류: {data['error']}")
                return pd.DataFrame(columns=["이름", "사번", "IP", "동의여부", "동의일시"])
            
            df = pd.DataFrame(data)
            
            # 💡 [안정성 보장] 혹시 모를 키값 누락에 대비해 안전하게 필요한 컬럼만 추출
            expected_keys = ["user_name", "user_id", "client_ip", "is_completed", "completed_at"]
            for key in expected_keys:
                if key not in df.columns:
                    df[key] = None if key != "is_completed" else False
            
            # 1:1 매핑 및 컬럼명 치환
            df = df[expected_keys]
            df.columns = ["이름", "사번", "IP", "동의여부", "동의일시"]
            
            # 백엔드에서 연산된 true/false 불리언 값을 대시보드용 한글 문자열로 안전하게 변환
            df["동의여부"] = df["동의여부"].map({True: '완료', False: '미완료'}).fillna('미완료')
            
            return df[["이름", "사번", "IP", "동의여부", "동의일시"]]
        else:
            st.error(f"서버 응답 실패 (Status Code: {response.status_code})")
            return pd.DataFrame(columns=["이름", "사번", "IP", "동의여부", "동의일시"])
            
    except Exception as e:
        st.error(f"서버 연결 오류: {e}")
        return pd.DataFrame(columns=["이름", "사번", "IP", "동의여부", "동의일시"])
    
    

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