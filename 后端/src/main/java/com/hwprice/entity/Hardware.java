package com.hwprice.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

/**
 * 硬件类目与文案表 t_hardware
 */
@Data
@TableName("t_hardware")
public class Hardware {

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 硬件类型编码（前端跳转参数），如 cpu / gpu / keyboard */
    private String type;

    /** 硬件名称，如 CPU（台式机） */
    private String name;

    /** 功能作用解释 */
    private String funcDesc;

    /** 适用场景 */
    private String scene;

    /** 易踩坑点 */
    private String pitfall;

    /** 首页排序 */
    private Integer sortOrder;
}
