package com.hwprice.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 二手硬件交易表 t_trade（本期暂不开发，仅预留表结构与实体，
 * 供后续迭代直接启用而无需数据迁移）
 */
@Data
@TableName("t_trade")
public class Trade {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long userId;

    /** 硬件类型，复用 t_hardware.type */
    private String hardwareType;

    private String title;

    private BigDecimal price;

    /** 0=待售 1=已售 2=下架 */
    private Integer status;

    private LocalDateTime createTime;
}
