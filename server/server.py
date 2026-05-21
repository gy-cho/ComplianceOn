import os
from fastapi import FastAPI, status
from pydantic import BaseModel, Field
from datetime import datetime
from fastapi.responses import JSONResponse
from typing import List
import psycopg2
from psycopg2.extras import RealDictCursor  # SQLite의 row_factory=sqlite3.Row 같은 역할을 합니다.

app = FastAPI()

# --- PostgreSQL 연결 설정 (본인 환경에 맞게 수정) ---
PG_HOST = "localhost"
PG_PORT = "5432"
PG_DB = "postgres"
PG_USER = "postgres"
PG_PASSWORD = "1234"  # 👈 여기에 실제 비밀번호를 넣어주세요!

# DB 연결을 편하게 도와주는 헬퍼 함수
def get_pg_connection():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        database=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD
    )

class ConsentRequest(BaseModel):
    emp_no: str
    emp_name: str
    pc_name: str
    agreement_yn: str = Field(default="N")

@app.post("/submit-consent")
async def receive_consent(data: ConsentRequest):
    try:
        conn = get_pg_connection()
        # RealDictCursor를 쓰면 결과를 딕셔너리 형태로 편하게 꺼낼 수 있습니다.
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # [변경 포인트 1] ? 대신 %s 사용
        cursor.execute("SELECT agreement_yn FROM compliance_records WHERE emp_no = %s", (data.emp_no,))
        user_record = cursor.fetchone()
        
        if not user_record:
            cursor.close()
            conn.close()
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"status": "error", "message": "존재하지 않는 사용자 입니다."}
            )
        
        # [변경 포인트 2] 컬럼명으로 데이터 접근
        if user_record["agreement_yn"] == "Y":
            cursor.close()
            conn.close()
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND, # 기존 코드의 status 구조 유지
                content={"status": "error", "message": "이미 동의한 사용자 입니다."}
            )
        
        # [변경 포인트 3] 데이터 업데이트 (? ➔ %s)
        now = datetime.now() # PostgreSQL은 datetime 객체를 바로 던져도 인식합니다.
        cursor.execute("""
            UPDATE compliance_records 
            SET agreement_yn = 'Y', 
                pc_name = %s, 
                consent_time = %s
            WHERE emp_no = %s
        """, (data.pc_name, now, data.emp_no))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "success", "message": "준법서약 동의가 서버에 기록되었습니다."}
        )
    
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": str(e)}
        )

@app.get("/get-all-records")
async def get_all_records():
    try:
        conn = get_pg_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT emp_name, emp_no, pc_name, agreement_yn, consent_time FROM compliance_records ORDER BY consent_time DESC")
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # RealDictCursor 덕분에 바로 딕셔너리 리스트로 직렬화가 가능합니다.
        # 시간 데이터(datetime)의 JSON 변환 에러를 막기 위해 스트링 변환 처리를 해줍니다.
        result = []
        for row in rows:
            row_dict = dict(row)
            if row_dict["consent_time"]:
                row_dict["consent_time"] = row_dict["consent_time"].strftime("%Y-%m-%d %H:%M:%S")
            result.append(row_dict)
            
        return result
    except Exception as e:
        return {"error": str(e)}
    
class UserAddRequest(BaseModel):
    emp_no: str
    emp_name: str

@app.post("/add-user")
async def add_user(data: UserAddRequest):
    try:
        conn = get_pg_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT emp_no FROM compliance_records WHERE emp_no = %s", (data.emp_no,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"status": "error", "message": "이미 등록된 사용자 입니다."}
            )
        
        cursor.execute("""
            INSERT INTO compliance_records (emp_no, emp_name, agreement_yn)
            VALUES (%s, %s, 'N')
        """, (data.emp_no, data.emp_name))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"status": "success", "message": f"사용자 {data.emp_name}님이 등록되었습니다."}
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": str(e)}
        )

class UserDeleteRequest(BaseModel):
    emp_nos: List[str]

@app.post("/delete-users")
async def delete_users(data: UserDeleteRequest):
    try:
        if not data.emp_nos:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": "error", "message": "삭제할 사번이 선택되지 않았습니다."}
            )

        conn = get_pg_connection()
        cursor = conn.cursor()
        
        # [변경 포인트 4] PostgreSQL의 다중 IN 구문 처리 방식
        # tuple(data.emp_nos)를 사용하면 %s 한 개로 리스트 치환이 깔끔하게 됩니다.
        query = "DELETE FROM compliance_records WHERE emp_no IN %s"
        cursor.execute(query, (tuple(data.emp_nos),))
        deleted_count = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        if deleted_count == 0:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"status": "error", "message": "삭제 대상 사용자를 찾을 수 없습니다."}
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success", 
                "message": f"총 {deleted_count}명의 사용자가 삭제되었습니다."
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": str(e)}
        )