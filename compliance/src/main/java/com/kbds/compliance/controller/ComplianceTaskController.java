package com.kbds.compliance.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.util.*;

/**
 * 📌 준법 TASK(TB_COMP_TASK) 관리 관련 API
 *  - TASK 목록/질문풀/적용일 조회, TASK 등록/수정/삭제
 *  - 기존 ComplianceController 에서 분리된 부분
 */
@RestController
@RequiredArgsConstructor
public class ComplianceTaskController {

    private final NamedParameterJdbcTemplate jdbcTemplate;

    // 📌 준법 항목 목록 상세 조회 API (전체 필드 포함)
    @GetMapping("/get-compliance-tasks")
    public ResponseEntity<?> getComplianceTasks() {
        try {
            
            String query = "SELECT TASK_ID AS task_id, TASK_NM AS task_nm, TASK_TYPE AS task_type, " +
                           "TASK_CN AS task_cn, IMG_FLNM as img_flnm, RCRN_YN AS rcrn_yn, PBLS_YN AS pbls_yn " +
                           "FROM TB_COMP_TASK WHERE DEL_YN = 'N' ORDER BY TASK_ID DESC";

            List<Map<String, Object>> taskList = jdbcTemplate.queryForList(query, new MapSqlParameterSource());

            query = " SELECT TASK.TASK_ID AS task_id "+
                            " , CTAD.APP_SEQ AS app_seq "+
                            " , TO_CHAR(CTAD.TASK_APP_DT, 'YYYY-MM-DD') AS task_app_dt "+
                        " FROM TB_COMP_TASK TASK, TB_COMP_TASK_APP_DT CTAD "+
                        " WHERE TASK.DEL_YN = 'N' "+ 
                        " AND TASK.TASK_ID = CTAD.TASK_ID "+
                        " AND (CTAD.DEL_YN = 'N' or CTAD.DEL_YN is null ) "+
                        " ORDER BY TASK.TASK_ID, CTAD.TASK_APP_DT ";
            List<Map<String, Object>> taskListAppDate = jdbcTemplate.queryForList(query, new MapSqlParameterSource());

            for (Map<String, Object> task : taskList) {
                int task_id = (Integer) task.get("task_id");
                List<Map<String, Object>> appDateList = new ArrayList<>();
                for (Map<String, Object> appDate : taskListAppDate) {
                    
                    int app_dt_task_id = (Integer) appDate.get("task_id");
                    if ( task_id == app_dt_task_id ) {
                        appDateList.add(appDate);
                    }

                }
                task.put("task_app_dt",appDateList);
            }
            return ResponseEntity.ok(taskList);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", e.getMessage()));
        }
    }

    // 📌 자가점검 질문 풀(POOL) 조회 API
    @GetMapping("/get-question-pool")
    public ResponseEntity<?> getQuestionPool() {
        try {
            String query = "SELECT QSTN_CD AS qstn_cd, QSTN_NM AS qstn_nm, QSTN_CN AS qstn_cn " +
                           "FROM TB_COMP_QSTN_POOL WHERE DEL_YN = 'N' ORDER BY QSTN_CD ASC";
            List<Map<String, Object>> qstnPool = jdbcTemplate.queryForList(query, new MapSqlParameterSource());
            return ResponseEntity.ok(qstnPool);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", e.getMessage()));
        }
    }

    // 📌 특정 TASK에 매핑된 질문 코드 목록 조회 API
    @GetMapping("/get-task-questions")
    public ResponseEntity<?> getTaskQuestions(@RequestParam("taskId") int taskId) {
        try {
            String query = "SELECT QSTN_CD AS qstn_cd FROM TB_COMP_TASK_QSTN WHERE TASK_ID = :taskId AND DEL_YN = 'N'";
            MapSqlParameterSource params = new MapSqlParameterSource("taskId", taskId);
            List<Map<String, Object>> rows = jdbcTemplate.queryForList(query, params);
            
            List<String> qstnCodes = new ArrayList<>();
            for (Map<String, Object> row : rows) {
                qstnCodes.add((String) row.get("qstn_cd"));
            }
            return ResponseEntity.ok(qstnCodes);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", e.getMessage()));
        }
    }

