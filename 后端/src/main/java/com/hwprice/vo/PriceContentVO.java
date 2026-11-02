package com.hwprice.vo;

import lombok.Data;

/**
 * 硬件文案视图（价格波动页面 F3：功能作用 / 适用场景 / 易踩坑点）
 */
@Data
public class PriceContentVO {

    private String type;

    /** 硬件名称 */
    private String name;

    /** 功能作用解释 */
    private String func;

    /** 适用场景 */
    private String scene;

    /** 易踩坑点 */
    private String pitfall;
}
