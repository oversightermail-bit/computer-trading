package com.hwprice.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

/**
 * 商品/型号主数据表 t_product
 */
@Data
@TableName("t_product")
public class Product {

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 所属硬件类型，与 t_hardware.type 对应 */
    private String hardwareType;

    private String brand;

    private String model;

    /** 规格，如 12GB / DDR5 6000 / 1TB */
    private String spec;

    /** 性能分 1-100（人工维护，用于高性价比推荐：性价比指数 = 性能分 ÷ 价格） */
    private Integer perfScore;
}