    // 📌 사용중인 날짜 조회 API
    @GetMapping("/get-all-used-dates")
    public ResponseEntity<?> getAllUsedDates(
            @RequestParam(value = "exclude_task_id", required = false) Integer excludeTaskId) {
        try {
            String query;
            MapSqlParameterSource params = new MapSqlParameterSource();

            if (excludeTaskId != null) {
                // 편집 모드: 자기 자신의 TASK 날짜는 제외
                query = "SELECT DISTINCT TO_CHAR(TASK_APP_DT, 'YYYY-MM-DD') AS app_dt " +
                        "FROM TB_COMP_TASK_APP_DT " +
                        "WHERE DEL_YN = 'N' AND TASK_APP_DT >= CURRENT_DATE " +
                        "AND TASK_ID != :excludeTaskId";
                params.addValue("excludeTaskId", excludeTaskId);
            } else {
                // 신규 등록 모드: 전체 사용 중인 날짜 반환
                query = "SELECT DISTINCT TO_CHAR(TASK_APP_DT, 'YYYY-MM-DD') AS app_dt " +
                        "FROM TB_COMP_TASK_APP_DT " +
                        "WHERE DEL_YN = 'N' AND TASK_APP_DT >= CURRENT_DATE";
            }

            List<Map<String, Object>> rows = jdbcTemplate.queryForList(query, params);
            List<String> dates = rows.stream().map(r -> (String) r.get("app_dt")).toList();
            return ResponseEntity.ok(dates);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", e.getMessage()));
        }
    }

    // 📌 특정 TASK에 등록된 적용일 목록 조회 API
    @GetMapping("/get-task-dates")
    public ResponseEntity<?> getTaskDates(@RequestParam("taskId") int taskId) {
        try {
            String query = "SELECT APP_SEQ AS app_seq, TO_CHAR(TASK_APP_DT, 'YYYY-MM-DD') AS task_app_dt " +
                           "FROM TB_COMP_TASK_APP_DT " +
                           "WHERE TASK_ID = :taskId AND DEL_YN = 'N' " +
                           "ORDER BY APP_SEQ ASC";
            List<Map<String, Object>> dates = jdbcTemplate.queryForList(query, new MapSqlParameterSource("taskId", taskId));
            return ResponseEntity.ok(dates);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", e.getMessage()));
        }
    }

    // 📌 신규 준법 TASK 등록 API (적용일 Multi Row insert 반영)
    @PostMapping("/create-compliance-task")
    @Transactional
    public ResponseEntity<?> createComplianceTask(@RequestBody Map<String, Object> payload) {
        try {
            System.out.println("=============== payload create ================");
            System.out.println(payload);

            
            // 1. 마스터 Insert
            String taskQuery = "INSERT INTO TB_COMP_TASK (TASK_NM, TASK_TYPE, TASK_CN, IMG_FLNM, RCRN_YN, PBLS_YN, DEL_YN, REG_EMP_NO) " +
                               "VALUES (:task_nm, :task_type, :task_cn, :img_flnm, :rcrn_yn, :pbls_yn, 'N', :emp_no) RETURNING TASK_ID";
            
            int taskId = jdbcTemplate.queryForObject(taskQuery, new MapSqlParameterSource(payload), Integer.class);
            String emp_no = (String) payload.get("emp_no");
            
            // 2. 질문 매핑 (기존 로직 유지)
            if ("SELF_CHECK".equals(payload.get("task_type")) && payload.get("selected_qstn_cds") != null) {
                List<String> selected_qstn_cds = (List<String>) payload.get("selected_qstn_cds");
                if (!selected_qstn_cds.isEmpty()) {
                    String qstnQuery = "INSERT INTO TB_COMP_TASK_QSTN (TASK_ID, QSTN_CD, DEL_YN, REG_EMP_NO) " +
                                     "VALUES (:taskId, :selected_qstn_cds, 'N', :empNo)";
                    List<Map<String, Object>> batchValues = new ArrayList<>();
                    for (String selectedQstnCd : selected_qstn_cds) {
                        batchValues.add(Map.of("taskId", taskId, "selected_qstn_cds", selectedQstnCd, "empNo", emp_no));
                    }
                    jdbcTemplate.batchUpdate(qstnQuery, batchValues.toArray(new Map[0]));
                }
            }

            // 3. 다중 적용일 등록 (APP_SEQ는 1부터 순차 생성)
            if (payload.get("app_dates") != null) {
                List<String> appDates = (List<String>) payload.get("app_dates");
                if (!appDates.isEmpty()) {
                    String dtQuery = "INSERT INTO TB_COMP_TASK_APP_DT (TASK_ID, APP_SEQ, TASK_APP_DT, DEL_YN, REG_EMP_NO) " +
                                     "VALUES (:taskId, :appSeq, TO_DATE(:appDt, 'YYYY-MM-DD'), 'N', :empNo)";
                    List<Map<String, Object>> batchValues = new ArrayList<>();
                    int seq = 1;
                    for (String dt : appDates) {
                        batchValues.add(Map.of("taskId", taskId, "appSeq", seq++, "appDt", dt, "empNo", emp_no));
                    }
                    jdbcTemplate.batchUpdate(dtQuery, batchValues.toArray(new Map[0]));
                }
            }
            return ResponseEntity.ok(Map.of("status", "success"));
        } catch (Exception e) {
            throw e;
            //return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", e.getMessage()));
        }
    }

