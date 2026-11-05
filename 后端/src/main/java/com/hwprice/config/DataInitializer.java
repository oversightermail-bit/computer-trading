package com.hwprice.config;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.hwprice.entity.User;
import com.hwprice.mapper.UserMapper;
import com.hwprice.service.SubscriptionService;
import com.hwprice.service.UserService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;

/**
 * 启动初始化（幂等）：
 * <ul>
 *   <li>根管理员 Controler（密码 comtoapi，角色 ADMIN）不存在则创建，角色不对则修复；</li>
 *   <li>演示账号 demo（密码 demo123，角色 USER）不存在则创建，并补免费级订阅。
 *       demo 登录后前端自动切换 Mock 演示模式，注册用户始终走真实模式。</li>
 * </ul>
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class DataInitializer implements CommandLineRunner {

    private final UserMapper userMapper;
    private final PasswordEncoder passwordEncoder;
    private final SubscriptionService subscriptionService;

    @Override
    public void run(String... args) {
        ensureUser(UserService.ROOT_ADMIN, "comtoapi", "ADMIN");
        ensureUser("demo", "demo123", "USER");
    }

    private void ensureUser(String username, String password, String role) {
        User user = userMapper.selectOne(new QueryWrapper<User>().eq("username", username));
        if (user == null) {
            user = new User();
            user.setUsername(username);
            user.setPasswordHash(passwordEncoder.encode(password));
            user.setRole(role);
            user.setCreateTime(LocalDateTime.now());
            userMapper.insert(user);
            log.info("已创建内置账号: {}（角色 {}）", username, role);
        } else {
            boolean changed = false;
            // 幂等修复：内置账号密码与规定不一致时重置（保证文档凭证始终可用）
            if (!passwordEncoder.matches(password, user.getPasswordHash())) {
                user.setPasswordHash(passwordEncoder.encode(password));
                changed = true;
            }
            if (role.equals("ADMIN") && !"ADMIN".equals(user.getRole())) {
                user.setRole(role);
                changed = true;
            }
            if (changed) {
                userMapper.updateById(user);
                log.info("已修复内置账号: {}（重置密码/角色）", username);
            }
        }
        // 演示账号也需要订阅上下文（登录时 subscriptionService.current 会自动补免费级）；
        // 套餐表缺失时不影响启动，登录时按现有逻辑补。
        try {
            subscriptionService.current(user.getId());
        } catch (Exception e) {
            log.warn("初始化订阅失败（可忽略，登录时会重试）：{}", e.getMessage());
        }
    }
}
