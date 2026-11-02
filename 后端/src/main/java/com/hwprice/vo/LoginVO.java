package com.hwprice.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 登录响应
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class LoginVO {

    private String token;

    private String role;

    /** 当前套餐名（如 免费版） */
    private String plan;

    /** 剩余额度概览 */
    private QuotaVO quotaRemain;
}