    // 📌 기존 TASK 수정 및 날짜 갱신 API
    @PostMapping("/update-compliance-task")
    @Transactional
    public ResponseEntity<?> updateComplianceTask(@RequestBody Map<String, Object> payload) {
        try {
            System.out.println("=============== payload update ================");
            System.out.println(payload);

            int task_id = (Integer) payload.get("task_id");
            String emp_no = (String) payload.get("emp_no");

            // 1. 마스터 업데이트
            String updateQuery = "UPDATE TB_COMP_TASK SET TASK_NM = :task_nm, IMG_FLNM = :img_flnm, PBLS_YN = :pbls_yn, " +
                                "TASK_CN = :task_cn, CHG_DTM = now(), CHG_EMP_NO = :emp_no WHERE TASK_ID = :task_id";
            jdbcTemplate.update(updateQuery, new MapSqlParameterSource(payload));

            // 2. 적용일 MERGE 처리 (DELETE 후 재등록 방식 → 날짜 단위 비교로 변경)
            if (payload.get("app_dates") != null) {
                List<String> newDates = (List<String>) payload.get("app_dates");

                // 2-1. 현재 DB에 등록된 적용일 목록 조회 (삭제 포함 전체)
                String selectExistingQuery = "SELECT APP_SEQ, TO_CHAR(TASK_APP_DT, 'YYYY-MM-DD') AS TASK_APP_DT, DEL_YN " +
                                            "FROM TB_COMP_TASK_APP_DT WHERE TASK_ID = :task_id";
                List<Map<String, Object>> existingRows = jdbcTemplate.queryForList(
                    selectExistingQuery, new MapSqlParameterSource("task_id", task_id)
                );

                // 기존 날짜 → APP_SEQ 맵 구성 (날짜 문자열 기준)
                Map<String, Integer> existingDateSeqMap = new LinkedHashMap<>();
                for (Map<String, Object> row : existingRows) {
                    existingDateSeqMap.put((String) row.get("task_app_dt"), (Integer) row.get("app_seq"));
                }

                // 2-2. 새 날짜 목록 기준으로 INSERT or 소프트딜리트 복원 처리
                // 현재 DB의 최대 APP_SEQ 조회 (신규 순번 채번 기준)
                String maxSeqQuery = "SELECT COALESCE(MAX(APP_SEQ), 0) FROM TB_COMP_TASK_APP_DT WHERE TASK_ID = :task_id";
                int maxSeq = jdbcTemplate.queryForObject(maxSeqQuery, new MapSqlParameterSource("task_id", task_id), Integer.class);

                for (String newDate : newDates) {
                    if (existingDateSeqMap.containsKey(newDate)) {
                        // 이미 존재하는 날짜 → DEL_YN = 'Y'이면 복원, 'N'이면 그대로 유지
                        int seq = existingDateSeqMap.get(newDate);
                        String restoreDtQuery = "UPDATE TB_COMP_TASK_APP_DT SET DEL_YN = 'N', CHG_DTM = now(), CHG_EMP_NO = :emp_no " +
                                                "WHERE TASK_ID = :task_id AND APP_SEQ = :app_seq AND DEL_YN = 'Y'";
                        jdbcTemplate.update(restoreDtQuery, new MapSqlParameterSource()
                            .addValue("emp_no", emp_no)
                            .addValue("task_id", task_id)
                            .addValue("app_seq", seq));
                    } else {
                        // 신규 날짜 → 새 APP_SEQ 채번 후 INSERT
                        maxSeq++;
                        String insertDtQuery = "INSERT INTO TB_COMP_TASK_APP_DT (TASK_ID, APP_SEQ, TASK_APP_DT, DEL_YN, REG_EMP_NO) " +
                                            "VALUES (:task_id, :appSeq, TO_DATE(:appDt, 'YYYY-MM-DD'), 'N', :emp_no)";
                        jdbcTemplate.update(insertDtQuery, new MapSqlParameterSource()
                            .addValue("task_id", task_id)
                            .addValue("appSeq", maxSeq)
                            .addValue("appDt", newDate)
                            .addValue("emp_no", emp_no));
                    }
                }

                // 2-3. 새 날짜 목록에 없는 기존 날짜 → 답변 이력 확인 후 소프트딜리트 또는 하드 DELETE
                for (Map.Entry<String, Integer> entry : existingDateSeqMap.entrySet()) {
                    String existingDate = entry.getKey();
                    int existingSeq = entry.getValue();

                    if (!newDates.contains(existingDate)) {
                        // 답변 이력 존재 여부 확인
                        String ansCheckQuery = "SELECT COUNT(*) FROM TB_COMP_EMP_ANS " +
                                            "WHERE TASK_ID = :task_id AND APP_SEQ = :app_seq";
                        int ansCount = jdbcTemplate.queryForObject(ansCheckQuery, new MapSqlParameterSource()
                            .addValue("task_id", task_id)
                            .addValue("app_seq", existingSeq), Integer.class);

                        if (ansCount > 0) {
                            // 답변 이력 있음 → 소프트 딜리트
                            String softDeleteQuery = "UPDATE TB_COMP_TASK_APP_DT SET DEL_YN = 'Y', CHG_DTM = now(), CHG_EMP_NO = :emp_no " +
                                                    "WHERE TASK_ID = :task_id AND APP_SEQ = :app_seq";
                            jdbcTemplate.update(softDeleteQuery, new MapSqlParameterSource()
                                .addValue("emp_no", emp_no)
                                .addValue("task_id", task_id)
                                .addValue("app_seq", existingSeq));
                        } else {
                            // 답변 이력 없음 → 하드 DELETE
                            String hardDeleteQuery = "DELETE FROM TB_COMP_TASK_APP_DT WHERE TASK_ID = :task_id AND APP_SEQ = :app_seq";
                            jdbcTemplate.update(hardDeleteQuery, new MapSqlParameterSource()
                                .addValue("task_id", task_id)
                                .addValue("app_seq", existingSeq));
                        }
                    }
                }
            }

            return ResponseEntity.ok(Map.of("status", "success"));
        } catch (Exception e) {
            throw e;
        }
    }

