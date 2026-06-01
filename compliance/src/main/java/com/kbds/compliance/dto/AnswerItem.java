package com.kbds.compliance.dto;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class AnswerItem {
    private Integer q_id; // Optional 대신 Null 허용 객체 타입 사용
    private String txt;
    private String ans;
}