import os
import json
from fastapi import FastAPI, status
from pydantic import BaseModel, Field
from datetime import datetime
from fastapi.responses import JSONResponse
from typing import List, Optional, Any
import psycopg2
from psycopg2.extras import RealDictCursor, Json

app = FastAPI()

# --- PostgreSQL 연결 설정 ---
PG_HOST = "localhost"
PG_PORT = "5432"
PG_DB = "postgres"
PG_USER = "postgres"
PG_PASSWORD = "1234"

def get_pg_connection():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        database=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD
    )

# --- Pydantic 요청 스펙 모델 ---

# 1. 서약/점검 제출 요청 (기존 ConsentRequest 확장)
class AnswerItem(BaseModel):
    q_id: Optional[int] = None
    txt: str
    ans: str # Y, N, AGREE

class SubmitComplianceRequest(BaseModel):
    task_id: int
    user_id: str
    client_ip: str
    answers: List[AnswerItem] # JSONB 배열 스펙 자동 검증

# 2. 사용자 마스터 등록 요청
class UserAddRequest(BaseModel):
    user_id: str
    user_name: str
    ip_address: str

# 3. 사용자 마스터 다중 삭제 요청
class UserDeleteRequest(BaseModel):
    user_ids: List[str]


# --- 엔드포인트 로직 구현 ---

# 📌 1. 준법 서약/자가점검 제출 API
@app.post("/submit-compliance")
async def submit_compliance(data: SubmitComplianceRequest):
    conn = None
    cursor = None
    try:
        conn = get_pg_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # [검증 1] 유효한 점검 항목(Task)인지, 현재 게시 중(is_published)인지 확인
        cursor.execute("""
            SELECT task_id, task_type, start_date, end_date 
            FROM compliance_tasks 
            WHERE task_id = %s AND is_published = true
        """, (data.task_id,))
        task = cursor.fetchone()
        
        if not task:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"status": "error", "message": "활성화된 준법 항목을 찾을 수 없습니다."}
            )
            
        # [검증 2] 점검 기간 유효성 체크
        now = datetime.now()
        if not (task["start_date"] <= now <= task["end_date"]):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": "error", "message": "현재 점검 기간이 아닙니다."}
            )

        # [검증 3] 등록된 마스터 사용자인지 파악
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s AND is_active = true", (data.user_id,))
        if not cursor.fetchone():
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"status": "error", "message": "준법 관리 대상 사용자가 아니거나 찾을 수 없습니다."}
            )

        # [검증 4] 중복 제출 방지 (이미 기록이 존재하는지)
        cursor.execute("""
            SELECT log_id FROM compliance_logs 
            WHERE task_id = %s AND user_id = %s AND is_completed = true
        """, (data.task_id, data.user_id))
        if cursor.fetchone():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": "error", "message": "이미 제출을 완료한 항목입니다."}
            )

        # Pydantic 객체를 직렬화 가능한 딕셔너리 리스트로 변환
        answers_list = [item.model_dump() for item in data.answers]

        # [핵심] 로그 테이블에 증적 적재 (psycopg2.extras.Json 래퍼를 쓰면 jsonb 호환 완벽)
        cursor.execute("""
            INSERT INTO compliance_logs (task_id, user_id, client_ip, is_completed, answers, completed_at)
            VALUES (%s, %s, %s, true, %s, %s)
        """, (data.task_id, data.user_id, data.client_ip, Json(answers_list), now))
        
        conn.commit()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "success", "message": "준법 프로그램 수행 기록이 정상적으로 저장되었습니다."}
        )
        
    except Exception as e:
        if conn: conn.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": str(e)}
        )
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# 📌 2. 전체 서약/수행 완료 로그 조회 API (관리자 뷰어용)
@app.get("/get-all-logs")
async def get_all_logs():
    try:
        conn = get_pg_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 어떤 사원이 어떤 제목의 서약을 언제 마쳤는지 관계형 조인(JOIN) 쿼리 수행
        query = """
            SELECT 
                l.log_id,
                t.title AS task_title,
                t.task_type,
                u.user_id,
                u.user_name,
                l.client_ip,
                l.is_completed,
                l.answers,
                l.completed_at
            FROM compliance_logs l
            JOIN compliance_tasks t ON l.task_id = t.task_id
            JOIN users u ON l.user_id = u.user_id
            ORDER BY l.completed_at DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # datetime 및 jsonb 데이터를 깨지지 않게 보정
        result = []
        for row in rows:
            row_dict = dict(row)
            if row_dict["completed_at"]:
                row_dict["completed_at"] = row_dict["completed_at"].strftime("%Y-%m-%d %H:%M:%S")
            # row_dict["answers"]는 psycopg2가 내장 dict/list로 자동 파싱해 주므로 그대로 리턴 가능합니다.
            result.append(row_dict)
            
        return result
    except Exception as e:
        return {"error": str(e)}


# 📌 3. 대상 사원 추가 API (사용자 마스터 동기화)
@app.post("/add-user")
async def add_user(data: UserAddRequest):
    conn = None
    cursor = None
    try:
        conn = get_pg_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (data.user_id,))
        if cursor.fetchone():
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"status": "error", "message": "이미 등록된 사번입니다."}
            )
        
        cursor.execute("""
            INSERT INTO users (user_id, user_name, ip_address, is_active)
            VALUES (%s, %s, %s, true)
        """, (data.user_id, data.user_name, data.ip_address))
        
        conn.commit()
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"status": "success", "message": f"{data.user_name} 사원이 관리 마스터에 유입되었습니다."}
        )
    except Exception as e:
        if conn: conn.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": str(e)}
        )
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# 📌 4. 대상 사원 다중 삭제 API (인사 이동 대응용)
@app.post("/delete-users")
async def delete_users(data: UserDeleteRequest):
    conn = None
    cursor = None
    try:
        if not data.user_ids:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": "error", "message": "삭제할 사번 리스트가 누락되었습니다."}
            )

        conn = get_pg_connection()
        cursor = conn.cursor()
        
        query = "DELETE FROM users WHERE user_id IN %s"
        cursor.execute(query, (tuple(data.user_ids),))
        deleted_count = cursor.rowcount
        
        conn.commit()
        
        if deleted_count == 0:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"status": "error", "message": "삭제 대상 사용자를 찾을 수 없습니다."}
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "success", "message": f"총 {deleted_count}명의 대상자가 명단에서 제외되었습니다."}
        )
    except Exception as e:
        if conn: conn.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": str(e)}
        )
    finally:
        if cursor: cursor.close()
        if conn: conn.close()