package com.kbds.compliance.controller;

import com.kbds.compliance.dto.*;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

@RestController
@RequiredArgsConstructor
public class ComplianceController {

    private final NamedParameterJdbcTemplate jdbcTemplate;

    // 공통 에러 응답
    private Map<String, String> errorResponse(String message) {
        Map<String, String> response = new HashMap<>();
        response.put("status", "error");
        response.put("message", message);
        return response;
    }

    // 공통 성공 응답
    private Map<String, String> successResponse(String message) {
        Map<String, String> response = new HashMap<>();
        response.put("status", "success");
        response.put("message", message);
        return response;
    }

    // 📌 1. 준법 서약/자가점검 제출 API
    @PostMapping("/submit-compliance")
    @Transactional
    public ResponseEntity<?> submitCompliance(@RequestBody SubmitComplianceRequest data) {
        try {
            // [검증 1] 유효한 점검 항목(Task)인지 및 상태 확인
            String taskQuery = "SELECT TASK_ID, TASK_TYPE, PBLS_YN FROM TB_COMP_TASK WHERE TASK_ID = :taskId AND DEL_YN = 'N'";
            MapSqlParameterSource params = new MapSqlParameterSource("taskId", data.getTask_id());
            List<Map<String, Object>> tasks = jdbcTemplate.queryForList(taskQuery, params);

            if (tasks.isEmpty()) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(errorResponse("활성화된 준법 항목을 찾을 수 없습니다."));
            }
            Map<String, Object> task = tasks.get(0);
            if (!"Y".equals(task.get("PBLS_YN"))) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse("현재 게시 중인 항목이 아닙니다."));
            }

            // [검증 2] 등록된 마스터 사원인지 확인
            String empQuery = "SELECT EMP_NO FROM TB_EMP WHERE EMP_NO = :empNo AND DEL_YN = 'N'";
            MapSqlParameterSource empParams = new MapSqlParameterSource("empNo", data.getEmp_no());
            List<Map<String, Object>> employees = jdbcTemplate.queryForList(empQuery, empParams);

            if (employees.isEmpty()) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(errorResponse("준법 관리 대상 사용자가 아니거나 찾을 수 없습니다."));
            }

            // [검증 3] 중복 제출 방지 (동일 회차 및 사번 기준 완료 여부)
            String logCheckQuery = "SELECT EMP_NO FROM TB_COMP_EMP_ANS " +
                    "WHERE TASK_ID = :taskId AND APP_SEQ = :appSeq AND EMP_NO = :empNo AND EMP_ANS_YN = 'Y'";
            MapSqlParameterSource logParams = new MapSqlParameterSource()
                    .addValue("taskId", data.getTask_id())
                    .addValue("appSeq", data.getApp_seq())
                    .addValue("empNo", data.getEmp_no());
            List<Map<String, Object>> logs = jdbcTemplate.queryForList(logCheckQuery, logParams);

            if (!logs.isEmpty()) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse("이미 제출을 완료한 항목입니다."));
            }

            LocalDateTime now = LocalDateTime.now();
            String taskType = (String) task.get("TASK_TYPE");

            // [핵심 로직] 정규화 구조에 맞춘 로우 단위 적재
            String insertQuery = "INSERT INTO TB_COMP_EMP_ANS (EMP_NO, TASK_ID, APP_SEQ, QSTN_CD, ANS_DT, EMP_ANS_YN, DEL_YN, REG_EMP_NO) " +
                    "VALUES (:empNo, :taskId, :appSeq, :qstnCd, :ansDt, :empAnsYn, 'N', :regEmpNo)";

            if ("ETHICS".equals(taskType) && (data.getAnswers() == null || data.getAnswers().isEmpty())) {
                // ETHICS 타입은 매핑된 질문이 없으므로 'NONE' 플래그 코드로 1건 적재
                MapSqlParameterSource insertParams = new MapSqlParameterSource()
                        .addValue("empNo", data.getEmp_no())
                        .addValue("taskId", data.getTask_id())
                        .addValue("appSeq", data.getApp_seq())
                        .addValue("qstnCd", "NONE")
                        .addValue("ansDt", now)
                        .addValue("empAnsYn", "Y")
                        .addValue("regEmpNo", data.getEmp_no());
                jdbcTemplate.update(insertQuery, insertParams);
            } else {
                // SELF_CHECK 문항 루프 실행하며 개별 로우 추가
                for (AnswerItem item : data.getAnswers()) {
                    MapSqlParameterSource insertParams = new MapSqlParameterSource()
                            .addValue("empNo", data.getEmp_no())
                            .addValue("taskId", data.getTask_id())
                            .addValue("appSeq", data.getApp_seq())
                            .addValue("qstnCd", item.getQstn_cd())
                            .addValue("ansDt", now)
                            .addValue("empAnsYn", item.getEmp_ans_yn())
                            .addValue("regEmpNo", data.getEmp_no());
                    jdbcTemplate.update(insertQuery, insertParams);
                }
            }

            return ResponseEntity.ok(successResponse("준법 프로그램 수행 기록이 정상적으로 저장되었습니다."));

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse(e.getMessage()));
        }
    }

    // 📌 2. 전체 서약/수행 완료 로그 조회 API (관리자 뷰어 대시보드용)
    @GetMapping("/get-all-answers")
    public ResponseEntity<?> getAllAnswers(
            @RequestParam(value = "task_id", required = false) Long taskId,
            @RequestParam(value = "app_seq", required = false) Integer appSeq) {
        try {
            String query;
            MapSqlParameterSource params = new MapSqlParameterSource();

            if (taskId == null || taskId == 0) {
                // 준법 항목 선택이 안 된 경우 기본 전체 마스터 사용자 가공 데이터 반환
                query = "WITH TMP1 AS (" +
                            " SELECT TASK.TASK_ID AS task_id "+
                            "     , TASK.TASK_NM AS task_nm "+
                            "     , EMP.EMP_NM AS emp_nm "+
                            "     , EMP.EMP_NO AS emp_no "+
                            "     , COALESCE(EMP.IP, '0.0.0.0') AS ip "+
                            "     , CTAD.APP_SEQ "+
                            "     , CTAD.TASK_APP_DT "+
                            " FROM TB_COMP_TASK TASK "+
                            " , TB_COMP_TASK_APP_DT CTAD "+
                            " , TB_EMP EMP "+
                            " WHERE TASK.TASK_ID = CTAD.TASK_ID "+
                            " ORDER BY TASK.TASK_ID, CTAD.TASK_APP_DT, EMP.EMP_NO "+
                        " ) "+
                        " SELECT TP1.task_id "+
                            " , TP1.task_nm "+
                            " , TP1.APP_SEQ "+
                            " , TP1.TASK_APP_DT "+
                            " , TP1.emp_nm "+
                            " , TP1.emp_no "+
                            " , TP1.ip  "+
                            " , COALESCE(CTADEA.EMP_MAIN_ANS_YN, 'N') AS emp_main_ans_yn   "+
                            " , COALESCE(CTADEA.EMP_ANS_AGR_YN, 'N') AS emp_ans_agr_yn   "+
                            " , CTADEA.ANS_DT AS ans_dt  "+
                        " FROM TMP1 TP1 "+
                        " LEFT JOIN TB_COMP_TASK_APP_DT_EMP_ANS CTADEA "+
                            " ON CTADEA.TASK_ID = TP1.TASK_ID "+
                            " AND CTADEA.APP_SEQ = TP1.APP_SEQ "+
                            " AND CTADEA.EMP_NO = TP1.EMP_NO "+
                            " AND (CTADEA.DEL_YN = 'N' or CTADEA.DEL_YN is null ) ";

            } else {
                params.addValue("taskId", taskId);
                params.addValue("appSeq", appSeq);

                if ( appSeq == null || appSeq == 0 ) {
                    query = "WITH TMP1 AS (" +
                            " SELECT TASK.TASK_ID AS task_id "+
                            "     , TASK.TASK_NM AS task_nm "+
                            "     , EMP.EMP_NM AS emp_nm "+
                            "     , EMP.EMP_NO AS emp_no "+
                            "     , COALESCE(EMP.IP, '0.0.0.0') AS ip "+
                            "     , CTAD.APP_SEQ "+
                            "     , CTAD.TASK_APP_DT "+
                            " FROM TB_COMP_TASK TASK "+
                            " , TB_COMP_TASK_APP_DT CTAD "+
                            " , TB_EMP EMP "+
                            " WHERE TASK.TASK_ID = :taskId "+
                            " AND TASK.TASK_ID = CTAD.TASK_ID "+
                            " ORDER BY TASK.TASK_ID, CTAD.TASK_APP_DT, EMP.EMP_NO "+
                        " ) "+
                        " SELECT TP1.task_id "+
                            " , TP1.task_nm "+
                            " , TP1.APP_SEQ "+
                            " , TP1.TASK_APP_DT "+
                            " , TP1.emp_nm "+
                            " , TP1.emp_no "+
                            " , TP1.ip  "+
                            " , COALESCE(CTADEA.EMP_MAIN_ANS_YN, 'N') AS emp_main_ans_yn   "+
                            " , COALESCE(CTADEA.EMP_ANS_AGR_YN, 'N') AS emp_ans_agr_yn   "+
                            " , CTADEA.ANS_DT AS ans_dt  "+
                        " FROM TMP1 TP1 "+
                        " LEFT JOIN TB_COMP_TASK_APP_DT_EMP_ANS CTADEA "+
                            " ON CTADEA.TASK_ID = TP1.TASK_ID "+
                            " AND CTADEA.APP_SEQ = TP1.APP_SEQ "+
                            " AND CTADEA.EMP_NO = TP1.EMP_NO "+
                            " AND (CTADEA.DEL_YN = 'N' or CTADEA.DEL_YN is null ) ";
                } else {
                    query = "WITH TMP1 AS (" +
                            " SELECT TASK.TASK_ID AS task_id "+
                            "     , TASK.TASK_NM AS task_nm "+
                            "     , EMP.EMP_NM AS emp_nm "+
                            "     , EMP.EMP_NO AS emp_no "+
                            "     , COALESCE(EMP.IP, '0.0.0.0') AS ip "+
                            "     , CTAD.APP_SEQ "+
                            "     , CTAD.TASK_APP_DT "+
                            " FROM TB_COMP_TASK TASK "+
                            " , TB_COMP_TASK_APP_DT CTAD "+
                            " , TB_EMP EMP "+
                            " WHERE TASK.TASK_ID = :taskId "+
                            " AND TASK.TASK_ID = CTAD.TASK_ID "+
                            " AND CTAD.APP_SEQ = :appSeq "+
                            " ORDER BY TASK.TASK_ID, CTAD.TASK_APP_DT, EMP.EMP_NO "+
                        " ) "+
                        " SELECT TP1.task_id "+
                            " , TP1.task_nm "+
                            " , TP1.APP_SEQ "+
                            " , TP1.TASK_APP_DT "+
                            " , TP1.emp_nm "+
                            " , TP1.emp_no "+
                            " , TP1.ip  "+
                            " , COALESCE(CTADEA.EMP_MAIN_ANS_YN, 'N') AS emp_main_ans_yn   "+
                            " , COALESCE(CTADEA.EMP_ANS_AGR_YN, 'N') AS emp_ans_agr_yn   "+
                            " , CTADEA.ANS_DT AS ans_dt  "+
                        " FROM TMP1 TP1 "+
                        " LEFT JOIN TB_COMP_TASK_APP_DT_EMP_ANS CTADEA "+
                            " ON CTADEA.TASK_ID = TP1.TASK_ID "+
                            " AND CTADEA.APP_SEQ = TP1.APP_SEQ "+
                            " AND CTADEA.EMP_NO = TP1.EMP_NO "+
                            " AND (CTADEA.DEL_YN = 'N' or CTADEA.DEL_YN is null ) ";
                }
                
            }

            List<Map<String, Object>> rows = jdbcTemplate.queryForList(query, params);
            List<Map<String, Object>> result = new ArrayList<>();
            
            // 💡 자바의 패턴 규격 매칭 (yyyy-MM-dd HH:mm:ss)
            DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

            for (Map<String, Object> row : rows) {
                Map<String, Object> rowMap = new LinkedHashMap<>(row);
                if (rowMap.get("ans_dt") != null) {
                    LocalDateTime ansDt = ((java.sql.Timestamp) rowMap.get("ans_dt")).toLocalDateTime();
                    rowMap.put("ans_dt", ansDt.format(formatter));
                } else {
                    rowMap.put("ans_dt", "-");
                }
                result.add(rowMap);
            }

            return ResponseEntity.ok(result);

        } catch (Exception e) {
            throw e;
            //return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse(e.getMessage()));
        }
    }

    // 📌 7. 모든 직원 목록 조회 API (직원 관리 및 대시보드 연동 규격)
    @GetMapping("/get-all-employees")
    public ResponseEntity<?> getAllEmployees() {
        try {
            // TB_EMP 테이블에서 삭제되지 않은 직원을 사원번호 순으로 정렬하여 조회
            String query = "SELECT EMP_NO AS emp_no, EMP_NM AS emp_nm, IP AS ip " +
                           "FROM TB_EMP " +
                           "WHERE DEL_YN = 'N' " +
                           "ORDER BY EMP_NO ASC";
                           
            List<Map<String, Object>> empList = jdbcTemplate.queryForList(query, new MapSqlParameterSource());
            return ResponseEntity.ok(empList);

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("message", e.getMessage()));
        }
    }

    // 📌 3. 대상 사원 추가 API (사원 마스터 테이블 반영)
    @PostMapping("/add-employee")
    @Transactional
    public ResponseEntity<?> addEmployee(@RequestBody EmployeeAddRequest data) {
        try {
            String checkQuery = "SELECT EMP_NO FROM TB_EMP WHERE EMP_NO = :empNo";
            MapSqlParameterSource params = new MapSqlParameterSource("empNo", data.getEmp_no());
            List<Map<String, Object>> employees = jdbcTemplate.queryForList(checkQuery, params);

            if (!employees.isEmpty()) {
                return ResponseEntity.status(HttpStatus.CONFLICT).body(errorResponse("이미 등록된 사번입니다."));
            }

            String insertQuery = "INSERT INTO TB_EMP (EMP_NO, EMP_NM, IP, DEL_YN, REG_EMP_NO) " +
                    "VALUES (:empNo, :empNm, :ip, 'N', 'ADMIN')";
            MapSqlParameterSource insertParams = new MapSqlParameterSource()
                    .addValue("empNo", data.getEmp_no())
                    .addValue("empNm", data.getEmp_nm())
                    .addValue("ip", data.getIp());

            jdbcTemplate.update(insertQuery, insertParams);

            return ResponseEntity.status(HttpStatus.CREATED).body(successResponse(data.getEmp_nm() + " 사원이 관리 마스터에 유입되었습니다."));

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse(e.getMessage()));
        }
    }

    // 📌 4. 대상 사원 다중 삭제 API (소프트 딜리트 변경)
    @PostMapping("/delete-employees")
    @Transactional
    public ResponseEntity<?> deleteEmployees(@RequestBody EmployeeDeleteRequest data) {
        try {
            if (data.getEmp_nos() == null || data.getEmp_nos().isEmpty()) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse("삭제할 사번 리스트가 누락되었습니다."));
            }

            // 하드 삭제 대신 시스템 안정성을 위해 DEL_YN = 'Y' 플래그 업데이트 처리
            String deleteQuery = "UPDATE TB_EMP SET DEL_YN = 'Y' WHERE EMP_NO IN (:empNos)";
            MapSqlParameterSource params = new MapSqlParameterSource("empNos", data.getEmp_nos());
            
            int updatedCount = jdbcTemplate.update(deleteQuery, params);

            if (updatedCount == 0) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(errorResponse("삭제 대상 사용자를 찾을 수 없습니다."));
            }

            return ResponseEntity.ok(successResponse("총 " + updatedCount + "명의 대상자가 명단에서 제외되었습니다."));

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse(e.getMessage()));
        }
    }

    // 📌 [기존 호환 및 확장] 1. 준법 항목 목록 상세 조회 API (전체 필드 포함)
    @GetMapping("/get-compliance-tasks")
    public ResponseEntity<?> getComplianceTasks() {
        try {
            String query = "SELECT TASK_ID AS task_id, TASK_NM AS task_nm, TASK_TYPE AS task_type, " +
                           "TASK_CN AS task_cn, RCRN_YN AS rcrn_yn, PBLS_YN AS pbls_yn " +
                           "FROM TB_COMP_TASK WHERE DEL_YN = 'N' ORDER BY TASK_ID DESC";

            List<Map<String, Object>> taskList = jdbcTemplate.queryForList(query, new MapSqlParameterSource());

            query = " SELECT TASK.TASK_ID AS task_id "+
                            " , CTAD.APP_SEQ AS app_seq "+
                            " , CTAD.TASK_APP_DT AS task_app_dt "+
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

    // 📌 2. 자가점검 질문 풀(POOL) 조회 API
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

    // 📌 3. 특정 TASK에 매핑된 질문 코드 목록 조회 API
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

    // 📌 8. 이미 다른 TASK에서 사용 중인 모든 적용일 목록 조회 (과거 날짜 제외)
    @GetMapping("/get-all-used-dates")
    public ResponseEntity<?> getAllUsedDates() {
        try {
            String query = "SELECT DISTINCT TO_CHAR(TASK_APP_DT, 'YYYY-MM-DD') AS app_dt " +
                           "FROM TB_COMP_TASK_APP_DT " +
                           "WHERE DEL_YN = 'N' AND TASK_APP_DT >= CURRENT_DATE";
            List<Map<String, Object>> rows = jdbcTemplate.queryForList(query, new MapSqlParameterSource());
            List<String> dates = rows.stream().map(r -> (String) r.get("app_dt")).toList();
            return ResponseEntity.ok(dates);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", e.getMessage()));
        }
    }

    // 📌 9. 특정 TASK에 등록된 적용일 목록 조회 API
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

    // 📌 [수정] 4. 신규 준법 TASK 등록 API (적용일 Multi Row insert 반영)
    @PostMapping("/create-compliance-task")
    @Transactional
    public ResponseEntity<?> createComplianceTask(@RequestBody Map<String, Object> payload) {
        try {
            // 1. 마스터 Insert
            String taskQuery = "INSERT INTO TB_COMP_TASK (TASK_NM, TASK_TYPE, TASK_CN, RCRN_YN, PBLS_YN, DEL_YN, REG_EMP_NO) " +
                               "VALUES (:taskNm, :taskType, :taskCn, :rcrnYn, :pblcYn, 'N', 'SYSTEM') RETURNING TASK_ID";
            
            int taskId = jdbcTemplate.queryForObject(taskQuery, new MapSqlParameterSource(payload), Integer.class);

            // 2. 질문 매핑 (기존 로직 유지)
            if ("SELF_CHECK".equals(payload.get("task_type")) && payload.get("selected_qstn_cds") != null) {
                // ... 생략 (기존 질문 등록 batchUpdate 동일) ...
            }

            // 3. 다중 적용일 등록 (APP_SEQ는 1부터 순차 생성)
            if (payload.get("app_dates") != null) {
                List<String> appDates = (List<String>) payload.get("app_dates");
                if (!appDates.isEmpty()) {
                    String dtQuery = "INSERT INTO TB_COMP_TASK_APP_DT (TASK_ID, APP_SEQ, TASK_APP_DT, DEL_YN, REG_EMP_NO) " +
                                     "VALUES (:taskId, :appSeq, TO_DATE(:appDt, 'YYYY-MM-DD'), 'N', 'SYSTEM')";
                    List<Map<String, Object>> batchValues = new ArrayList<>();
                    int seq = 1;
                    for (String dt : appDates) {
                        batchValues.add(Map.of("taskId", taskId, "appSeq", seq++, "appDt", dt));
                    }
                    jdbcTemplate.batchUpdate(dtQuery, batchValues.toArray(new Map[0]));
                }
            }
            return ResponseEntity.ok(Map.of("status", "success"));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", e.getMessage()));
        }
    }

    // 📌 [수정] 5. 기존 TASK 수정 및 날짜 갱신 API
    @PostMapping("/update-compliance-task")
    @Transactional
    public ResponseEntity<?> updateComplianceTask(@RequestBody Map<String, Object> payload) {
        try {
            int taskId = (Integer) payload.get("task_id");
            
            // 1. 마스터 업데이트
            String updateQuery = "UPDATE TB_COMP_TASK SET TASK_NM = :taskNm, PBLS_YN = :pblsYn, TASK_CN = :taskCn, CHG_DTM = now() WHERE TASK_ID = :taskId";
            jdbcTemplate.update(updateQuery, new MapSqlParameterSource(payload));

            // 2. 기존 적용일 데이터 일괄 삭제 후 재등록 (또는 변경분 갱신)
            jdbcTemplate.update("DELETE FROM TB_COMP_TASK_APP_DT WHERE TASK_ID = :taskId", new MapSqlParameterSource("taskId", taskId));
            
            if (payload.get("app_dates") != null) {
                List<String> appDates = (List<String>) payload.get("app_dates");
                int seq = 1;
                List<Map<String, Object>> batchValues = new ArrayList<>();
                for (String dt : appDates) {
                    batchValues.add(Map.of("taskId", taskId, "appSeq", seq++, "appDt", dt));
                }
                String dtQuery = "INSERT INTO TB_COMP_TASK_APP_DT (TASK_ID, APP_SEQ, TASK_APP_DT, DEL_YN, REG_EMP_NO) VALUES (:taskId, :appSeq, TO_DATE(:appDt, 'YYYY-MM-DD'), 'N', 'SYSTEM')";
                jdbcTemplate.batchUpdate(dtQuery, batchValues.toArray(new Map[0]));
            }

            return ResponseEntity.ok(Map.of("status", "success"));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", e.getMessage()));
        }
    }

    // 📌 6. TASK 소프트 삭제(Soft Delete) API
    @PostMapping("/delete-compliance-task")
    public ResponseEntity<?> deleteComplianceTask(@RequestParam("taskId") int taskId) {
        try {
            String query = "UPDATE TB_COMP_TASK SET DEL_YN = 'Y', CHG_DTM = now() WHERE TASK_ID = :taskId";
            MapSqlParameterSource params = new MapSqlParameterSource("taskId", taskId);
            jdbcTemplate.update(query, params);
            return ResponseEntity.ok(Map.of("status", "success"));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", e.getMessage()));
        }
    }
}