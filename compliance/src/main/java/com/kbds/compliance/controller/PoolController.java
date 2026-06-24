package com.kbds.compliance.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.List;
import java.util.Map;

import static com.kbds.compliance.controller.ApiResponseUtil.errorResponse;
import static com.kbds.compliance.controller.ApiResponseUtil.successResponse;

/**
 * 📌 질문 Pool(TB_COMP_QSTN_POOL) / 이미지 Pool(TB_COMP_IMG_POOL) 관리 API
 *  - 목록 조회는 기존 API 재사용:
 *      질문 목록 → GET /get-question-pool   (ComplianceTaskController)
 *      이미지 목록 → GET /get-img-pool        (ComplianceTaskController)
 *  - 이 컨트롤러는 등록/수정/삭제만 담당한다.
 *  - "이미 사용 중인 Pool"은 수정/삭제를 막는다.
 *      질문 사용 여부 판단: TB_COMP_TASK_QSTN 에 매핑 기록이 있는지
 *      이미지 사용 여부 판단: TB_COMP_TASK.IMG_FLNM 에서 참조되고 있는지
 */
@RestController
@RequiredArgsConstructor
public class PoolController {

    private final NamedParameterJdbcTemplate jdbcTemplate;

    // 실제 이미지 파일이 저장되는 서버 경로
    //  - WebConfig.java 의 addResourceHandlers 에서 "/images/**" 요청을
    //    이 경로로 매핑해서 서빙하고 있으므로, 반드시 이 경로와 동일하게 맞춰야 한다.
    //  - [개발환경] C:\Users\KBDS\Documents\images
    //  - [운영환경] /home/kbds/Documents/images/  (운영 반영 시 이 값으로 교체 필요)
    private static final String IMAGE_UPLOAD_DIR = "/home/kbds/Documents/images/";

    // ===================================================================
    // 질문 Pool (TB_COMP_QSTN_POOL)
    // ===================================================================

