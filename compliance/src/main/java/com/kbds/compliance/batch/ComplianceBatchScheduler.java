package com.kbds.compliance.batch;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * 📌 준법/자가점검 미동의자 자동 마감 배치
 *
 * 매일 자정 직후(00:10) 실행되어, '최근 7일(어제 포함)' 적용일이었던 항목에 대해
 * 아무런 응답 기록(TB_COMP_TASK_APP_DT_EMP_ANS)이 없는 대상자를
 * "미동의(N)" 상태로 자동 적재한다.
 *
 * - 처리 대상은 어제부터 7일 전까지로 범위를 넓혀서 매일 다시 확인한다.
 *   NOT EXISTS 조건으로 이미 기록이 있는 사람은 자동 제외되므로,
 *   같은 날짜를 여러 번 다시 훑어도 중복 INSERT 되지 않는다 (멱등성 보장).
 *   이 덕분에 특정 날짜에 배치가 실패하거나 서버가 잠시 내려가 있었어도
 *   다음 배치 실행 시 자동으로 복구(재처리)된다.
 * - 대상자 산정은 TB_EMP 의 "현재 활성(DEL_YN='N')" 기준으로만 처리한다.
 *   즉 배치 실행 시점에 이미 삭제(DEL_YN='Y')된 직원은 미동의 대상자 집계에서
 *   의도적으로 제외한다. (삭제된 직원은 더 이상 관리 대상이 아니므로 정책상 제외)
 * - EMP.REG_DTM(최초등록일시) <= 해당 TASK_APP_DT 조건으로,
 *   "그 적용일 당시에 이미 등록되어 있던 직원"만 대상으로 본다.
 *   조회 범위를 7일치로 넓혔기 때문에, 그 사이 새로 입사(등록)한 직원이
 *   과거 날짜의 미동의자로 잘못 집계되는 것을 방지한다.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class ComplianceBatchScheduler {

    private final NamedParameterJdbcTemplate jdbcTemplate;

    /**
     * 매일 00:10 에 실행.
     * cron = "초 분 시 일 월 요일"
     */
    @Scheduled(cron = "0 10 0 * * *")
    @Transactional
    public void closeUnansweredTasks() {
        log.info("===== [BATCH] 미동의자 자동 마감 배치 시작 =====");

        try {
            // 1. 마감 대상 적용일 조회: 최근 7일(어제 포함) 범위로 재확인
            //    - 같은 날짜를 매일 다시 훑지만, NOT EXISTS 조건으로 이미 처리된 사람은
            //      자동 제외되므로 중복 INSERT 되지 않는다 (멱등성 보장).
            //    - 이렇게 범위를 넓혀두면 특정 날짜에 배치가 실패하거나
            //      서버가 잠시 내려가 있었어도, 다음 실행 때 자동으로 복구(재처리)된다.
            String targetDtQuery =
                    "SELECT CTAD.TASK_ID AS task_id " +
                    "     , CTAD.APP_SEQ AS app_seq " +
                    "     , CTAD.TASK_APP_DT AS task_app_dt " +
                    "     , TASK.TASK_TYPE AS task_type " +
                    "  FROM TB_COMP_TASK_APP_DT CTAD " +
                    "  JOIN TB_COMP_TASK TASK ON TASK.TASK_ID = CTAD.TASK_ID " +
                    " WHERE CTAD.TASK_APP_DT BETWEEN CURRENT_DATE - INTERVAL '7 day' AND CURRENT_DATE - INTERVAL '1 day' " +
                    "   AND (CTAD.DEL_YN = 'N' OR CTAD.DEL_YN IS NULL) " +
                    "   AND (TASK.DEL_YN = 'N' OR TASK.DEL_YN IS NULL) ";

            List<Map<String, Object>> targets = jdbcTemplate.queryForList(
                    targetDtQuery, new MapSqlParameterSource());

            if (targets.isEmpty()) {
                log.info("===== [BATCH] 최근 7일 내 마감 대상 적용일이 없습니다. 종료합니다. =====");
                return;
            }

            LocalDateTime now = LocalDateTime.now();
            int totalInsertedMain = 0;
            int totalInsertedAns = 0;

            for (Map<String, Object> target : targets) {
                int taskId = (Integer) target.get("task_id");
                int appSeq = (Integer) target.get("app_seq");
                String taskType = (String) target.get("task_type");
                Object taskAppDt = target.get("task_app_dt");

                // 2. 해당 TASK/APP_SEQ 기준, "그 적용일 이전에 이미 등록되어 있던" 활성 직원 중
                //    TB_COMP_TASK_APP_DT_EMP_ANS 에 기록이 없는 사람만 추출.
                //    EMP.REG_DTM <= 적용일 조건으로, 적용일 이후에 새로 입사(등록)한 직원은
                //    그 날짜의 미동의 대상에서 제외한다. (당시에는 대상자가 아니었으므로)
                String unansweredEmpQuery =
                        "SELECT EMP.EMP_NO AS emp_no " +
                        "  FROM TB_EMP EMP " +
                        " WHERE (EMP.DEL_YN = 'N' OR EMP.DEL_YN IS NULL) " +
                        "   AND EMP.REG_DTM <= :taskAppDt " +
                        "   AND NOT EXISTS ( " +
                        "       SELECT 1 FROM TB_COMP_TASK_APP_DT_EMP_ANS CTADEA " +
                        "        WHERE CTADEA.TASK_ID = :taskId " +
                        "          AND CTADEA.APP_SEQ = :appSeq " +
                        "          AND CTADEA.EMP_NO = EMP.EMP_NO " +
                        "   ) ";

                MapSqlParameterSource empParams = new MapSqlParameterSource()
                        .addValue("taskId", taskId)
                        .addValue("appSeq", appSeq)
                        .addValue("taskAppDt", taskAppDt);

                List<Map<String, Object>> unansweredEmps =
                        jdbcTemplate.queryForList(unansweredEmpQuery, empParams);

                if (unansweredEmps.isEmpty()) {
                    continue;
                }

                // 3. 마스터(TB_COMP_TASK_APP_DT_EMP_ANS) 미동의 INSERT
                String insertMainQuery =
                        "INSERT INTO TB_COMP_TASK_APP_DT_EMP_ANS " +
                        "(TASK_ID, APP_SEQ, EMP_NO, EMP_MAIN_ANS_YN, EMP_ANS_AGR_YN, ANS_DT, DEL_YN, REG_EMP_NO) " +
                        "VALUES (:taskId, :appSeq, :empNo, 'N', 'N', :ansDt, 'N', 'BATCH')";

                // 4. 상세(TB_COMP_EMP_ANS) 미동의 INSERT
                //    - ETHICS 타입: 질문 매핑이 없으므로 'NONE' 코드로 1건만 적재
                //    - SELF_CHECK 타입: 해당 TASK에 매핑된 질문 전체에 대해 'N'으로 적재
                String taskQstnQuery =
                        "SELECT QSTN_CD FROM TB_COMP_TASK_QSTN " +
                        " WHERE TASK_ID = :taskId AND (DEL_YN = 'N' OR DEL_YN IS NULL)";
                List<Map<String, Object>> qstnCds = jdbcTemplate.queryForList(
                        taskQstnQuery, new MapSqlParameterSource("taskId", taskId));

                String insertAnsQuery =
                        "INSERT INTO TB_COMP_EMP_ANS " +
                        "(EMP_NO, TASK_ID, APP_SEQ, QSTN_CD, ANS_DT, EMP_ANS_YN, DEL_YN, REG_EMP_NO) " +
                        "VALUES (:empNo, :taskId, :appSeq, :qstnCd, :ansDt, 'N', 'N', 'BATCH')";

                for (Map<String, Object> empRow : unansweredEmps) {
                    String empNo = (String) empRow.get("emp_no");

                    MapSqlParameterSource mainParams = new MapSqlParameterSource()
                            .addValue("taskId", taskId)
                            .addValue("appSeq", appSeq)
                            .addValue("empNo", empNo)
                            .addValue("ansDt", now);
                    jdbcTemplate.update(insertMainQuery, mainParams);
                    totalInsertedMain++;

                    if ("ETHICS".equals(taskType) || qstnCds.isEmpty()) {
                        MapSqlParameterSource ansParams = new MapSqlParameterSource()
                                .addValue("empNo", empNo)
                                .addValue("taskId", taskId)
                                .addValue("appSeq", appSeq)
                                .addValue("qstnCd", "NONE")
                                .addValue("ansDt", now);
                        jdbcTemplate.update(insertAnsQuery, ansParams);
                        totalInsertedAns++;
                    } else {
                        for (Map<String, Object> qstnRow : qstnCds) {
                            String qstnCd = (String) qstnRow.get("QSTN_CD") != null
                                    ? (String) qstnRow.get("QSTN_CD")
                                    : (String) qstnRow.get("qstn_cd");
                            MapSqlParameterSource ansParams = new MapSqlParameterSource()
                                    .addValue("empNo", empNo)
                                    .addValue("taskId", taskId)
                                    .addValue("appSeq", appSeq)
                                    .addValue("qstnCd", qstnCd)
                                    .addValue("ansDt", now);
                            jdbcTemplate.update(insertAnsQuery, ansParams);
                            totalInsertedAns++;
                        }
                    }
                }

                log.info("[BATCH] TASK_ID={}, APP_SEQ={} → 미동의 처리 {}명",
                        taskId, appSeq, unansweredEmps.size());
            }

            log.info("===== [BATCH] 완료: 마스터 {}건, 상세 {}건 적재 =====",
                    totalInsertedMain, totalInsertedAns);

        } catch (Exception e) {
            log.error("===== [BATCH] 미동의자 자동 마감 배치 실패 =====", e);
            throw e;
        }
    }
}