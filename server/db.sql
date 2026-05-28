-- ======================================================================
-- 1. 마스터 테이블 생성 (users, compliance_tasks)
-- ======================================================================

-- 준법 관리 대상 사용자 마스터 테이블
CREATE TABLE "users" (
  "user_id" varchar(50) PRIMARY KEY,
  "user_name" varchar(50) NOT NULL,
  "ip_address" varchar(45) NOT NULL,
  "is_active" boolean NOT NULL DEFAULT true,
  "created_at" timestamp NOT NULL DEFAULT (now())
);

COMMENT ON TABLE "users" IS '준법 관리 대상 사용자 마스터 테이블';
COMMENT ON COLUMN "users"."user_id" IS '사원번호 (PK)';
COMMENT ON COLUMN "users"."user_name" IS '사원이름';


-- 준법 항목 마스터 테이블
CREATE TABLE "compliance_tasks" (
  "task_id" SERIAL PRIMARY KEY,
  "title" varchar(200) NOT NULL,
  "task_type" varchar(20) NOT NULL,
  "content" jsonb,
  "recurrence_type" varchar(20) NOT NULL DEFAULT 'ONCE',
  "is_published" boolean NOT NULL DEFAULT false,
  "start_date" timestamp NOT NULL,
  "end_date" timestamp NOT NULL,
  "created_at" timestamp NOT NULL DEFAULT (now()),
  
  -- 💡 유효성 검증: ETHICS 타입일 때 content 내부에 반드시 type 필드가 포함되도록 제한
  CONSTRAINT "chk_ethics_content_format" CHECK (
    (task_type = 'ETHICS' AND content IS NOT NULL AND content ? 'type') OR 
    (task_type != 'ETHICS')
  )
);

COMMENT ON TABLE "compliance_tasks" IS '준법 항목 마스터 테이블';
COMMENT ON COLUMN "compliance_tasks"."task_id" IS '준법 항목 일련번호 (PK)';
COMMENT ON COLUMN "compliance_tasks"."title" IS '준법 공지 제목';
COMMENT ON COLUMN "compliance_tasks"."task_type" IS '준법 타입 (ETHICS, SELF_CHECK)';
COMMENT ON COLUMN "compliance_tasks"."content" IS '[API 약속] ETHICS 본문 데이터 (JSONB) - TEXT형: {"type": "TEXT", "body": "..."}, IMAGE형: {"type": "IMAGE", "url": "..."}';


-- ======================================================================
-- 2. 자식 테이블 및 로그 테이블 생성 (compliance_questions, compliance_logs)
-- ======================================================================

-- 자가점검 유형의 상세 문항 테이블
CREATE TABLE "compliance_questions" (
  "question_id" SERIAL PRIMARY KEY,
  "task_id" int NOT NULL,
  "question_text" text NOT NULL,
  "sort_order" int NOT NULL DEFAULT 1,
  "is_deleted" boolean NOT NULL DEFAULT false,
  "created_at" timestamp NOT NULL DEFAULT (now())
);

COMMENT ON TABLE "compliance_questions" IS '자가점검 유형의 상세 문항 테이블';


-- 사용자별 준법 프로그램 수행 마스터 로그
CREATE TABLE "compliance_logs" (
  "log_id" SERIAL PRIMARY KEY,
  "task_id" int NOT NULL,
  "user_id" varchar(50) NOT NULL,
  "client_ip" varchar(45) NOT NULL,
  "answers" jsonb NOT NULL,
  "completed_at" timestamp NOT NULL DEFAULT (now()),
  
  -- 💡 유효성 검증: answers 저장 시 반드시 JSON 배열([]) 형태여야 함을 보장
  CONSTRAINT "chk_answers_is_array" CHECK (jsonb_typeof(answers) = 'array')
);

COMMENT ON TABLE "compliance_logs" IS '사용자별 준법 프로그램 수행 마스터 로그';
COMMENT ON COLUMN "compliance_logs"."answers" IS '[API 약속] 사용자 응답 데이터 배열 (JSONB) - [{"q_id": 101, "txt": "질문", "ans": "Y/AGREE"}]';


-- ======================================================================
-- 3. 인덱스(Indexes) 생성
-- ======================================================================

CREATE INDEX "idx_questions_task_order" ON "compliance_questions" ("task_id", "sort_order");
CREATE INDEX "idx_logs_user_task" ON "compliance_logs" ("user_id", "task_id");
CREATE INDEX "idx_logs_completed_at" ON "compliance_logs" ("completed_at");


-- ======================================================================
-- 4. 외래키(Foreign Keys) 제약조건 설정
-- ======================================================================

ALTER TABLE "compliance_questions" ADD FOREIGN KEY ("task_id") REFERENCES "compliance_tasks" ("task_id") ON DELETE CASCADE;
ALTER TABLE "compliance_logs" ADD FOREIGN KEY ("task_id") REFERENCES "compliance_tasks" ("task_id");
ALTER TABLE "compliance_logs" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("user_id");