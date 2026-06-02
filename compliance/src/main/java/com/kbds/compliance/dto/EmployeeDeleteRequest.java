package com.kbds.compliance.dto;

import lombok.Getter;
import lombok.Setter;
import java.util.List;

@Getter
@Setter
public class EmployeeDeleteRequest {
    private List<String> emp_nos;
}