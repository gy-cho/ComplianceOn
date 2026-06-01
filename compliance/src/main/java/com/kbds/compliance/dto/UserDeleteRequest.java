package com.kbds.compliance.dto;

import lombok.Getter;
import lombok.Setter;
import java.util.List;

@Getter
@Setter
public class UserDeleteRequest {
    private List<String> user_ids;
}