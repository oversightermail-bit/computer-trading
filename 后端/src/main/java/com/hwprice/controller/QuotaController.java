package com.hwprice.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.hwprice.common.Result;
import com.hwprice.mapper.AiQuotaLogMapper;
import com.hwprice.security.SecurityUtils;
import com.hwprice.service.SubscriptionService;
import com.hwprice.service.UserService;
import com.hwprice.vo.QuotaLogVO;
import com.hwprice.vo.QuotaVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 额度接口（登录）：当前套餐与剩余额度、消耗明细（F7）
 */
@Tag(name = "AI 额度", description = "剩余额度查询与消耗明细")
@RestController
@RequestMapping("/api/auth/quota")
@RequiredArgsConstructor
public class QuotaController {

    private final SubscriptionService subscriptionService;
    private final UserService userService;
    private final AiQuotaLogMapper aiQuotaLogMapper;

    @Operation(summary = "当前订阅等级与剩余额度（日/月）",
            description = "字段与前端 quota.js 约定一致：plan/dayUsed/dayTotal/monthUsed/monthTotal")
    @GetMapping
    public Result<QuotaVO> quota() {
        Long userId = SecurityUtils.currentUser().getUserId();
        return Result.ok(userService.quotaView(subscriptionService.current(userId), true));
    }

    @Operation(summary = "额度消耗明细", description = "按时间倒序分页，含会话提问预览")
    @GetMapping("/logs")
    public Result<IPage<QuotaLogVO>> logs(@RequestParam(value = "page", defaultValue = "1") long page,
                                          @RequestParam(value = "size", defaultValue = "20") long size) {
        Long userId = SecurityUtils.currentUser().getUserId();
        return Result.ok(aiQuotaLogMapper.selectLogPage(new Page<>(page, size), userId));
    }
}
