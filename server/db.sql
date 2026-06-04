-- ======================================================================
-- 1. 마스터 테이블 생성 (TB_COMP_QSTN_POOL, TB_EMP, TB_COMP_TASK)
-- ======================================================================

-- 준법질문POOL
CREATE TABLE "TB_COMP_QSTN_POOL" (
  "QSTN_CD" varchar(4) PRIMARY KEY,
  "QSTN_NM" varchar(200),
  "QSTN_TYPE" varchar(3),
  "QSTN_CN" varchar(300) NOT NULL,
  "QSTN_STD_ANS_YN" varchar(1),
  "DEL_YN" varchar(20) ,
  "REG_EMP_NO" varchar(10) ,
  "REG_DTM" timestamp DEFAULT (now()),
  "CHG_EMP_NO" varchar(10) ,
  "CHG_DTM" timestamp
);

COMMENT ON TABLE "TB_COMP_QSTN_POOL" IS '준법질문POOL';
COMMENT ON COLUMN "TB_COMP_QSTN_POOL"."QSTN_CD" IS '질문코드';
COMMENT ON COLUMN "TB_COMP_QSTN_POOL"."QSTN_NM" IS '질문명';
COMMENT ON COLUMN "TB_COMP_QSTN_POOL"."QSTN_TYPE" IS '질문종류';
COMMENT ON COLUMN "TB_COMP_QSTN_POOL"."QSTN_CN" IS '질문내용';
COMMENT ON COLUMN "TB_COMP_QSTN_POOL"."QSTN_STD_ANS_YN" IS '질문별표준답변';
COMMENT ON COLUMN "TB_COMP_QSTN_POOL"."DEL_YN" IS '삭제여부';
COMMENT ON COLUMN "TB_COMP_QSTN_POOL"."REG_EMP_NO" IS '최초등록자';
COMMENT ON COLUMN "TB_COMP_QSTN_POOL"."REG_DTM" IS '최초등록일시';
COMMENT ON COLUMN "TB_COMP_QSTN_POOL"."CHG_EMP_NO" IS '최종수정자';
COMMENT ON COLUMN "TB_COMP_QSTN_POOL"."CHG_DTM" IS '최종수정일시';


-- 준법 관리 대상 사용자 마스터 테이블
CREATE TABLE "TB_EMP" (
  "EMP_NO" varchar(10) PRIMARY KEY,
  "EMP_NM" varchar(50) NOT NULL,
  "IP" varchar(20) NOT NULL,
  "DEL_YN" varchar(20) ,
  "REG_EMP_NO" varchar(10) ,
  "REG_DTM" timestamp DEFAULT (now()),
  "CHG_EMP_NO" varchar(10) ,
  "CHG_DTM" timestamp
);

COMMENT ON TABLE "TB_EMP" IS '준법 관리 대상 사원 마스터 테이블';
COMMENT ON COLUMN "TB_EMP"."EMP_NO" IS '사원번호';
COMMENT ON COLUMN "TB_EMP"."EMP_NM" IS '사원명';
COMMENT ON COLUMN "TB_EMP"."IP" IS 'IP';
COMMENT ON COLUMN "TB_EMP"."DEL_YN" IS '삭제여부';
COMMENT ON COLUMN "TB_EMP"."REG_EMP_NO" IS '최초등록자';
COMMENT ON COLUMN "TB_EMP"."REG_DTM" IS '최초등록일시';
COMMENT ON COLUMN "TB_EMP"."CHG_EMP_NO" IS '최종수정자';
COMMENT ON COLUMN "TB_EMP"."CHG_DTM" IS '최종수정일시';


