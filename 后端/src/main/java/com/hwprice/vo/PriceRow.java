package com.hwprice.vo;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 价格行（t_price_history 与 t_product 的联表结果，供聚合计算）
 */
@Data
public class PriceRow {

    private Long productId;

    private String hardwareType;

    private String brand;

    private String model;

    private String spec;

    /** 性能分 1-100（来自 t_product.perf_score，基准自动映射，用于高性价比推荐） */
    private Integer perfScore;

    /** 性能分依据（基准数值与公式） */
    private String perfBasis;

    /** 性能分更新日期 */
    private LocalDate perfUpdated;

    private String platform;

    private BigDecimal price;

    private LocalDate date;
}
