package com.legal.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class LawSummary {
    private String title;        // 法律名称
    private String lawType;      // 法律类型
    private String publishOrg;   // 发布机构
    private Long count;          // 法条数量
}
