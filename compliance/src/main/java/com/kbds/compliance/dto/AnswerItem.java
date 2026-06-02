package com.kbds.compliance.dto;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class AnswerItem {
    private String qstn_cd;    // TB_COMP_QSTN_POOL 코드 참조
    private String emp_ans_yn; // 완료 여부 ('Y', 'N')
}