from fastapi import FastAPI, status, Query
from pydantic import BaseModel
from datetime import datetime
from fastapi.responses import JSONResponse
from typing import List, Optional
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
async def get_all_logs(task_title: str = Query(None)):
    conn = None
    cursor = None
    try:
        conn = get_pg_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if not task_title or task_title == "등록된 준법 항목이 없습니다.":
            query = """
                SELECT 
                    user_id, user_name, ip_address AS client_ip,
                    false AS is_completed, NULL AS completed_at, '선택 없음' AS task_title
                FROM users WHERE is_active = true ORDER BY user_name ASC
            """
            cursor.execute(query)
        else:
            # 💡 [핵심 해결 포인트]
            # CASE 문을 통해 항목의 주기(recurrence_type)에 따라 현재 시간(now())과의 차이를 계산합니다.
            # - DAILY: 완료일이 1일 이내여야 인정
            # - WEEKLY: 완료일이 7일 이내여야 인정
            # - MONTHLY: 완료일이 30일 이내여야 인정
            # 이 유효기간을 벗어난 과거 완료 데이터는 유저에게 재동의를 받아야 하므로 false로 판정합니다.
            query = """
                SELECT 
                    u.user_id,
                    u.user_name,
                    COALESCE(l.client_ip, u.ip_address) AS client_ip,
                    CASE 
                        WHEN l.is_completed = true AND t.recurrence_type = 'DAILY' AND l.completed_at >= now() - INTERVAL '1 day' THEN true
                        WHEN l.is_completed = true AND t.recurrence_type = 'WEEKLY' AND l.completed_at >= now() - INTERVAL '7 days' THEN true
                        WHEN l.is_completed = true AND t.recurrence_type = 'MONTHLY' AND l.completed_at >= now() - INTERVAL '30 days' THEN true
                        WHEN l.is_completed = true AND t.recurrence_type = 'ONCE' THEN true -- 단발성은 언제 했든 완료 인정
                        ELSE false
                    END AS is_completed,
                    l.completed_at,
                    t.title AS task_title
                FROM users u
                CROSS JOIN (
                    SELECT task_id, title, recurrence_type FROM compliance_tasks WHERE title = %s
                ) t
                LEFT JOIN compliance_logs l ON u.user_id = l.user_id AND t.task_id = l.task_id
                WHERE u.is_active = true
                ORDER BY u.user_name ASC
            """
            cursor.execute(query, (task_title,))
            
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        result = []
        for row in rows:
            row_dict = dict(row)
            if row_dict["completed_at"]:
                row_dict["completed_at"] = row_dict["completed_at"].strftime("%Y-%m-%d %H:%M:%S")
            else:
                row_dict["completed_at"] = "-"
            result.append(row_dict)
            
        return result
        
    except Exception as e:
        if cursor: cursor.close()
        if conn: conn.close()
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


# --- 5. 준법 항목 목록 조회 API ---
@app.get("/get-compliance-items")
async def get_compliance_items():
    conn = None
    cursor = None
    try:
        # 1. 기존 삭제 API와 동일한 방식으로 커넥션 및 커서 생성
        conn = get_pg_connection()
        cursor = conn.cursor()
        
        # 2. 약속된 마스터 테이블(compliance_tasks)에서 제목(title) 조회
        # 최근 등록된 항목이 상단에 나오도록 task_id 기준 내림차순 정렬을 추가했습니다.
        query = 'SELECT title FROM "compliance_tasks" ORDER BY "task_id" DESC'
        cursor.execute(query)
        
        # 3. 데이터 패치 및 가공
        rows = cursor.fetchall()
        
        # 데이터가 없을 경우 빈 배열 반환
        if not rows:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=[]
            )
            
        # 튜플 형태의 결과를 깔끔하게 문자열 리스트로 변환
        compliance_list = [row[0] for row in rows]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=compliance_list
        )
        
    except Exception as e:
        # 기존 예외 처리 구조와 동일하게 맞춤
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": str(e)}
        )
    finally:
        # 커넥션 누수 방지를 위한 자원 반납 구조 통일
        if cursor: cursor.close()
        if conn: conn.close()