-- 준법 항목 마스터 테이블
CREATE TABLE "TB_COMP_TASK" (
  "TASK_ID" SERIAL PRIMARY KEY,
  "TASK_NM" varchar(200) NOT NULL,
  "TASK_TYPE" varchar(20),
  "TASK_CN" varchar(300),
  "IMG_FLNM" varchar(300),
  "RCRN_YN" varchar(1),
  "RCRN_CYC_CD" varchar(2),
  "PBLS_YN" varchar(1),
  "DEL_YN" varchar(20) ,
  "REG_EMP_NO" varchar(10) ,
  "REG_DTM" timestamp DEFAULT now(),
  "CHG_EMP_NO" varchar(10) ,
  "CHG_DTM" timestamp
);

COMMENT ON TABLE "TB_COMP_TASK" IS '준법 항목 마스터 테이블';
COMMENT ON COLUMN "TB_COMP_TASK"."TASK_ID" IS '타스크아이디';
COMMENT ON COLUMN "TB_COMP_TASK"."TASK_NM" IS '타스크명';
COMMENT ON COLUMN "TB_COMP_TASK"."TASK_TYPE" IS '타스크종류';
COMMENT ON COLUMN "TB_COMP_TASK"."TASK_CN" IS '타스크내용';
COMMENT ON COLUMN "TB_COMP_TASK"."IMG_FLNM" IS '이미지파일명';
COMMENT ON COLUMN "TB_COMP_TASK"."RCRN_YN" IS '반복여부';
COMMENT ON COLUMN "TB_COMP_TASK"."RCRN_CYC_CD" IS '반복주기';
COMMENT ON COLUMN "TB_COMP_TASK"."PBLS_YN" IS '게시여부';
COMMENT ON COLUMN "TB_COMP_TASK"."DEL_YN" IS '삭제여부';
COMMENT ON COLUMN "TB_COMP_TASK"."REG_EMP_NO" IS '최초등록자';
COMMENT ON COLUMN "TB_COMP_TASK"."REG_DTM" IS '최초등록일시';
COMMENT ON COLUMN "TB_COMP_TASK"."CHG_EMP_NO" IS '최종수정자';
COMMENT ON COLUMN "TB_COMP_TASK"."CHG_DTM" IS '최종수정일시';

-- ======================================================================
-- 2. 자식 테이블 및 답변 테이블 생성 (TB_COMP_TASK_APP_DT, TB_COMP_TASK_QSTN, TB_COMP_EMP_ANS)
-- ======================================================================

-- TASK 적용일
CREATE TABLE "TB_COMP_TASK_APP_DT" (
  "TASK_ID" int,
  "APP_SEQ" int,
  "TASK_APP_DT" DATE NOT NULL,
  "DEL_YN" varchar(20) ,
  "REG_EMP_NO" varchar(10) ,
  "REG_DTM" timestamp DEFAULT now(),
  "CHG_EMP_NO" varchar(10) ,
  "CHG_DTM" timestamp,

  PRIMARY KEY ("TASK_ID", "APP_SEQ")
);

COMMENT ON TABLE "TB_COMP_TASK_APP_DT" IS 'TASK 적용일';
COMMENT ON COLUMN "TB_COMP_TASK_APP_DT"."TASK_ID" IS '타스크아이디';
COMMENT ON COLUMN "TB_COMP_TASK_APP_DT"."APP_SEQ" IS '순번';
COMMENT ON COLUMN "TB_COMP_TASK_APP_DT"."TASK_APP_DT" IS '타스크적용일';
COMMENT ON COLUMN "TB_COMP_TASK_APP_DT"."DEL_YN" IS '삭제여부';
COMMENT ON COLUMN "TB_COMP_TASK_APP_DT"."REG_EMP_NO" IS '최초등록자';
COMMENT ON COLUMN "TB_COMP_TASK_APP_DT"."REG_DTM" IS '최초등록일시';
COMMENT ON COLUMN "TB_COMP_TASK_APP_DT"."CHG_EMP_NO" IS '최종수정자';
COMMENT ON COLUMN "TB_COMP_TASK_APP_DT"."CHG_DTM" IS '최종수정일시';


