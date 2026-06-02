package com.kbds.compliance.dto;

import lombok.Getter;
import lombok.Setter;
import java.util.List;

@Getter
@Setter
public class SubmitComplianceRequest {
    private Long task_id;
    private Integer app_seq; // 회차 순번 필수 추가
    private String emp_no;   // user_id -> emp_no 변경
    private List<AnswerItem> answers;
}