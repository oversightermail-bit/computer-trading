package com.hwprice.vo;

import lombok.Data;

import java.math.BigDecimal;

/**
 * 首页硬件分类视图
 */
@Data
public class HardwareVO {

    /** 类型编码（跳转 /price?type=xxx） */
    private String type;

    /** 硬件名称 */
    private String name;

    /** 收录型号数量 */
    private long productCount;

    /** 当日最低价格（参考） */
    private BigDecimal minPrice;
}
