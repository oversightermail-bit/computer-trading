package com.hwprice.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;

/**
 * 订阅等级与额度定义表 t_subscription_plan（运营可后台调整，无需发版）
 */
@Data
@TableName("t_subscription_plan")
public class SubscriptionPlan {

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 套餐名称：免费版 / 基础版 / 专业版 / 旗舰版 */
    private String planName;

    /** 月付价格（元） */
    private BigDecimal priceMonth;

    /** 每日 AI 额度（次） */
    private Integer quotaDay;

    /** 每月 AI 额度（次） */
    private Integer quotaMonth;

    /** 是否支持多模态（图片解析）：1=支持 0=不支持 */
    private Integer multimodal;

    /** 1=上架 0=下架 */
    private Integer status;

    /** 权益描述文案（升级弹窗展示） */
    private String description;

    /** 排序 */
    private Integer sortOrder;
}