    // 📌 TASK 소프트 삭제(Soft Delete) API
    @PostMapping("/delete-compliance-task")
    public ResponseEntity<?> deleteComplianceTask(@RequestParam("taskId") int taskId) {
        try {
            // 1. 단 한 번이라도 답변(동의 진행)이 발생한 적이 있는지 확인
            //    - TB_COMP_TASK_APP_DT_EMP_ANS 에 해당 TASK_ID로 기록이 하나라도 있으면
            //      "동의가 진행된 TASK"로 간주하여 삭제를 막는다.
            //    - 날짜(TB_COMP_TASK_APP_DT)만 등록되어 있고 답변 기록이 전혀 없는 경우는
            //      삭제를 허용한다.
            String checkAnsQuery =
                    "SELECT COUNT(*) FROM TB_COMP_TASK_APP_DT_EMP_ANS " +
                    " WHERE TASK_ID = :taskId ";
            int ansCount = jdbcTemplate.queryForObject(
                    checkAnsQuery, new MapSqlParameterSource("taskId", taskId), Integer.class);

            if (ansCount > 0) {
                return ResponseEntity.status(HttpStatus.CONFLICT)
                        .body(Map.of("message", "이미 동의가 진행된 TASK는 삭제할 수 없습니다."));
            }

            String query = "UPDATE TB_COMP_TASK SET DEL_YN = 'Y', CHG_DTM = now() WHERE TASK_ID = :taskId";
            MapSqlParameterSource params = new MapSqlParameterSource("taskId", taskId);
            jdbcTemplate.update(query, params);

            query = "UPDATE TB_COMP_TASK_APP_DT SET DEL_YN = 'Y', CHG_DTM = now() WHERE TASK_ID = :taskId";
            jdbcTemplate.update(query, params);

            return ResponseEntity.ok(Map.of("status", "success"));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", e.getMessage()));
        }
    }

    // 📌 이미지 POOL 조회 API (TASK 등록/수정 화면에서 이미지 선택용으로 사용)
    @GetMapping("/get-img-pool")
    public ResponseEntity<?> getComplianceImgPool() {
        try {
            String query = "SELECT IMG_ID AS img_id " +
                                " , IMG_FLNM AS img_flnm " +
                                " , IMG_TYPE AS img_type " +
                            " FROM TB_COMP_IMG_POOL " +
                            " WHERE (DEL_YN = 'N' OR DEL_YN = NULL) " +
                            " ORDER BY IMG_ID";
            List<Map<String, Object>> qstnPool = jdbcTemplate.queryForList(query, new MapSqlParameterSource());
            return ResponseEntity.ok(qstnPool);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", e.getMessage()));
        }
    }
}