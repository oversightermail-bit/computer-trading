package com.hwprice.vo;

import lombok.Data;

import java.time.LocalDateTime;

/**
 * 管理页用户列表项
 */
@Data
public class AdminUserVO {

    private Long id;

    private String username;

    /** USER / ADMIN */
    private String role;

    /** 当前套餐名（如 免费版） */
    private String plan;

    private LocalDateTime createTime;
}
