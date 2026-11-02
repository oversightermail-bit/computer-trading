package com.hwprice.vo;

import lombok.Data;

import java.math.BigDecimal;

/**
 * 订阅套餐视图
 */
@Data
public class PlanVO {

    private Long id;

    /** 套餐名 */
    private String planName;

    /** 月付价格（元） */
    private BigDecimal priceMonth;

    /** 每日额度 */
    private Integer quotaDay;

    /** 每月额度 */
    private Integer quotaMonth;

    /** 是否支持图片解析 */
    private boolean multimodal;

    /** 权益描述 */
    private String description;
}
