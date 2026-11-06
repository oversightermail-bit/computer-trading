package com.hwprice.pay;

import com.hwprice.entity.PayOrder;

import java.util.Map;

/**
 * 支付通道抽象：模拟支付与真实支付接口（支付宝/微信）共用一个流程入口，
 * 通过 app.subscribe.payment.channel 切换实现，其余下单/回调/激活流程不变。
 */
public interface PaymentChannel {

    /** 渠道标识：mock / alipay / wechat（与 app.subscribe.payment.channel 对应） */
    String name();

    /**
     * 生成支付参数（下单时调用）：
     * mock 渠道返回模拟收款码内容；真实渠道接入后返回预下单结果（二维码串/收银台地址）。
     */
    String createPay(PayOrder order);

    /** 支付异步回调验签（真实渠道接入后实现；mock 渠道恒真） */
    boolean verifyNotify(Map<String, String> params);
}
