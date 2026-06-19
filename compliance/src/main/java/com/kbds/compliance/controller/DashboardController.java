package com.kbds.compliance.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

/**
 * 📌 관리자 대시보드에서 사용하는 조회 API
 *  - 전체 서약/점검 현황 조회, 특정 직원의 상세 답변 내역 조회
 */
@RestController
@RequiredArgsConstructor
public class DashboardController {

    private final NamedParameterJdbcTemplate jdbcTemplate;

    // 📌 전체 서약/수행 완료 로그 조회 API (관리자 뷰어 대시보드용)
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
                            // (A) 현재 활성 대상자 (TB_EMP 기준)
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
                            "   AND (TASK.DEL_YN = 'N' OR TASK.DEL_YN = NULL) "+
                            "   AND (CTAD.DEL_YN = 'N' OR CTAD.DEL_YN = NULL) "+
                            "   AND (EMP.DEL_YN = 'N' OR EMP.DEL_YN = NULL) "+

                            " UNION "+

                            // (B) 삭제된 직원이라도 이미 답변(동의) 기록이 있으면 포함
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
                            " , TB_COMP_TASK_APP_DT_EMP_ANS CTADEA2 "+
                            " WHERE TASK.TASK_ID = CTAD.TASK_ID "+
                            "   AND CTADEA2.TASK_ID = TASK.TASK_ID "+
                            "   AND CTADEA2.APP_SEQ = CTAD.APP_SEQ "+
                            "   AND CTADEA2.EMP_NO = EMP.EMP_NO "+
                            "   AND (TASK.DEL_YN = 'N' OR TASK.DEL_YN = NULL) "+
                            "   AND (CTAD.DEL_YN = 'N' OR CTAD.DEL_YN = NULL) "+
                            "   AND (CTADEA2.DEL_YN = 'N' OR CTADEA2.DEL_YN = NULL) "+
                        " ) "+
                        " SELECT TP1.task_id as task_id "+
                            " , TP1.task_nm as task_nm "+
                            " , TP1.APP_SEQ as app_seq "+
                            " , TO_CHAR(TP1.TASK_APP_DT, 'YYYY-MM-DD') as task_app_dt "+
                            " , TP1.emp_nm as emp_nm"+
                            " , TP1.emp_no as emp_no"+
                            " , TP1.ip as ip "+
                            " , COALESCE(CTADEA.EMP_MAIN_ANS_YN, 'N') AS emp_main_ans_yn   "+
                            " , COALESCE(CTADEA.EMP_ANS_AGR_YN, 'N') AS emp_ans_agr_yn   "+
                            " , CTADEA.ANS_DT AS ans_dt  "+
                        " FROM TMP1 TP1 "+
                        " LEFT JOIN TB_COMP_TASK_APP_DT_EMP_ANS CTADEA "+
                            " ON CTADEA.TASK_ID = TP1.TASK_ID "+
                            " AND CTADEA.APP_SEQ = TP1.APP_SEQ "+
                            " AND CTADEA.EMP_NO = TP1.EMP_NO "+
                            " AND (CTADEA.DEL_YN = 'N' or CTADEA.DEL_YN is null ) "+
                        " ORDER BY TP1.task_id, TP1.TASK_APP_DT, TP1.emp_no ";

            } else {
                params.addValue("taskId", taskId);
                params.addValue("appSeq", appSeq);

                if ( appSeq == null || appSeq == 0 ) {
                    query = "WITH TMP1 AS (" +
                            // (A) 현재 활성 대상자
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
                            "   AND (TASK.DEL_YN = 'N' OR TASK.DEL_YN = NULL) "+
                            "   AND (CTAD.DEL_YN = 'N' OR CTAD.DEL_YN = NULL) "+
                            "   AND (EMP.DEL_YN = 'N' OR EMP.DEL_YN = NULL) "+

                            " UNION "+

                            // (B) 삭제된 직원이라도 이미 답변(동의) 기록이 있으면 포함
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
                            " , TB_COMP_TASK_APP_DT_EMP_ANS CTADEA2 "+
                            " WHERE TASK.TASK_ID = :taskId "+
                            "   AND TASK.TASK_ID = CTAD.TASK_ID "+
                            "   AND CTADEA2.TASK_ID = TASK.TASK_ID "+
                            "   AND CTADEA2.APP_SEQ = CTAD.APP_SEQ "+
                            "   AND CTADEA2.EMP_NO = EMP.EMP_NO "+
                            "   AND (TASK.DEL_YN = 'N' OR TASK.DEL_YN = NULL) "+
                            "   AND (CTAD.DEL_YN = 'N' OR CTAD.DEL_YN = NULL) "+
                            "   AND (CTADEA2.DEL_YN = 'N' OR CTADEA2.DEL_YN = NULL) "+
                        " ) "+
                        " SELECT TP1.task_id as task_id "+
                            " , TP1.task_nm as task_nm "+
                            " , TP1.APP_SEQ as app_seq "+
                            " , TO_CHAR(TP1.TASK_APP_DT, 'YYYY-MM-DD') as task_app_dt "+
                            " , TP1.emp_nm as emp_nm "+
                            " , TP1.emp_no as emp_no "+
                            " , TP1.ip as ip "+
                            " , COALESCE(CTADEA.EMP_MAIN_ANS_YN, 'N') AS emp_main_ans_yn   "+
                            " , COALESCE(CTADEA.EMP_ANS_AGR_YN, 'N') AS emp_ans_agr_yn   "+
                            " , CTADEA.ANS_DT AS ans_dt  "+
                        " FROM TMP1 TP1 "+
                        " LEFT JOIN TB_COMP_TASK_APP_DT_EMP_ANS CTADEA "+
                            " ON CTADEA.TASK_ID = TP1.TASK_ID "+
                            " AND CTADEA.APP_SEQ = TP1.APP_SEQ "+
                            " AND CTADEA.EMP_NO = TP1.EMP_NO "+
                            " AND (CTADEA.DEL_YN = 'N' or CTADEA.DEL_YN is null ) "+
                        " ORDER BY TP1.task_id, TP1.TASK_APP_DT, TP1.emp_no ";
                } else {
                    query = "WITH TMP1 AS (" +
                            // (A) 현재 활성 대상자
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
                            "   AND (TASK.DEL_YN = 'N' OR TASK.DEL_YN = NULL) "+
                            "   AND (CTAD.DEL_YN = 'N' OR CTAD.DEL_YN = NULL) "+
                            "   AND (EMP.DEL_YN = 'N' OR EMP.DEL_YN = NULL) "+

                            " UNION "+

                            // (B) 삭제된 직원이라도 이미 답변(동의) 기록이 있으면 포함
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
                            " , TB_COMP_TASK_APP_DT_EMP_ANS CTADEA2 "+
                            " WHERE TASK.TASK_ID = :taskId "+
                            "   AND TASK.TASK_ID = CTAD.TASK_ID "+
                            "   AND CTAD.APP_SEQ = :appSeq "+
                            "   AND CTADEA2.TASK_ID = TASK.TASK_ID "+
                            "   AND CTADEA2.APP_SEQ = CTAD.APP_SEQ "+
                            "   AND CTADEA2.EMP_NO = EMP.EMP_NO "+
                            "   AND (TASK.DEL_YN = 'N' OR TASK.DEL_YN = NULL) "+
                            "   AND (CTAD.DEL_YN = 'N' OR CTAD.DEL_YN = NULL) "+
                            "   AND (CTADEA2.DEL_YN = 'N' OR CTADEA2.DEL_YN = NULL) "+
                        " ) "+
                        " SELECT TP1.task_id as task_id "+
                            " , TP1.task_nm as task_nm "+
                            " , TP1.APP_SEQ as app_seq "+
                            " , TO_CHAR(TP1.TASK_APP_DT, 'YYYY-MM-DD') as task_app_dt "+
                            " , TP1.emp_nm as emp_nm"+
                            " , TP1.emp_no as emp_no"+
                            " , TP1.ip as ip "+
                            " , COALESCE(CTADEA.EMP_MAIN_ANS_YN, 'N') AS emp_main_ans_yn   "+
                            " , COALESCE(CTADEA.EMP_ANS_AGR_YN, 'N') AS emp_ans_agr_yn   "+
                            " , CTADEA.ANS_DT AS ans_dt  "+
                        " FROM TMP1 TP1 "+
                        " LEFT JOIN TB_COMP_TASK_APP_DT_EMP_ANS CTADEA "+
                            " ON CTADEA.TASK_ID = TP1.TASK_ID "+
                            " AND CTADEA.APP_SEQ = TP1.APP_SEQ "+
                            " AND CTADEA.EMP_NO = TP1.EMP_NO "+
                            " AND (CTADEA.DEL_YN = 'N' or CTADEA.DEL_YN is null ) "+
                        " ORDER BY TP1.task_id, TP1.TASK_APP_DT, TP1.emp_no ";

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

    // 📌 특정 직원의 회차별 질문 및 상세 답변 내역 조회 API
    @GetMapping("/get-emp-detail-answers")
    public ResponseEntity<?> getEmpDetailAnswers(
            @RequestParam("task_id") int taskId,
            @RequestParam("app_seq") int appSeq,
            @RequestParam("emp_no") String empNo) {
        try {
            String query = "SELECT CEA.TASK_ID as task_id "+
                                " , CEA.APP_SEQ as app_seq "+
                                " , CQP.QSTN_NM AS qstn_nm " +
                                " , CQP.QSTN_CN AS qstn_cn " +
                                " , COALESCE(CEA.EMP_ANS_YN, 'N') AS emp_ans_yn " +
                                " , EMP.EMP_NO emp_no " +
                                " , EMP.EMP_NM emp_nm " +
                                " , EMP.IP ip " +
                            " FROM TB_COMP_EMP_ANS CEA, TB_COMP_QSTN_POOL CQP, TB_EMP EMP " + 
                            " WHERE CEA.TASK_ID = :taskId " +
                            "   AND CEA.APP_SEQ = :appSeq " +
                            "   AND CEA.EMP_NO = :empNo " +
                            "   AND CQP.QSTN_CD = CEA.QSTN_CD" +
                            "   AND CEA.EMP_NO = EMP.EMP_NO" +
                            " ORDER BY CEA.QSTN_CD ASC"; 

            MapSqlParameterSource params = new MapSqlParameterSource()
                    .addValue("taskId", taskId)
                    .addValue("appSeq", appSeq)
                    .addValue("empNo", empNo);

            List<Map<String, Object>> detailAnswers = jdbcTemplate.queryForList(query, params);
            
            return ResponseEntity.ok(detailAnswers);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("message", e.getMessage()));
        }
    }
}