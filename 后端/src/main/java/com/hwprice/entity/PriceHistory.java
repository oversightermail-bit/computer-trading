package com.hwprice.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 价格时序表 t_price_history（爬虫子系统写入，后端只读聚合）
 */
@Data
@TableName("t_price_history")
public class PriceHistory {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long productId;

    /** 数据源：中关村在线（ZOL）等 */
    private String platform;

    private BigDecimal price;

    /** 采集日期 */
    private LocalDate date;
}
