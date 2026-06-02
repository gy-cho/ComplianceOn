package com.kbds.compliance.dto;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class EmployeeAddRequest {
    private String emp_no;
    private String emp_nm;
    private String ip;
}