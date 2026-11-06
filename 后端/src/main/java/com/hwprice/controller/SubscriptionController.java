package com.hwprice.controller;

import com.hwprice.common.Result;
import com.hwprice.dto.SubscribeOrderReq;
import com.hwprice.security.SecurityUtils;
import com.hwprice.service.PaymentService;
import com.hwprice.service.PlanService;
import com.hwprice.service.SubscriptionService;
import com.hwprice.vo.PayOrderVO;
import com.hwprice.vo.PlanVO;
import com.hwprice.vo.SubscriptionVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

/**
 * 订阅接口（F7）：套餐列表（游客）、支付下单（登录）、模拟支付确认（登录）、
 * 支付异步回调（游客）、我的订阅（登录）。
 * <p>支付模块：app.subscribe.payment.channel 决定支付通道（mock=模拟支付，
 * alipay/wechat=真实接口预留，营业执照办理后切换）；下单→支付→回调激活流程固定。</p>
 */
@Tag(name = "订阅", description = "套餐列表 / 支付下单 / 模拟支付确认 / 支付回调 / 我的订阅")
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class SubscriptionController {

    private final PlanService planService;
    private final SubscriptionService subscriptionService;
    private final PaymentService paymentService;

    @Operation(summary = "套餐列表（游客）", description = "各订阅等级与 AI 额度权益")
    @GetMapping("/public/subscribe/plans")
    public Result<List<PlanVO>> plans() {
        return Result.ok(planService.listActive());
    }

    @Operation(summary = "订阅支付下单（登录）", description = "创建支付单；mock 渠道返回模拟收款码（demo 演示账号走模拟支付确认），真实渠道接入后返回收银台参数")
    @PostMapping("/auth/subscribe/order")
    public Result<PayOrderVO> order(@Valid @RequestBody SubscribeOrderReq req) {
        Long userId = SecurityUtils.currentUser().getUserId();
        return Result.ok(paymentService.createOrder(userId, req.getPlanId()));
    }

    @Operation(summary = "模拟支付确认（登录）", description = "比赛演示：demo 演示账号/根管理员下单后确认支付，标记已支付并激活套餐")
    @PostMapping("/auth/subscribe/pay/mock/confirm")
    public Result<SubscriptionVO> mockConfirm(@RequestBody Map<String, String> body) {
        Long userId = SecurityUtils.currentUser().getUserId();
        return Result.ok(paymentService.confirmMockPay(userId, body.getOrDefault("orderNo", "")));
    }

    @Operation(summary = "支付异步回调（游客）", description = "支付网关通知入口（无 JWT）；mock 渠道兼容，真实渠道接入后在此验签并激活订阅")
    @PostMapping("/public/subscribe/pay/notify")
    public Result<String> payNotify(@RequestBody(required = false) String rawBody) {
        return Result.ok(paymentService.handleNotify(rawBody));
    }

    @Operation(summary = "我的订阅（登录）", description = "当前套餐、有效期与等级快照")
    @GetMapping("/auth/subscribe/me")
    public Result<SubscriptionVO> me() {
        Long userId = SecurityUtils.currentUser().getUserId();
        return Result.ok(subscriptionService.me(userId));
    }
}
