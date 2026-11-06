package com.hwprice.pay;

import com.hwprice.entity.PayOrder;
import org.springframework.stereotype.Component;

import java.util.Map;

/**
 * 模拟支付通道（比赛演示默认）：
 * 下单即生成模拟收款码内容；确认支付（/pay/mock/confirm）后激活套餐；
 * demo 演示账号与根管理员走本通道。回调验签恒真。
 */
@Component
public class MockPaymentChannel implements PaymentChannel {

    @Override
    public String name() {
        return "mock";
    }

    @Override
    public String createPay(PayOrder order) {
        // 模拟收款码内容：真实接入后此字段为二维码串/收银台地址
        return "mockpay://qr/" + order.getOrderNo();
    }

    @Override
    public boolean verifyNotify(Map<String, String> params) {
        return true;
    }
}
