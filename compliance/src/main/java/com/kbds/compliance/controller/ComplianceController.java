package com.kbds.compliance.controller;

import com.kbds.compliance.dto.*;
import lombok.RequiredArgsConstructor;
import tools.jackson.databind.ObjectMapper;
import org.postgresql.util.PGobject;
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
    private final ObjectMapper objectMapper; // JSON 직렬화용

    // 공통 에러 응답 맵 생성기
    private Map<String, String> errorResponse(String message) {
        Map<String, String> response = new HashMap<>();
        response.put("status", "error");
        response.put("message", message);
        return response;
    }

    // 공통 성공 응답 맵 생성기
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
            // [검증 1] 유효한 점검 항목(Task)인지 확인
            String taskQuery = "SELECT task_id, task_type, start_date, end_date FROM compliance_tasks WHERE task_id = :taskId AND is_published = true";
            MapSqlParameterSource params = new MapSqlParameterSource("taskId", data.getTask_id());
            List<Map<String, Object>> tasks = jdbcTemplate.queryForList(taskQuery, params);

            if (tasks.isEmpty()) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(errorResponse("활성화된 준법 항목을 찾을 수 없습니다."));
            }
            Map<String, Object> task = tasks.get(0);

            // [검증 2] 점검 기간 유효성 체크
            LocalDateTime now = LocalDateTime.now();
            LocalDateTime startDate = ((java.sql.Timestamp) task.get("start_date")).toLocalDateTime();
            LocalDateTime endDate = ((java.sql.Timestamp) task.get("end_date")).toLocalDateTime();

            if (now.isBefore(startDate) || now.isAfter(endDate)) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse("현재 점검 기간이 아닙니다."));
            }

            // [검증 3] 등록된 마스터 사용자인지 파악
            String userQuery = "SELECT user_id FROM users WHERE user_id = :userId AND is_active = true";
            MapSqlParameterSource userParams = new MapSqlParameterSource("userId", data.getUser_id());
            List<Map<String, Object>> users = jdbcTemplate.queryForList(userQuery, userParams);

            if (users.isEmpty()) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(errorResponse("준법 관리 대상 사용자가 아니거나 찾을 수 없습니다."));
            }

            // [검증 4] 중복 제출 방지
            String logCheckQuery = "SELECT log_id FROM compliance_logs WHERE task_id = :taskId AND user_id = :userId AND is_completed = true";
            MapSqlParameterSource logParams = new MapSqlParameterSource()
                    .addValue("taskId", data.getTask_id())
                    .addValue("userId", data.getUser_id());
            List<Map<String, Object>> logs = jdbcTemplate.queryForList(logCheckQuery, logParams);

            if (!logs.isEmpty()) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse("이미 제출을 완료한 항목입니다."));
            }

            // Pydantic 객체 배열 -> JSONB 대응을 위한 PGobject 설정
            String jsonAnswers = objectMapper.writeValueAsString(data.getAnswers());
            PGobject jsonbObject = new PGobject();
            jsonbObject.setType("jsonb");
            jsonbObject.setValue(jsonAnswers);

            // [핵심] 로그 테이블에 증적 적재
            String insertQuery = "INSERT INTO compliance_logs (task_id, user_id, client_ip, is_completed, answers, completed_at) " +
                    "VALUES (:taskId, :userId, :clientIp, true, :answers, :completedAt)";
            MapSqlParameterSource insertParams = new MapSqlParameterSource()
                    .addValue("taskId", data.getTask_id())
                    .addValue("userId", data.getUser_id())
                    .addValue("clientIp", data.getClient_ip())
                    .addValue("answers", jsonbObject)
                    .addValue("completedAt", now);

            jdbcTemplate.update(insertQuery, insertParams);

            return ResponseEntity.ok(successResponse("준법 프로그램 수행 기록이 정상적으로 저장되었습니다."));

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse(e.getMessage()));
        }
    }

    // 📌 2. 전체 서약/수행 완료 로그 조회 API (관리자 뷰어용)
    @GetMapping("/get-all-logs")
    public ResponseEntity<?> getAllLogs(@RequestParam(value = "task_title", required = false) String taskTitle) {
        try {
            String query;
            MapSqlParameterSource params = new MapSqlParameterSource();
            
            if (taskTitle == null || "등록된 준법 항목이 없습니다.".equals(taskTitle)) {
                query = "SELECT user_id, user_name, ip_address AS client_ip, " +
                        "false AS is_completed, NULL AS completed_at, '선택 없음' AS task_title " +
                        "FROM users WHERE is_active = true ORDER BY user_name ASC";
            } else {
                query = "SELECT u.user_id, u.user_name, COALESCE(l.client_ip, u.ip_address) AS client_ip, " +
                        "CASE " +
                        "    WHEN t.recurrence_type = 'DAILY'   AND l.completed_at >= NOW() - INTERVAL '1 day'   THEN true " +
                        "    WHEN t.recurrence_type = 'WEEKLY'  AND l.completed_at >= NOW() - INTERVAL '7 days'  THEN true " +
                        "    WHEN t.recurrence_type = 'MONTHLY' AND l.completed_at >= NOW() - INTERVAL '30 days' THEN true " +
                        "    WHEN t.recurrence_type = 'ONCE'    AND l.completed_at IS NOT NULL                    THEN true " +
                        "    ELSE false " +
                        "END AS is_completed, " +
                        "l.completed_at, t.title AS task_title " +
                        "FROM users u " +
                        "CROSS JOIN (SELECT task_id, title, recurrence_type FROM compliance_tasks WHERE title = :taskTitle) t " +
                        "LEFT JOIN compliance_logs l ON u.user_id = l.user_id AND t.task_id = l.task_id " +
                        "WHERE u.is_active = true " +
                        "ORDER BY u.user_name ASC";
                params.addValue("taskTitle", taskTitle);
            }

            List<Map<String, Object>> rows = jdbcTemplate.queryForList(query, params);
            List<Map<String, Object>> result = new ArrayList<>();
            DateTimeFormatter formatter = DateTimeFormatter.ofPattern("Y-m-d H:i:s");

            // 날짜 포맷 가공 파이프라인
            for (Map<String, Object> row : rows) {
                Map<String, Object> rowMap = new LinkedHashMap<>(row); // 순서 유지를 위한 빈 맵 생성
                if (rowMap.get("completed_at") != null) {
                    LocalDateTime completedAt = ((java.sql.Timestamp) rowMap.get("completed_at")).toLocalDateTime();
                    rowMap.put("completed_at", completedAt.format(formatter));
                } else {
                    rowMap.put("completed_at", "-");
                }
                result.add(rowMap);
            }

            return ResponseEntity.ok(result);

        } catch (Exception e) {
            throw e;
            //return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse(e.getMessage()));
        }
    }

    // 📌 3. 대상 사원 추가 API (사용자 마스터 동기화)
    @PostMapping("/add-user")
    @Transactional
    public ResponseEntity<?> addUser(@RequestBody UserAddRequest data) {
        try {
            String checkQuery = "SELECT user_id FROM users WHERE user_id = :userId";
            MapSqlParameterSource params = new MapSqlParameterSource("userId", data.getUser_id());
            List<Map<String, Object>> users = jdbcTemplate.queryForList(checkQuery, params);

            if (!users.isEmpty()) {
                return ResponseEntity.status(HttpStatus.CONFLICT).body(errorResponse("이미 등록된 사번입니다."));
            }

            String insertQuery = "INSERT INTO users (user_id, user_name, ip_address, is_active) VALUES (:userId, :userName, :ipAddress, true)";
            MapSqlParameterSource insertParams = new MapSqlParameterSource()
                    .addValue("userId", data.getUser_id())
                    .addValue("userName", data.getUser_name())
                    .addValue("ipAddress", data.getIp_address());

            jdbcTemplate.update(insertQuery, insertParams);

            return ResponseEntity.status(HttpStatus.CREATED).body(successResponse(data.getUser_name() + " 사원이 관리 마스터에 유입되었습니다."));

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse(e.getMessage()));
        }
    }

    // 📌 4. 대상 사원 다중 삭제 API (인사 이동 대응용)
    @PostMapping("/delete-users")
    @Transactional
    public ResponseEntity<?> deleteUsers(@RequestBody UserDeleteRequest data) {
        try {
            if (data.getUser_ids() == null || data.getUser_ids().isEmpty()) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse("삭제할 사번 리스트가 누락되었습니다."));
            }

            // Java의 IN 절 처리는 List 객체를 파라미터로 그대로 넘기면 됩니다.
            String deleteQuery = "DELETE FROM users WHERE user_id IN (:userIds)";
            MapSqlParameterSource params = new MapSqlParameterSource("userIds", data.getUser_ids());
            
            int deletedCount = jdbcTemplate.update(deleteQuery, params);

            if (deletedCount == 0) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(errorResponse("삭제 대상 사용자를 찾을 수 없습니다."));
            }

            return ResponseEntity.ok(successResponse("총 " + deletedCount + "명의 대상자가 명단에서 제외되었습니다."));

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse(e.getMessage()));
        }
    }

    // 📌 5. 준법 항목 목록 조회 API
    @GetMapping("/get-compliance-items")
    public ResponseEntity<?> getComplianceItems() {
        try {
            String query = "SELECT title FROM compliance_tasks ORDER BY task_id DESC";
            List<String> complianceList = jdbcTemplate.queryForList(query, new MapSqlParameterSource(), String.class);

            // 데이터가 없을 경우 빈 배열 반환
            if (complianceList.isEmpty()) {
                return ResponseEntity.ok(new ArrayList<>());
            }

            return ResponseEntity.ok(complianceList);

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse(e.getMessage()));
        }
    }
}