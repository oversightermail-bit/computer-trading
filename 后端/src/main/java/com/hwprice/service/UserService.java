package com.hwprice.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.hwprice.common.BizException;
import com.hwprice.common.ErrorCode;
import com.hwprice.dto.LoginReq;
import com.hwprice.dto.RegisterReq;
import com.hwprice.entity.User;
import com.hwprice.mapper.UserMapper;
import com.hwprice.quota.QuotaContext;
import com.hwprice.security.JwtUtil;
import com.hwprice.vo.LoginVO;
import com.hwprice.vo.QuotaVO;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;

/**
 * 用户服务：注册（校验唯一性 + BCrypt 加盐存储）、登录（签发 JWT）。
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class UserService {

    private final UserMapper userMapper;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtil jwtUtil;
    private final SubscriptionService subscriptionService;
    private final QuotaService quotaService;
    private final PlanService planService;

    /** 注册：默认免费级订阅（3 次/日，仅文本问答） */
    @Transactional(rollbackFor = Exception.class)
    public String register(RegisterReq req) {
        Long exists = userMapper.selectCount(new QueryWrapper<User>()
                .eq("username", req.getUsername()));
        if (exists != null && exists > 0) {
            throw new BizException(ErrorCode.PARAM_ERROR, "用户名已被注册");
        }
        User user = new User();
        user.setUsername(req.getUsername());
        user.setPasswordHash(passwordEncoder.encode(req.getPassword()));
        user.setRole("USER");
        user.setCreateTime(LocalDateTime.now());
        userMapper.insert(user);
        // 注册即生效免费级订阅
        subscriptionService.current(user.getId());
        log.info("新用户注册: {}", user.getUsername());
        return user.getUsername();
    }

    /** 登录：校验密码，签发 JWT，附带当前套餐与剩余额度 */
    public LoginVO login(LoginReq req) {
        User user = userMapper.selectOne(new QueryWrapper<User>()
                .eq("username", req.getUsername()));
        if (user == null || !passwordEncoder.matches(req.getPassword(), user.getPasswordHash())) {
            throw new BizException(ErrorCode.PARAM_ERROR, "用户名或密码错误");
        }
        String token = jwtUtil.generate(user.getId(), user.getUsername(), user.getRole());
        QuotaContext ctx = subscriptionService.current(user.getId());
        QuotaVO quota = quotaView(ctx, true);
        return new LoginVO(token, user.getRole(), ctx.getPlanName(), quota);
    }

    /** 组装额度视图（plan 字段 = 套餐名，与前端 quota.js 约定一致） */
    public QuotaVO quotaView(QuotaContext ctx, boolean withUpgradable) {
        long[] used = quotaService.used(ctx);
        QuotaVO vo = new QuotaVO();
        vo.setPlan(ctx.getPlanName());
        vo.setPlanId(ctx.getPlanId());
        vo.setDayUsed(used[0]);
        vo.setDayTotal(ctx.getQuotaDay());
        vo.setDayRemain(Math.max(ctx.getQuotaDay() - used[0], 0));
        vo.setMonthUsed(used[1]);
        vo.setMonthTotal(ctx.getQuotaMonth());
        vo.setMonthRemain(Math.max(ctx.getQuotaMonth() - used[1], 0));
        vo.setMultimodal(ctx.isMultimodal());
        vo.setExpireTime(ctx.getExpireTime());
        if (withUpgradable) {
            com.hwprice.entity.SubscriptionPlan current = planService.getActive(ctx.getPlanId());
            vo.setUpgradable(planService.upgradable(current));
        }
        return vo;
    }
}
