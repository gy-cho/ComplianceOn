import pandas as pd
import requests
import streamlit as st

# 백엔드 서버 베이스 URL (환경에 맞게 수정)
BASE_URL = "http://127.0.0.1:8000"

import pandas as pd
import requests
import streamlit as st

BASE_URL = "http://127.0.0.1:8000"

def fetch_data_from_server():
    """
    서버로부터 로그 데이터를 가져와서, 기존 대시보드 UI가 기대하는
    ['이름', '사번', 'IP', '동의여부', '동의일시'] 구조로 완벽히 매핑하여 반환합니다.
    """
    url = f"{BASE_URL}/get-all-logs"
    try:
        response = requests.get(url, timeout=5)
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