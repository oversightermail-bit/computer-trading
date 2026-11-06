package com.hwprice.pay;

import com.hwprice.common.BizException;
import com.hwprice.common.ErrorCode;
import com.hwprice.config.AppProperties;
import com.hwprice.entity.PayOrder;
import org.springframework.stereotype.Component;

import java.util.Map;

/**
 * 微信支付通道（真实接口预留）：
 * 营业执照办理后接入「Native 支付」，参数取 app.subscribe.payment.wechat-*。
 * 未接入前下单直接返回"功能开发中"，支付模块其余流程（订单/回调/激活）保持不变。
 */
@Component
public class WechatPaymentChannel implements PaymentChannel {

    private final AppProperties properties;

    public WechatPaymentChannel(AppProperties properties) {
        this.properties = properties;
    }

    @Override
    public String name() {
        return "wechat";
    }

    @Override
    public String createPay(PayOrder order) {
        // TODO 营业执照办理后接入：
        //  1) 用 wechat-app-id / wechat-mch-id 调 Native 下单 API；
        //  2) 返回 code_url（二维码内容）；
        //  3) 异步通知地址为 wechat-notify-url，回调进 PaymentService.handleNotify。
        throw new BizException(ErrorCode.SYSTEM_ERROR,
                "微信支付功能开发中：营业执照办理后接入（当前仅支持模拟支付）");
    }

    @Override
    public boolean verifyNotify(Map<String, String> params) {
        // TODO 微信支付 APIv3 验签（平台证书），验签失败返回 false
        return false;
    }
}
