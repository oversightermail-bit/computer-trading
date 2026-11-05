package com.hwprice.dto;

import lombok.Data;

/**
 * 管理员修改用户请求：role（USER/ADMIN）与 password 至少一项
 */
@Data
public class AdminUserUpdateReq {

    private String role;

    private String password;
}
