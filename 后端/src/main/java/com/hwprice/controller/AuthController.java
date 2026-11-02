package com.hwprice.controller;

import com.hwprice.common.Result;
import com.hwprice.dto.LoginReq;
import com.hwprice.dto.RegisterReq;
import com.hwprice.service.UserService;
import com.hwprice.vo.LoginVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 认证接口（游客开放）：注册 / 登录（F1）
 */
@Tag(name = "认证", description = "注册与登录")
@RestController
@RequestMapping("/api/public")
@RequiredArgsConstructor
public class AuthController {

    private final UserService userService;

    @Operation(summary = "注册（游客）", description = "创建账户，注册后默认免费级订阅（3 次/日，仅文本问答）")
    @PostMapping("/register")
    public Result<String> register(@Valid @RequestBody RegisterReq req) {
        return Result.ok(userService.register(req));
    }

    @Operation(summary = "登录（游客）", description = "校验密码并返回 JWT、角色、当前套餐与剩余额度")
    @PostMapping("/login")
    public Result<LoginVO> login(@Valid @RequestBody LoginReq req) {
        return Result.ok(userService.login(req));
    }
}