    // 📌 질문 신규 등록 API
    //  - QSTN_CD는 서버가 자동 채번 (Qnnn 형식, 현재 최대값 + 1)
    @PostMapping("/add-question")
    @Transactional
    public ResponseEntity<?> addQuestion(@RequestBody Map<String, String> payload) {
        try {
            String qstnNm = payload.get("qstn_nm");
            String qstnCn = payload.get("qstn_cn");
            String qstnType = payload.get("qstn_type"); // null 가능

            if (qstnNm == null || qstnNm.isBlank()) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse("질문명(qstn_nm)은 필수입니다."));
            }
            if (qstnCn == null || qstnCn.isBlank()) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse("질문내용(qstn_cn)은 필수입니다."));
            }

            // 현재 등록된 QSTN_CD 중 가장 큰 번호를 찾아 다음 번호로 채번 (Q001, Q002 ... 형식 가정)
            String maxCdQuery = "SELECT QSTN_CD FROM TB_COMP_QSTN_POOL " +
                                 "WHERE QSTN_CD ~ '^Q[0-9]+$' " +
                                 "ORDER BY CAST(SUBSTRING(QSTN_CD FROM 2) AS INTEGER) DESC LIMIT 1";
            List<Map<String, Object>> maxRows = jdbcTemplate.queryForList(maxCdQuery, new MapSqlParameterSource());

            int nextNum = 1;
            if (!maxRows.isEmpty()) {
                String maxCd = (String) maxRows.get(0).get("qstn_cd") != null
                        ? (String) maxRows.get(0).get("qstn_cd")
                        : (String) maxRows.get(0).get("QSTN_CD");
                nextNum = Integer.parseInt(maxCd.substring(1)) + 1;
            }
            String newCd = String.format("Q%03d", nextNum);

            String insertQuery = "INSERT INTO TB_COMP_QSTN_POOL (QSTN_CD, QSTN_NM, QSTN_TYPE, QSTN_CN, QSTN_STD_ANS_YN, DEL_YN, REG_EMP_NO) " +
                                  "VALUES (:qstnCd, :qstnNm, :qstnType, :qstnCn, 'Y', 'N', 'ADMIN')";
            MapSqlParameterSource params = new MapSqlParameterSource()
                    .addValue("qstnCd", newCd)
                    .addValue("qstnNm", qstnNm)
                    .addValue("qstnType", qstnType)
                    .addValue("qstnCn", qstnCn);
            jdbcTemplate.update(insertQuery, params);

            return ResponseEntity.status(HttpStatus.CREATED).body(Map.of(
                    "status", "success",
                    "message", "질문이 등록되었습니다.",
                    "qstn_cd", newCd
            ));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse(e.getMessage()));
        }
    }

    // 📌 질문 수정 API
    //  - 이미 TASK에 매핑되어 사용 중인 질문은 수정 불가
    @PostMapping("/update-question")
    @Transactional
    public ResponseEntity<?> updateQuestion(@RequestBody Map<String, String> payload) {
        try {
            String qstnCd = payload.get("qstn_cd");
            if (qstnCd == null || qstnCd.isBlank()) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse("qstn_cd는 필수입니다."));
            }

            if (isQuestionInUse(qstnCd)) {
                return ResponseEntity.status(HttpStatus.CONFLICT)
                        .body(errorResponse("이미 TASK에 사용 중인 질문은 수정할 수 없습니다."));
            }

            String updateQuery = "UPDATE TB_COMP_QSTN_POOL SET QSTN_NM = :qstnNm, QSTN_TYPE = :qstnType, " +
                                  "QSTN_CN = :qstnCn, CHG_DTM = now(), CHG_EMP_NO = 'ADMIN' " +
                                  "WHERE QSTN_CD = :qstnCd AND (DEL_YN = 'N' OR DEL_YN IS NULL)";
            MapSqlParameterSource params = new MapSqlParameterSource()
                    .addValue("qstnCd", qstnCd)
                    .addValue("qstnNm", payload.get("qstn_nm"))
                    .addValue("qstnType", payload.get("qstn_type"))
                    .addValue("qstnCn", payload.get("qstn_cn"));

            int updated = jdbcTemplate.update(updateQuery, params);
            if (updated == 0) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(errorResponse("해당 질문을 찾을 수 없습니다."));
            }

            return ResponseEntity.ok(successResponse("질문이 수정되었습니다."));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse(e.getMessage()));
        }
    }

    // 📌 질문 삭제 API (소프트 딜리트)
    //  - 이미 TASK에 매핑되어 사용 중인 질문은 삭제 불가
    @PostMapping("/delete-question")
    @Transactional
    public ResponseEntity<?> deleteQuestion(@RequestBody Map<String, String> payload) {
        try {
            String qstnCd = payload.get("qstn_cd");
            if (qstnCd == null || qstnCd.isBlank()) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse("qstn_cd는 필수입니다."));
            }

            if (isQuestionInUse(qstnCd)) {
                return ResponseEntity.status(HttpStatus.CONFLICT)
                        .body(errorResponse("이미 TASK에 사용 중인 질문은 삭제할 수 없습니다."));
            }

            String deleteQuery = "UPDATE TB_COMP_QSTN_POOL SET DEL_YN = 'Y', CHG_DTM = now(), CHG_EMP_NO = 'ADMIN' " +
                                  "WHERE QSTN_CD = :qstnCd";
            int updated = jdbcTemplate.update(deleteQuery, new MapSqlParameterSource("qstnCd", qstnCd));
            if (updated == 0) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(errorResponse("해당 질문을 찾을 수 없습니다."));
            }

            return ResponseEntity.ok(successResponse("질문이 삭제되었습니다."));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse(e.getMessage()));
        }
    }

    // 질문이 하나라도 TASK에 매핑되어 "사용 중"인지 확인하는 헬퍼
    //  - 삭제 여부(DEL_YN)와 무관하게, 매핑 기록 자체가 있으면 사용 중으로 판단한다.
    //    (TASK 쪽이 소프트 딜리트된 경우라도 과거에 사용된 적 있는 질문은 보존 차원에서 막는다)
    private boolean isQuestionInUse(String qstnCd) {
        String checkQuery = "SELECT COUNT(*) FROM TB_COMP_TASK_QSTN WHERE QSTN_CD = :qstnCd";
        int count = jdbcTemplate.queryForObject(checkQuery, new MapSqlParameterSource("qstnCd", qstnCd), Integer.class);
        return count > 0;
    }

    // ===================================================================
    // 이미지 Pool (TB_COMP_IMG_POOL)
    // ===================================================================

    // 📌 이미지 신규 등록 API (실제 파일 업로드 + DB 등록)
    @PostMapping("/upload-image")
    @Transactional
    public ResponseEntity<?> uploadImage(@RequestParam("file") MultipartFile file,
                                          @RequestParam(value = "img_type", required = false) String imgType) {
        try {
            if (file.isEmpty()) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse("업로드된 파일이 없습니다."));
            }

            String originalName = file.getOriginalFilename();
            if (originalName == null || originalName.isBlank()) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse("파일명을 확인할 수 없습니다."));
            }

            // 동일 파일명이 이미 Pool에 등록되어 있는지 확인 (활성 상태 기준)
            String checkQuery = "SELECT IMG_ID FROM TB_COMP_IMG_POOL WHERE IMG_FLNM = :imgFlnm AND (DEL_YN = 'N' OR DEL_YN IS NULL)";
            List<Map<String, Object>> existing = jdbcTemplate.queryForList(checkQuery, new MapSqlParameterSource("imgFlnm", originalName));
            if (!existing.isEmpty()) {
                return ResponseEntity.status(HttpStatus.CONFLICT).body(errorResponse("이미 등록된 파일명입니다: " + originalName));
            }

            // 1. 실제 파일을 서버 정적 리소스 폴더에 저장
            Path uploadPath = Paths.get(IMAGE_UPLOAD_DIR);
            Files.createDirectories(uploadPath);
            Path targetPath = uploadPath.resolve(originalName);
            Files.copy(file.getInputStream(), targetPath, StandardCopyOption.REPLACE_EXISTING);

            // 2. DB(TB_COMP_IMG_POOL)에 파일명 등록
            String insertQuery = "INSERT INTO TB_COMP_IMG_POOL (IMG_FLNM, IMG_TYPE, DEL_YN, REG_EMP_NO) " +
                                  "VALUES (:imgFlnm, :imgType, 'N', 'ADMIN')";
            MapSqlParameterSource params = new MapSqlParameterSource()
                    .addValue("imgFlnm", originalName)
                    .addValue("imgType", imgType);
            jdbcTemplate.update(insertQuery, params);

            return ResponseEntity.status(HttpStatus.CREATED).body(Map.of(
                    "status", "success",
                    "message", "이미지가 등록되었습니다.",
                    "img_flnm", originalName
            ));
        } catch (IOException e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse("파일 저장 중 오류: " + e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse(e.getMessage()));
        }
    }

    // 📌 이미지 삭제 API (소프트 딜리트, 실제 파일은 보존)
    //  - 이미 TASK에서 참조 중인 이미지(IMG_FLNM)는 삭제 불가
    //  - 실제 파일은 지우지 않고 DB 등록만 비활성화 처리한다.
    //    (과거 TASK 기록에서 이미지가 깨져 보이지 않도록 파일 자체는 보존)
    @PostMapping("/delete-image")
    @Transactional
    public ResponseEntity<?> deleteImage(@RequestBody Map<String, String> payload) {
        try {
            String imgFlnm = payload.get("img_flnm");
            if (imgFlnm == null || imgFlnm.isBlank()) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse("img_flnm은 필수입니다."));
            }

            if (isImageInUse(imgFlnm)) {
                return ResponseEntity.status(HttpStatus.CONFLICT)
                        .body(errorResponse("이미 TASK에 사용 중인 이미지는 삭제할 수 없습니다."));
            }

            String deleteQuery = "UPDATE TB_COMP_IMG_POOL SET DEL_YN = 'Y', CHG_DTM = now(), CHG_EMP_NO = 'ADMIN' " +
                                  "WHERE IMG_FLNM = :imgFlnm";
            int updated = jdbcTemplate.update(deleteQuery, new MapSqlParameterSource("imgFlnm", imgFlnm));
            if (updated == 0) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(errorResponse("해당 이미지를 찾을 수 없습니다."));
            }

            return ResponseEntity.ok(successResponse("이미지가 삭제되었습니다."));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse(e.getMessage()));
        }
    }

    // 이미지가 TASK에서 참조되어 "사용 중"인지 확인하는 헬퍼
    //  - TB_COMP_TASK.IMG_FLNM 에 같은 파일명이 있으면 사용 중으로 판단한다.
    private boolean isImageInUse(String imgFlnm) {
        String checkQuery = "SELECT COUNT(*) FROM TB_COMP_TASK WHERE IMG_FLNM = :imgFlnm";
        int count = jdbcTemplate.queryForObject(checkQuery, new MapSqlParameterSource("imgFlnm", imgFlnm), Integer.class);
        return count > 0;
    }
}
