package com.hwprice.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 订阅支付单 t_pay_order（支付模块：模拟支付 + 可切换真实接口）。
 * <ul>
 *   <li>status：0=待支付，1=已支付，2=已关闭；</li>
 *   <li>channel：mock=模拟支付（比赛演示）/ alipay / wechat（真实接口预留）；</li>
 *   <li>pay_params：支付参数，mock 渠道存模拟收款码内容，真实渠道存预下单返回串。</li>
 * </ul>
 */
@Data
@TableName("t_pay_order")
public class PayOrder {

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 业务订单号（对外展示/回调定位） */
    private String orderNo;

    private Long userId;

    private Long planId;

    /** 套餐名快照 */
    private String planName;

    /** 应付金额（元） */
    private BigDecimal amount;

    /** 支付通道：mock / alipay / wechat */
    private String channel;

    /** 0=待支付 1=已支付 2=已关闭 */
    private Integer status;

    /** 支付参数（mock：模拟收款码内容；真实：预下单返回串） */
    private String payParams;

    private LocalDateTime createTime;

    private LocalDateTime payTime;
}
