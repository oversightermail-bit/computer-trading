package com.hwprice.task;

import com.hwprice.service.SubscriptionService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * 订阅定时任务：付费等级到期后自动回落免费级。
 *
 * <p>额度计数器的"每日/每月重置"不需要定时任务：
 * Redis 方案靠 key 的 TTL 到日/月末自动过期；数据库方案靠 day_key / month_key 归属变化自动清零。</p>
 */
@Slf4j
@Component
@EnableScheduling
@RequiredArgsConstructor
public class SubscriptionTasks {

    private final SubscriptionService subscriptionService;

    /** 到期检查（默认每小时整点） */
    @Scheduled(cron = "${app.subscribe.expire-check-cron:0 0 * * * ?}")
    public void expireDowngrade() {
        subscriptionService.expireDowngrade();
    }
}
