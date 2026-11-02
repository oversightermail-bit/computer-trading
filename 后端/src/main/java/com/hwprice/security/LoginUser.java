package com.hwprice.security;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 登录用户主体（挂在 SecurityContext 上）。
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class LoginUser {

    private Long userId;
    private String username;
    /** 用户角色：USER（管理员可扩展 ADMIN） */
    private String role;
}