-- TASK별 질문
CREATE TABLE "TB_COMP_TASK_QSTN" (
  "TASK_ID" int,
  "QSTN_CD" varchar(4),
  "DEL_YN" varchar(20) ,
  "REG_EMP_NO" varchar(10) ,
  "REG_DTM" timestamp DEFAULT now(),
  "CHG_EMP_NO" varchar(10) ,
  "CHG_DTM" timestamp,
  
  PRIMARY KEY ("TASK_ID", "QSTN_CD")
);

COMMENT ON TABLE "TB_COMP_TASK_QSTN" IS 'TASK별 질문';
COMMENT ON COLUMN "TB_COMP_TASK_QSTN"."TASK_ID" IS '타스크아이디';
COMMENT ON COLUMN "TB_COMP_TASK_QSTN"."QSTN_CD" IS '질문코드';
COMMENT ON COLUMN "TB_COMP_TASK_QSTN"."DEL_YN" IS '삭제여부';
COMMENT ON COLUMN "TB_COMP_TASK_QSTN"."REG_EMP_NO" IS '최초등록자';
COMMENT ON COLUMN "TB_COMP_TASK_QSTN"."REG_DTM" IS '최초등록일시';
COMMENT ON COLUMN "TB_COMP_TASK_QSTN"."CHG_EMP_NO" IS '최종수정자';
COMMENT ON COLUMN "TB_COMP_TASK_QSTN"."CHG_DTM" IS '최종수정일시';


-- 직원별답변
CREATE TABLE "TB_COMP_EMP_ANS" (
  "EMP_NO" varchar(10) ,
  "TASK_ID" int ,
  "APP_SEQ" int ,
  "QSTN_CD" varchar(4) ,
  "ANS_DT" timestamp NOT NULL DEFAULT now(),
  "EMP_ANS_YN" varchar(1),
  "EMP_ANS_CN" varchar(200),
  "DEL_YN" varchar(20) ,
  "REG_EMP_NO" varchar(10) ,
  "REG_DTM" timestamp DEFAULT now(),
  "CHG_EMP_NO" varchar(10) ,
  "CHG_DTM" timestamp,
  
  PRIMARY KEY ("EMP_NO", "TASK_ID", "APP_SEQ", "QSTN_CD")
);

COMMENT ON TABLE "TB_COMP_EMP_ANS" IS '직원별답변';
COMMENT ON COLUMN "TB_COMP_EMP_ANS"."EMP_NO" IS '사원번호';
COMMENT ON COLUMN "TB_COMP_EMP_ANS"."TASK_ID" IS '타스크아이디';
COMMENT ON COLUMN "TB_COMP_EMP_ANS"."APP_SEQ" IS '적용순번';
COMMENT ON COLUMN "TB_COMP_EMP_ANS"."QSTN_CD" IS '질문코드';
COMMENT ON COLUMN "TB_COMP_EMP_ANS"."ANS_DT" IS '답변일시';
COMMENT ON COLUMN "TB_COMP_EMP_ANS"."EMP_ANS_YN" IS '질문별답변';
COMMENT ON COLUMN "TB_COMP_EMP_ANS"."EMP_ANS_CN" IS '질문별답변내용';
COMMENT ON COLUMN "TB_COMP_EMP_ANS"."DEL_YN" IS '삭제여부';
COMMENT ON COLUMN "TB_COMP_EMP_ANS"."REG_EMP_NO" IS '최초등록자';
COMMENT ON COLUMN "TB_COMP_EMP_ANS"."REG_DTM" IS '최초등록일시';
COMMENT ON COLUMN "TB_COMP_EMP_ANS"."CHG_EMP_NO" IS '최종수정자';
COMMENT ON COLUMN "TB_COMP_EMP_ANS"."CHG_DTM" IS '최종수정일시';


-- ======================================================================
-- 3. 인덱스(Indexes) 생성
-- ======================================================================

CREATE INDEX "IDX_TB_COMP_TASK_APP_DT_1" ON "TB_COMP_TASK_APP_DT" ("TASK_APP_DT");



