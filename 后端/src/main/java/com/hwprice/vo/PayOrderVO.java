package com.hwprice.vo;

import lombok.Data;

import java.math.BigDecimal;

/**
 * 订阅支付单视图（下单接口返回）：
 * mock 渠道返回模拟收款码内容；真实渠道接入后返回收银台地址/二维码串。
 */
@Data
public class PayOrderVO {

    /** 业务订单号 */
    private String orderNo;

    /** 支付通道：mock / alipay / wechat */
    private String channel;

    /** 是否模拟支付（前端据此走"模拟支付确认"或弹付款码） */
    private boolean mock;

    /** 收款码内容（mock 渠道的模拟收款码 / 真实渠道的二维码串） */
    private String qrContent;

    /** 收银台地址（真实渠道接入后返回） */
    private String payUrl;

    private BigDecimal amount;

    private String planName;

    /** 0=待支付 1=已支付 */
    private Integer status;

    private String message;
}
