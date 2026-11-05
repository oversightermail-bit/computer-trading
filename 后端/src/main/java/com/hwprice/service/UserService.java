package com.hwprice.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.hwprice.common.BizException;
import com.hwprice.common.ErrorCode;
import com.hwprice.dto.AdminUserUpdateReq;
import com.hwprice.dto.LoginReq;
import com.hwprice.dto.RegisterReq;
import com.hwprice.entity.User;
import com.hwprice.mapper.AiQuotaLogMapper;
import com.hwprice.mapper.AiSessionMapper;
import com.hwprice.mapper.UserMapper;
import com.hwprice.mapper.UserSubscriptionMapper;
import com.hwprice.quota.QuotaContext;
import com.hwprice.security.JwtUtil;
import com.hwprice.vo.AdminUserVO;
import com.hwprice.vo.LoginVO;
import com.hwprice.vo.QuotaVO;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 用户服务：注册（校验唯一性 + BCrypt 加盐存储）、登录（签发 JWT）、管理员用户管理。
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class UserService {

    /** 根管理员账号：不可被删除 / 不可被改角色（密码可由本人修改） */
    public static final String ROOT_ADMIN = "Controler";

    private final UserMapper userMapper;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtil jwtUtil;
    private final SubscriptionService subscriptionService;
    private final QuotaService quotaService;
    private final PlanService planService;
    private final UserSubscriptionMapper userSubscriptionMapper;
    private final AiSessionMapper aiSessionMapper;
    private final AiQuotaLogMapper aiQuotaLogMapper;

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

    // ---------------- 管理员：用户管理 ----------------

    /** 全部用户（含套餐名，管理页用户列表） */
    public List<AdminUserVO> listUsers() {
        return userMapper.selectList(new QueryWrapper<User>().orderByAsc("id")).stream().map(u -> {
            AdminUserVO vo = new AdminUserVO();
            vo.setId(u.getId());
            vo.setUsername(u.getUsername());
            vo.setRole(u.getRole());
            vo.setCreateTime(u.getCreateTime());
            try {
                vo.setPlan(subscriptionService.current(u.getId()).getPlanName());
            } catch (Exception e) {
                vo.setPlan("--");
            }
            return vo;
        }).toList();
    }

    /** 管理员修改用户：改角色 / 重置密码（至少一项；根管理员不可改角色） */
    public void updateUser(Long id, AdminUserUpdateReq req) {
        User user = userMapper.selectById(id);
        if (user == null) {
            throw new BizException(ErrorCode.NOT_FOUND, "用户不存在");
        }
        if (req.getRole() != null && !req.getRole().isBlank()) {
            String role = req.getRole().trim().toUpperCase();
            if (!List.of("USER", "ADMIN").contains(role)) {
                throw new BizException(ErrorCode.PARAM_ERROR, "角色仅支持 USER / ADMIN");
            }
            if (ROOT_ADMIN.equals(user.getUsername())) {
                throw new BizException(ErrorCode.FORBIDDEN, "根管理员 Controler 的角色不可修改");
            }
            user.setRole(role);
        }
        if (req.getPassword() != null && !req.getPassword().isBlank()) {
            if (req.getPassword().length() < 6 || req.getPassword().length() > 32) {
                throw new BizException(ErrorCode.PARAM_ERROR, "密码长度需在 6-32 位之间");
            }
            user.setPasswordHash(passwordEncoder.encode(req.getPassword()));
        }
        userMapper.updateById(user);
        log.info("管理员修改用户 id={} username={}", id, user.getUsername());
    }

    /** 管理员删除用户（连同订阅/会话/额度流水；根管理员不可删） */
    @Transactional(rollbackFor = Exception.class)
    public void deleteUser(Long id) {
        User user = userMapper.selectById(id);
        if (user == null) {
            throw new BizException(ErrorCode.NOT_FOUND, "用户不存在");
        }
        if (ROOT_ADMIN.equals(user.getUsername())) {
            throw new BizException(ErrorCode.FORBIDDEN, "根管理员 Controler 不可删除");
        }
        userSubscriptionMapper.delete(new QueryWrapper<com.hwprice.entity.UserSubscription>()
                .eq("user_id", id));
        aiSessionMapper.delete(new QueryWrapper<com.hwprice.entity.AiSession>()
                .eq("user_id", id));
        aiQuotaLogMapper.delete(new QueryWrapper<com.hwprice.entity.AiQuotaLog>()
                .eq("user_id", id));
        userMapper.deleteById(id);
        log.info("管理员删除用户 id={} username={}", id, user.getUsername());
    }
}
