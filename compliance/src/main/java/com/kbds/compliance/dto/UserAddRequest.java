package com.kbds.compliance.dto;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class UserAddRequest {
    private String user_id;
    private String user_name;
    private String ip_address;
}