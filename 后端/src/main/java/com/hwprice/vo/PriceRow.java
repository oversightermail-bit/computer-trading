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

    private String platform;

    private BigDecimal price;

    private LocalDate date;
}
