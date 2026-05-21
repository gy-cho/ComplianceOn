import pandas as pd
import requests
import streamlit as st

def fetch_data_from_server():
    url = "http://127.0.0.1:8000/get-all-records"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if not data:
                return pd.DataFrame(columns=["이름", "사번", "PC이름", "동의여부", "동의일시"])
            
            df = pd.DataFrame(data)
            df.columns = ["이름", "사번", "PC이름", "동의여부", "동의일시"]
            df["동의여부"] = df["동의여부"].map({'Y': '완료', 'N': '미완료'})
            return df[["이름", "사번", "PC이름", "동의여부", "동의일시"]]
        else:
            st.error("서버에서 데이터를 가져오지 못했습니다.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"서버 연결 오류: {e}")
        return pd.DataFrame()

def add_new_user(emp_no, emp_name):
    url = "http://127.0.0.1:8000/add-user"
    payload = {"emp_no": emp_no, "emp_name": emp_name}
    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code, response.json()
    except Exception as e:
        return 500, {"message": str(e)}
    
    
def delete_users(emp_nos: list):
    """
    선택된 사번 리스트를 서버에 전달하여 삭제를 요청합니다.
    """
    url = "http://127.0.0.1:8000/delete-users"
    # 서버 API의 데이터 구조인 {"emp_nos": [...]}에 맞춰 payload 구성
    payload = {"emp_nos": emp_nos}
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code, response.json()
    except Exception as e:
        return 500, {"message": str(e)}