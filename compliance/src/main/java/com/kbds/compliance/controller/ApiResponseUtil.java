package com.kbds.compliance.controller;

import java.util.HashMap;
import java.util.Map;

/**
 * 📌 공통 API 응답 포맷 유틸리티
 *  - 기존 ComplianceController 에 있던 errorResponse / successResponse 를
 *    여러 컨트롤러에서 공통으로 재사용할 수 있도록 분리.
 */
public class ApiResponseUtil {

    public static Map<String, String> errorResponse(String message) {
        Map<String, String> response = new HashMap<>();
        response.put("status", "error");
        response.put("message", message);
        return response;
    }

    public static Map<String, String> successResponse(String message) {
        Map<String, String> response = new HashMap<>();
        response.put("status", "success");
        response.put("message", message);
        return response;
    }
}