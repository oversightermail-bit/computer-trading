package com.hwprice.controller;

import com.hwprice.common.BizException;
import com.hwprice.common.ErrorCode;
import com.hwprice.common.Result;
import com.hwprice.dto.AdminUserUpdateReq;
import com.hwprice.security.SecurityUtils;
import com.hwprice.service.AiConfigService;
import com.hwprice.service.BackendService;
import com.hwprice.service.CrawlerService;
import com.hwprice.service.UserService;
import com.hwprice.vo.AdminUserVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 管理员接口（仅 ROLE_ADMIN，SecurityConfig 统一拦截）：
 * <ul>
 *   <li>爬虫控制：启动爬虫按钮 + 最近一轮统计；</li>
 *   <li>AI 网关配置：密钥、接口地址、模型名均无默认值，由管理员填写；</li>
 *   <li>用户管理：列表 / 改角色改密码 / 删除；</li>
 *   <li>后端服务管理：状态 / 重启（**仅根管理员 Controler**，其余管理员 403）。</li>
 * </ul>
 */
@Tag(name = "管理员", description = "爬虫控制 / AI 网关配置 / 用户管理 / 后端服务（仅管理员）")
@RestController
@RequestMapping("/api/auth/admin")
@RequiredArgsConstructor
public class AdminController {

    private final CrawlerService crawlerService;
    private final AiConfigService aiConfigService;
    private final UserService userService;
    private final BackendService backendService;

    /** 根管理员专属校验（后端服务管理：状态/重启） */
    private void requireRootAdmin() {
        if (!UserService.ROOT_ADMIN.equals(SecurityUtils.currentUser().getUsername())) {
            throw new BizException(ErrorCode.FORBIDDEN, "仅根管理员 Controler 可管理后端服务");
        }
    }

    // ---------------- 后端服务管理（仅根管理员） ----------------

    @Operation(summary = "后端服务状态（仅根管理员）", description = "PID / 启动时间 / 运行时长 / Java 版本 / jar 路径")
    @GetMapping("/backend/status")
    public Result<Map<String, Object>> backendStatus() {
        requireRootAdmin();
        return Result.ok(backendService.status());
    }

    @Operation(summary = "重启后端服务（仅根管理员）", description = "执行项目根目录 重启后端.bat/.sh（Windows/Linux 服务器通用），约 5~8 秒恢复")
    @PostMapping("/backend/restart")
    public Result<Map<String, Object>> backendRestart() {
        requireRootAdmin();
        return Result.ok(backendService.restart());
    }

    // ---------------- 爬虫控制 ----------------

    @Operation(summary = "启动爬虫", description = "后台执行真实采集（只写真实价，采不到显示暂无数据），同时只允许一轮")
    @PostMapping("/crawler/start")
    public Result<Map<String, Object>> startCrawler() {
        return Result.ok(crawlerService.start());
    }

    @Operation(summary = "爬虫状态", description = "最近一轮抓取统计 + 是否运行中")
    @GetMapping("/crawler/status")
    public Result<Map<String, Object>> crawlerStatus() {
        return Result.ok(crawlerService.status());
    }

    // ---------------- AI 网关配置 ----------------

    @Operation(summary = "查看 AI 网关配置", description = "apiKey 打码返回，避免密钥回显")
    @GetMapping("/ai-config")
    public Result<Map<String, Object>> aiConfig() {
        AiConfigService.Snapshot s = aiConfigService.current();
        Map<String, Object> out = new LinkedHashMap<>();
        String key = s.apiKey() == null ? "" : s.apiKey();
        out.put("configured", !key.isBlank());
        out.put("apiKeyMasked", mask(key));
        out.put("baseUrl", s.baseUrl());
        out.put("model", s.model());
        return Result.ok(out);
    }

    @Operation(summary = "保存 AI 网关配置", description = "密钥、接口地址、模型名均无默认值；填密钥必须同时填地址与模型名；密钥留空 = 清空并回落本地 Mock 演示模型")
    @PostMapping("/ai-config")
    public Result<String> saveAiConfig(@RequestBody Map<String, String> body) {
        aiConfigService.save(body.get("apiKey"), body.get("baseUrl"), body.get("model"));
        return Result.ok("已保存并即时生效");
    }

    // ---------------- 用户管理 ----------------

    @Operation(summary = "用户列表")
    @GetMapping("/users")
    public Result<List<AdminUserVO>> users() {
        return Result.ok(userService.listUsers());
    }

    @Operation(summary = "修改用户（角色 / 重置密码）")
    @PutMapping("/users/{id}")
    public Result<String> updateUser(@PathVariable Long id, @RequestBody AdminUserUpdateReq req) {
        userService.updateUser(id, req);
        return Result.ok("已更新");
    }

    @Operation(summary = "删除用户")
    @DeleteMapping("/users/{id}")
    public Result<String> deleteUser(@PathVariable Long id) {
        userService.deleteUser(id);
        return Result.ok("已删除");
    }

    private String mask(String key) {
        if (key == null || key.isBlank()) {
            return "";
        }
        if (key.length() <= 8) {
            return "****";
        }
        return key.substring(0, 4) + "****" + key.substring(key.length() - 4);
    }
}
