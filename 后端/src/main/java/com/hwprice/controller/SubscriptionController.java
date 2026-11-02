package com.hwprice.controller;

import com.hwprice.common.Result;
import com.hwprice.dto.SubscribeOrderReq;
import com.hwprice.security.SecurityUtils;
import com.hwprice.service.PlanService;
import com.hwprice.service.SubscriptionService;
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

/**
 * 订阅接口（F7）：套餐列表（游客）、下单激活（登录）、我的订阅（登录）
 */
@Tag(name = "订阅", description = "套餐列表 / 订阅下单 / 我的订阅")
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class SubscriptionController {

    private final PlanService planService;
    private final SubscriptionService subscriptionService;

    @Operation(summary = "套餐列表（游客）", description = "各订阅等级与 AI 额度权益")
    @GetMapping("/public/subscribe/plans")
    public Result<List<PlanVO>> plans() {
        return Result.ok(planService.listActive());
    }

    @Operation(summary = "订阅下单（登录）", description = "比赛模式跳过支付直接激活；接入支付后由支付回调激活")
    @PostMapping("/auth/subscribe/order")
    public Result<SubscriptionVO> order(@Valid @RequestBody SubscribeOrderReq req) {
        Long userId = SecurityUtils.currentUser().getUserId();
        return Result.ok(subscriptionService.subscribe(userId, req.getPlanId()));
    }

    @Operation(summary = "我的订阅（登录）", description = "当前套餐、有效期与等级快照")
    @GetMapping("/auth/subscribe/me")
    public Result<SubscriptionVO> me() {
        Long userId = SecurityUtils.currentUser().getUserId();
        return Result.ok(subscriptionService.me(userId));
    }
}
