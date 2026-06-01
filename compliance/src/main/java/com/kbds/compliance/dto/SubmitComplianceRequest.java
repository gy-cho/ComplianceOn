package com.kbds.compliance.dto;

import lombok.Getter;
import lombok.Setter;
import java.util.List;

@Getter
@Setter
public class SubmitComplianceRequest {
    private Long task_id;
    private String user_id;
    private String client_ip;
    private List<AnswerItem> answers;
}