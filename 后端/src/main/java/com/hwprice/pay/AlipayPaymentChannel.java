package com.hwprice.pay;

import com.hwprice.common.BizException;
import com.hwprice.common.ErrorCode;
import com.hwprice.config.AppProperties;
import com.hwprice.entity.PayOrder;
import org.springframework.stereotype.Component;

import java.util.Map;

/**
 * 支付宝支付通道（真实接口预留）：
 * 营业执照办理后接入「电脑网站支付」，参数取 app.subscribe.payment.alipay-*。
 * 未接入前下单直接返回"功能开发中"，支付模块其余流程（订单/回调/激活）保持不变。
 */
@Component
public class AlipayPaymentChannel implements PaymentChannel {

    private final AppProperties properties;

    public AlipayPaymentChannel(AppProperties properties) {
        this.properties = properties;
    }

    @Override
    public String name() {
        return "alipay";
    }

    @Override
    public String createPay(PayOrder order) {
        // TODO 营业执照办理后接入：
        //  1) 用 alipay-app-id / app-private-key 构造支付宝客户端；
        //  2) 调 alipay.trade.precreate（当面付二维码）生成 qr_code 返回；
        //  3) 异步通知地址为 alipay-notify-url，回调进 PaymentService.handleNotify。
        throw new BizException(ErrorCode.SYSTEM_ERROR,
                "支付宝支付功能开发中：营业执照办理后接入（当前仅支持模拟支付）");
    }

    @Override
    public boolean verifyNotify(Map<String, String> params) {
        // TODO 支付宝 RSA2 验签（alipay-public-key），验签失败返回 false
        return false;
    }
}
