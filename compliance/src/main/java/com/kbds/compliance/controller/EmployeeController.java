package com.kbds.compliance.controller;

import com.kbds.compliance.dto.*;
import lombok.RequiredArgsConstructor;
import org.apache.poi.ss.usermodel.Cell;
import org.apache.poi.ss.usermodel.Row;
import org.apache.poi.ss.usermodel.Sheet;
import org.apache.poi.ss.usermodel.Workbook;
import org.apache.poi.ss.usermodel.WorkbookFactory;
import org.springframework.core.io.ClassPathResource;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.*;

import static com.kbds.compliance.controller.ApiResponseUtil.errorResponse;
import static com.kbds.compliance.controller.ApiResponseUtil.successResponse;

/**
 * 📌 직원(TB_EMP) 관리 관련 API
 *  - 조회 / 단건 등록 / 엑셀 일괄등록 / 양식 다운로드 / 다중 삭제
 *  - 기존 ComplianceController 에서 분리된 부분
 */
@RestController
@RequiredArgsConstructor
public class EmployeeController {

    private final NamedParameterJdbcTemplate jdbcTemplate;

    // 📌 모든 직원 목록 조회 API (직원 관리 및 대시보드 연동 규격)
    @GetMapping("/get-all-employees")
    public ResponseEntity<?> getAllEmployees() {
        try {
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

    // 📌 대상 사원 추가 API (사원 마스터 테이블 반영)
    @PostMapping("/add-employee")
    @Transactional
    public ResponseEntity<?> addEmployee(@RequestBody EmployeeAddRequest data) {
        try {
            String checkQuery = "SELECT EMP_NO FROM TB_EMP WHERE EMP_NO = :empNo AND DEL_YN = 'N'";
            MapSqlParameterSource params = new MapSqlParameterSource("empNo", data.getEmp_no());
            List<Map<String, Object>> employees = jdbcTemplate.queryForList(checkQuery, params);

            if (!employees.isEmpty()) {
                return ResponseEntity.status(HttpStatus.CONFLICT).body(errorResponse("이미 등록된 사번입니다."));
            }

            MapSqlParameterSource insertParams = new MapSqlParameterSource()
                    .addValue("empNo", data.getEmp_no())
                    .addValue("empNm", data.getEmp_nm())
                    .addValue("ip", data.getIp());

            String existQuery = "SELECT EMP_NO FROM TB_EMP WHERE EMP_NO = :empNo";
            List<Map<String, Object>> existing = jdbcTemplate.queryForList(existQuery, params);

            if (!existing.isEmpty()) {
                String restoreQuery = "UPDATE TB_EMP SET EMP_NM = :empNm, IP = :ip, DEL_YN = 'N', CHG_DTM = now() " +
                                    "WHERE EMP_NO = :empNo";
                jdbcTemplate.update(restoreQuery, insertParams);
            } else {
                String insertQuery = "INSERT INTO TB_EMP (EMP_NO, EMP_NM, IP, DEL_YN, REG_EMP_NO) " +
                                    "VALUES (:empNo, :empNm, :ip, 'N', 'ADMIN')";
                jdbcTemplate.update(insertQuery, insertParams);
            }

            return ResponseEntity.status(HttpStatus.CREATED).body(successResponse(data.getEmp_nm() + " 사원이 관리 마스터에 유입되었습니다."));

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse(e.getMessage()));
        }
    }

    // 📌 직원 일괄등록용 엑셀 양식 다운로드 API
    @GetMapping("/download-employee-template")
    public ResponseEntity<?> downloadEmployeeTemplate() {
        try {
            Resource resource = new ClassPathResource("static/templates/employee_upload_template.xlsx");
            if (!resource.exists()) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(errorResponse("양식 파일을 찾을 수 없습니다."));
            }

            String downloadName = "직원_일괄등록_양식.xlsx";
            String encodedName = URLEncoder.encode(downloadName, StandardCharsets.UTF_8).replace("+", "%20");

            return ResponseEntity.ok()
                    .contentType(MediaType.parseMediaType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))
                    .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + encodedName + "\"; filename*=UTF-8''" + encodedName)
                    .body(resource);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse(e.getMessage()));
        }
    }

    // 📌 엑셀 파일을 통한 직원 일괄 등록 API
    @PostMapping("/upload-employees")
    @Transactional
    public ResponseEntity<?> uploadEmployees(@RequestParam("file") MultipartFile file) {
        if (file.isEmpty()) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse("업로드된 파일이 없습니다."));
        }

        List<Map<String, Object>> rows = new ArrayList<>();
        List<String> errors = new ArrayList<>();

        try (Workbook workbook = WorkbookFactory.create(file.getInputStream())) {
            Sheet sheet = workbook.getSheetAt(0);

            Row headerRow = sheet.getRow(0);
            if (headerRow == null) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse("엑셀 헤더(1행)가 비어있습니다."));
            }

            int empNoCol = -1, empNmCol = -1, ipCol = -1;
            for (Cell cell : headerRow) {
                String header = getCellString(cell).trim();
                if (header.contains("사번") || header.equalsIgnoreCase("EMP_NO")) {
                    empNoCol = cell.getColumnIndex();
                } else if (header.contains("이름") || header.contains("성명") || header.equalsIgnoreCase("EMP_NM")) {
                    empNmCol = cell.getColumnIndex();
                } else if (header.equalsIgnoreCase("IP") || header.contains("아이피")) {
                    ipCol = cell.getColumnIndex();
                }
            }

            if (empNoCol == -1 || empNmCol == -1 || ipCol == -1) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                        .body(errorResponse("엑셀 헤더에서 '사번', '이름', 'IP' 컬럼을 찾을 수 없습니다."));
            }

            int lastRow = sheet.getLastRowNum();
            Set<String> empNoSetInFile = new HashSet<>();

            for (int r = 1; r <= lastRow; r++) {
                Row row = sheet.getRow(r);
                if (row == null) continue;

                String empNo = getCellString(row.getCell(empNoCol)).trim();
                String empNm = getCellString(row.getCell(empNmCol)).trim();
                String ip = getCellString(row.getCell(ipCol)).trim();

                if (empNo.isEmpty() && empNm.isEmpty() && ip.isEmpty()) {
                    continue;
                }

                int excelRowNum = r + 1;

                if (empNo.isEmpty()) {
                    errors.add(excelRowNum + "행: 사번이 비어있습니다.");
                    continue;
                }
                if (empNm.isEmpty()) {
                    errors.add(excelRowNum + "행: 이름이 비어있습니다.");
                    continue;
                }
                if (ip.isEmpty()) {
                    errors.add(excelRowNum + "행: IP가 비어있습니다.");
                    continue;
                }

                if (empNo.length() > 10) {
                    errors.add(excelRowNum + "행: 사번 [" + empNo + "] 이 10자를 초과합니다. (현재 " + empNo.length() + "자)");
                    continue;
                }
                if (empNm.length() > 50) {
                    errors.add(excelRowNum + "행: 이름 [" + empNm + "] 이 50자를 초과합니다. (현재 " + empNm.length() + "자)");
                    continue;
                }
                if (ip.length() > 20) {
                    errors.add(excelRowNum + "행: IP [" + ip + "] 가 20자를 초과합니다. (현재 " + ip.length() + "자)");
                    continue;
                }

                if (!empNoSetInFile.add(empNo)) {
                    errors.add(excelRowNum + "행: 사번 [" + empNo + "] 이 엑셀 내에서 중복되었습니다.");
                    continue;
                }

                Map<String, Object> rowData = new HashMap<>();
                rowData.put("rowNum", excelRowNum);
                rowData.put("empNo", empNo);
                rowData.put("empNm", empNm);
                rowData.put("ip", ip);
                rows.add(rowData);
            }

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(errorResponse("엑셀 파일을 읽는 중 오류가 발생했습니다: " + e.getMessage()));
        }

        if (!rows.isEmpty()) {
            String checkQuery = "SELECT EMP_NO FROM TB_EMP WHERE DEL_YN = 'N' AND EMP_NO IN (:empNos)";
            List<String> empNosToCheck = rows.stream()
                    .map(r -> (String) r.get("empNo"))
                    .toList();
            MapSqlParameterSource checkParams = new MapSqlParameterSource("empNos", empNosToCheck);
            List<Map<String, Object>> existingActive = jdbcTemplate.queryForList(checkQuery, checkParams);
            Set<String> existingActiveSet = new HashSet<>();
            for (Map<String, Object> row : existingActive) {
                existingActiveSet.add((String) row.get("EMP_NO") != null
                        ? (String) row.get("EMP_NO") : (String) row.get("emp_no"));
            }

            for (Map<String, Object> row : rows) {
                String empNo = (String) row.get("empNo");
                if (existingActiveSet.contains(empNo)) {
                    errors.add(row.get("rowNum") + "행: 사번 [" + empNo + "] 은 이미 등록된 사번입니다.");
                }
            }
        }

        if (!errors.isEmpty()) {
            return ResponseEntity.status(HttpStatus.CONFLICT)
                    .body(Map.of(
                            "status", "fail",
                            "message", "엑셀 검증 중 오류가 발견되어 전체 등록이 취소되었습니다.",
                            "errors", errors
                    ));
        }

        if (rows.isEmpty()) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse("등록할 데이터가 없습니다."));
        }

        String existQuery = "SELECT EMP_NO FROM TB_EMP WHERE EMP_NO = :empNo";
        String restoreQuery = "UPDATE TB_EMP SET EMP_NM = :empNm, IP = :ip, DEL_YN = 'N', CHG_DTM = now() WHERE EMP_NO = :empNo";
        String insertQuery = "INSERT INTO TB_EMP (EMP_NO, EMP_NM, IP, DEL_YN, REG_EMP_NO) " +
                              "VALUES (:empNo, :empNm, :ip, 'N', 'ADMIN')";

        int insertedCount = 0;
        int restoredCount = 0;

        try {
            for (Map<String, Object> row : rows) {
                String empNo = (String) row.get("empNo");
                String empNm = (String) row.get("empNm");
                String ip = (String) row.get("ip");

                MapSqlParameterSource params = new MapSqlParameterSource()
                        .addValue("empNo", empNo)
                        .addValue("empNm", empNm)
                        .addValue("ip", ip);

                List<Map<String, Object>> existing = jdbcTemplate.queryForList(
                        existQuery, new MapSqlParameterSource("empNo", empNo));

                if (!existing.isEmpty()) {
                    jdbcTemplate.update(restoreQuery, params);
                    restoredCount++;
                } else {
                    jdbcTemplate.update(insertQuery, params);
                    insertedCount++;
                }
            }
        } catch (Exception e) {
            throw new RuntimeException("직원 등록 처리 중 오류가 발생하여 전체 등록이 취소되었습니다. 원인: " + e.getMessage(), e);
        }

        return ResponseEntity.status(HttpStatus.CREATED).body(Map.of(
                "status", "success",
                "message", "총 " + rows.size() + "명 등록 완료 (신규 " + insertedCount + "명, 복원 " + restoredCount + "명)",
                "totalCount", rows.size(),
                "insertedCount", insertedCount,
                "restoredCount", restoredCount
        ));
    }

    private String getCellString(Cell cell) {
        if (cell == null) return "";
        switch (cell.getCellType()) {
            case STRING:
                return cell.getStringCellValue();
            case NUMERIC:
                double num = cell.getNumericCellValue();
                if (num == Math.floor(num) && !Double.isInfinite(num)) {
                    return String.valueOf((long) num);
                }
                return String.valueOf(num);
            case BOOLEAN:
                return String.valueOf(cell.getBooleanCellValue());
            case FORMULA:
                try {
                    return cell.getStringCellValue();
                } catch (Exception e) {
                    return String.valueOf(cell.getNumericCellValue());
                }
            default:
                return "";
        }
    }

    // 📌 대상 사원 다중 삭제 API (소프트 딜리트 변경)
    @PostMapping("/delete-employees")
    @Transactional
    public ResponseEntity<?> deleteEmployees(@RequestBody EmployeeDeleteRequest data) {
        try {
            if (data.getEmp_nos() == null || data.getEmp_nos().isEmpty()) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse("삭제할 사번 리스트가 누락되었습니다."));
            }

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
}