package com.hwprice.service;

import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.hwprice.config.AppProperties;
import com.hwprice.entity.SubscriptionPlan;
import com.hwprice.entity.UserSubscription;
import com.hwprice.mapper.UserSubscriptionMapper;
import com.hwprice.quota.QuotaContext;
import com.hwprice.vo.SubscriptionVO;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;

/**
 * 用户订阅服务：
 * <ul>
 *   <li>注册默认免费级；付费等级由"下单（比赛模式跳过支付）"直接激活并写入有效期；</li>
 *   <li>订阅记录保存等级快照（套餐名/日额度/月额度/多模态），到期由定时任务回落免费级；</li>
 *   <li>数据库额度计数器 day_used/month_used 随订阅记录一并维护。</li>
 * </ul>
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class SubscriptionService {

    private final UserSubscriptionMapper subscriptionMapper;
    private final PlanService planService;
    private final AppProperties properties;

    /** 当前生效订阅（含等级快照）；无订阅记录时自动补一条免费级 */
    public QuotaContext current(Long userId) {
        UserSubscription sub = subscriptionMapper.selectActive(userId);
        if (sub == null) {
            sub = createSubscription(userId, planService.freePlan(), true);
        }
        return toContext(sub);
    }

    /** 我的订阅（展示层） */
    public SubscriptionVO me(Long userId) {
        return toVO(current(userId));
    }

    /**
     * 订阅套餐：
     * 比赛模式（app.subscribe.skip-payment=true）跳过支付直接激活；
     * 接入支付后，先创建订单，支付回调再调用本方法激活。
     */
    @Transactional(rollbackFor = Exception.class)
    public SubscriptionVO subscribe(Long userId, Long planId) {
        SubscriptionPlan plan = planService.getActive(planId);
        boolean isFree = plan.getPriceMonth() != null && plan.getPriceMonth().signum() == 0;
        // 关闭当前生效订阅
        subscriptionMapper.update(null, new LambdaUpdateWrapper<UserSubscription>()
                .eq(UserSubscription::getUserId, userId)
                .eq(UserSubscription::getStatus, 1)
                .set(UserSubscription::getStatus, 0)
                .set(UserSubscription::getExpireTime, LocalDateTime.now()));
        UserSubscription sub = createSubscription(userId, plan, isFree);
        log.info("用户 {} 订阅套餐 [{}]，比赛模式跳过支付：{}", userId, plan.getPlanName(), properties.getSubscribe().isSkipPayment());
        return toVO(toContext(sub));
    }

    /**
     * 到期回落：把已过期的付费订阅置为失效（免费级 expire_time 为 NULL，永不过期）。
     *
     * @return 本次处理条数
     */
    @Transactional(rollbackFor = Exception.class)
    public int expireDowngrade() {
        int rows = subscriptionMapper.update(null, new LambdaUpdateWrapper<UserSubscription>()
                .eq(UserSubscription::getStatus, 1)
                .isNotNull(UserSubscription::getExpireTime)
                .lt(UserSubscription::getExpireTime, LocalDateTime.now())
                .set(UserSubscription::getStatus, 0));
        if (rows > 0) {
            log.info("订阅到期回落免费级：处理 {} 条", rows);
        }
        return rows;
    }

    /** 新建订阅记录（含等级快照与计数器初始化） */
    private UserSubscription createSubscription(Long userId, SubscriptionPlan plan, boolean permanent) {
        UserSubscription sub = new UserSubscription();
        sub.setUserId(userId);
        sub.setPlanId(plan.getId());
        sub.setPlanName(plan.getPlanName());
        sub.setQuotaDay(plan.getQuotaDay());
        sub.setQuotaMonth(plan.getQuotaMonth());
        sub.setMultimodal(plan.getMultimodal());
        sub.setStartTime(LocalDateTime.now());
        // 免费级永久有效；付费级按月计费（比赛模式到期 +1 个月）
        sub.setExpireTime(permanent ? null : LocalDateTime.now().plusMonths(1));
        sub.setStatus(1);
        sub.setDayUsed(0);
        sub.setMonthUsed(0);
        subscriptionMapper.insert(sub);
        return sub;
    }

    private QuotaContext toContext(UserSubscription sub) {
        return new QuotaContext(
                sub.getUserId(),
                sub.getId(),
                sub.getPlanId(),
                sub.getPlanName(),
                sub.getQuotaDay() == null ? 0 : sub.getQuotaDay(),
                sub.getQuotaMonth() == null ? 0 : sub.getQuotaMonth(),
                sub.getMultimodal() != null && sub.getMultimodal() == 1,
                sub.getExpireTime());
    }

    private SubscriptionVO toVO(QuotaContext ctx) {
        SubscriptionVO vo = new SubscriptionVO();
        vo.setSubscriptionId(ctx.getSubscriptionId());
        vo.setPlanId(ctx.getPlanId());
        vo.setPlanName(ctx.getPlanName());
        vo.setQuotaDay(ctx.getQuotaDay());
        vo.setQuotaMonth(ctx.getQuotaMonth());
        vo.setMultimodal(ctx.isMultimodal());
        vo.setExpireTime(ctx.getExpireTime());
        vo.setStatus(1);
        // 起始时间从订阅记录取
        UserSubscription sub = subscriptionMapper.selectById(ctx.getSubscriptionId());
        if (sub != null) {
            vo.setStartTime(sub.getStartTime());
        }
        return vo;
    }
}
