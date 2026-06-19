package com.kbds.compliance.controller;

import com.kbds.compliance.dto.*;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.*;

import static com.kbds.compliance.controller.ApiResponseUtil.errorResponse;
import static com.kbds.compliance.controller.ApiResponseUtil.successResponse;

/**
 * 📌 윈도우 클라이언트 앱(직원용)에서 사용하는 API
 *  - 직원 PC에 설치된 윈도우 앱이 호출: 오늘의 준법 항목 조회 + 서약/점검 제출
 */
@RestController
@RequiredArgsConstructor
public class ClientAppController {

    private final NamedParameterJdbcTemplate jdbcTemplate;

    // 📌 준법 서약/자가점검 제출 API
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
                    "WHERE TASK_ID = :taskId AND APP_SEQ = :appSeq AND EMP_NO = :empNo ";
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
            String insertQuery = "INSERT INTO TB_COMP_TASK_APP_DT_EMP_ANS (TASK_ID, APP_SEQ, EMP_NO, EMP_MAIN_ANS_YN, EMP_ANS_AGR_YN, ANS_DT, DEL_YN, REG_EMP_NO) " +
                    "VALUES (:taskId, :appSeq, :empNo, :empMainAnsYn, :empAnsAgrYn, :ansDt, 'N', :regEmpNo)";
            MapSqlParameterSource insertAnsParams = new MapSqlParameterSource()
                        .addValue("taskId", data.getTask_id())
                        .addValue("appSeq", data.getApp_seq())
                        .addValue("empNo", data.getEmp_no())
                        .addValue("empMainAnsYn", data.getEmp_main_ans_yn())
                        .addValue("empAnsAgrYn", data.getEmp_ans_agr_yn())
                        .addValue("ansDt", now)
                        .addValue("regEmpNo", data.getEmp_no());
            jdbcTemplate.update(insertQuery, insertAnsParams);

            insertQuery = "INSERT INTO TB_COMP_EMP_ANS (EMP_NO, TASK_ID, APP_SEQ, QSTN_CD, ANS_DT, EMP_ANS_YN, DEL_YN, REG_EMP_NO) " +
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

    // 📌 직원별 질문 대상 여부 조회 API
    @GetMapping("/get-task-qstn")
    public ResponseEntity<?> getemployeeTaskYn(@RequestParam(value = "emp_no", required = false) String empNo) {
        try {
            
            String taskYn = "";
            List<Map<String, Object>> results = new ArrayList<>();
            MapSqlParameterSource params = new MapSqlParameterSource();

            params.addValue("empNo", empNo);
            // TB_EMP 테이블에서 삭제되지 않은 직원을 조회
            String query = "SELECT EMP_NO AS emp_no, EMP_NM AS emp_nm, IP AS ip " +
                           "FROM TB_EMP " +
                           "WHERE EMP_NO = :empNo " +
                           " AND ( DEL_YN = 'N' OR DEL_YN = null )";
            List<Map<String, Object>> empList = jdbcTemplate.queryForList(query, params);

            if ( empList.size() > 0 ) { // 대상 직원이면
                LocalDate todayLocalDate = LocalDate.now();
                String todayDate = todayLocalDate.toString();
                params.addValue("todayDate", todayDate);
                System.out.println("todayDate ====>> "+todayDate);
                
                query = "SELECT TASK.TASK_ID AS task_id "+
                            " , TASK.TASK_NM AS task_nm "+
                            " , TASK.TASK_TYPE AS task_type "+
                            " , TASK.TASK_CN AS task_cn "+
                            " , TASK.IMG_FLNM AS img_flnm "+
                            " , TASK.RCRN_YN AS rcrn_yn "+
                            " , TASK.RCRN_CYC_CD AS rcrn_cyc_cd "+
                            " , TASK.PBLS_YN AS pbls_yn "+
                            " , CTAD.APP_SEQ AS app_seq "+
                            " , TO_CHAR(CTAD.TASK_APP_DT, 'YYYY-MM-DD') AS task_app_dt "+
                        " FROM TB_COMP_TASK TASK, TB_COMP_TASK_APP_DT CTAD "+
                        " WHERE TASK.TASK_ID = CTAD.TASK_ID "+
                        " AND CTAD.TASK_APP_DT = TO_DATE(:todayDate, 'YYYY-MM-DD')"+
                        " AND (TASK.DEL_YN = 'N' OR TASK.DEL_YN = NULL) "+
                        " AND (CTAD.DEL_YN = 'N' OR CTAD.DEL_YN = NULL)" +
                        " AND TASK.PBLS_YN = 'Y'";
                results = jdbcTemplate.queryForList(query, params);

                for (Map<String, Object> result : results) {

                    String logCheckQuery = "SELECT EMP_NO FROM TB_COMP_EMP_ANS " +
                                        "WHERE TASK_ID = :taskId AND APP_SEQ = :appSeq AND EMP_NO = :empNo ";
                    MapSqlParameterSource logParams = new MapSqlParameterSource()
                            .addValue("taskId", result.get("task_id"))
                            .addValue("appSeq", result.get("app_seq"))
                            .addValue("empNo", empNo);
                    List<Map<String, Object>> logs = jdbcTemplate.queryForList(logCheckQuery, logParams);

                    if (!logs.isEmpty()) {
                        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse("이미 제출을 완료한 항목입니다."));
                    }

                    int task_id = (Integer) result.get("task_id");

                    List<Map<String, Object>> qstnList = new ArrayList<>();
                    MapSqlParameterSource qstnParams = new MapSqlParameterSource();

                    qstnParams.addValue("task_id", task_id);
                     query = "SELECT CTQ.TASK_ID AS task_id "+
                                " , CTQ.QSTN_CD AS qstn_cd "+
                                " , CQP.QSTN_NM AS qstn_nm "+
                                " , CQP.QSTN_TYPE AS qstn_type "+
                                " , CQP.QSTN_CN AS qstn_cn "+
                                " , CQP.QSTN_STD_ANS_YN AS qstn_std_ans_yn "+
                            " FROM TB_COMP_TASK_QSTN CTQ, TB_COMP_QSTN_POOL CQP "+
                            " WHERE CTQ.TASK_ID = :task_id "+
                            " AND (CTQ.DEL_YN = 'N' OR CTQ.DEL_YN = NULL) "+
                            " AND CTQ.QSTN_CD = CQP.QSTN_CD "+
                            " AND (CQP.DEL_YN = 'N' OR CQP.DEL_YN = NULL)";

                    qstnList = jdbcTemplate.queryForList(query, qstnParams);   
                    result.put("qstn_list",qstnList);
                }
            }
            System.out.println("results ====>> "+results);


            return ResponseEntity.ok(results);

        } catch (Exception e) {
            throw e;
            //return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", e.getMessage()));
        }
    }
}