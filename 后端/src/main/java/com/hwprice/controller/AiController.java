package com.hwprice.controller;

import com.hwprice.common.BizException;
import com.hwprice.common.ErrorCode;
import com.hwprice.common.Result;
import com.hwprice.dto.AiChatReq;
import com.hwprice.quota.QuotaInterceptor;
import com.hwprice.security.LoginUser;
import com.hwprice.security.SecurityUtils;
import com.hwprice.service.AiService;
import com.hwprice.vo.AiChatVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * AI 问答接口（需登录，受订阅额度约束）（F4）
 */
@Tag(name = "AI 问答", description = "文本/图片问答，额度由拦截器前置扣减")
@RestController
@RequestMapping("/api/auth/ai")
@RequiredArgsConstructor
public class AiController {

    private final AiService aiService;

    @Operation(summary = "AI 问答", description = "纯文本计 1 次，含图片计 2 次；额度用尽返回 429 + code 42901")
    @PostMapping("/chat")
    public Result<AiChatVO> chat(@Valid @RequestBody AiChatReq req, HttpServletRequest request) {
        LoginUser user = SecurityUtils.currentUser();
        // 额度已在 QuotaInterceptor 中扣减，这里取出本次成本
        Object costAttr = request.getAttribute(QuotaInterceptor.ATTR_AI_COST);
        int cost = costAttr instanceof Integer c ? c : 1;
        if (cost < 1) {
            throw new BizException(ErrorCode.SYSTEM_ERROR);
        }
        return Result.ok(aiService.chat(user.getUserId(), req, cost));
    }
}
