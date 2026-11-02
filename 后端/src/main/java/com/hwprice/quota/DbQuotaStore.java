package com.hwprice.quota;

import com.hwprice.mapper.UserSubscriptionMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.time.LocalDate;
import java.time.YearMonth;
import java.time.format.DateTimeFormatter;

/**
 * 数据库额度计数器（无 Redis 时的降级方案）：
 * 计数保存在 t_user_subscription.day_used / month_used，
 * 通过单条条件 UPDATE 实现"判断 + 扣减"原子性；
 * 日/月归属（day_key / month_key）变化时计数自动清零。
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class DbQuotaStore implements QuotaStore {

    private static final DateTimeFormatter DAY = DateTimeFormatter.ofPattern("yyyyMMdd");
    private static final DateTimeFormatter MONTH = DateTimeFormatter.ofPattern("yyyyMM");

    private final UserSubscriptionMapper userSubscriptionMapper;

    @Override
    public boolean tryOccupy(QuotaContext ctx, int cost) {
        int affected = userSubscriptionMapper.tryOccupy(
                ctx.getSubscriptionId(),
                LocalDate.now().format(DAY),
                YearMonth.now().format(MONTH),
                cost,
                ctx.getQuotaDay(),
                ctx.getQuotaMonth());
        return affected == 1;
    }

    @Override
    public void refund(QuotaContext ctx, int cost) {
        userSubscriptionMapper.refund(ctx.getSubscriptionId(), cost);
    }

    @Override
    public long[] used(QuotaContext ctx) {
        var sub = userSubscriptionMapper.selectById(ctx.getSubscriptionId());
        if (sub == null) {
            return new long[]{0L, 0L};
        }
        long dayUsed = LocalDate.now().format(DAY).equals(sub.getDayKey()) ? orZero(sub.getDayUsed()) : 0L;
        long monthUsed = YearMonth.now().format(MONTH).equals(sub.getMonthKey()) ? orZero(sub.getMonthUsed()) : 0L;
        return new long[]{dayUsed, monthUsed};
    }

    @Override
    public void resetDaily(QuotaContext ctx) {
        var sub = userSubscriptionMapper.selectById(ctx.getSubscriptionId());
        if (sub != null) {
            sub.setDayUsed(0);
            userSubscriptionMapper.updateById(sub);
        }
    }

    @Override
    public void resetMonthly(QuotaContext ctx) {
        var sub = userSubscriptionMapper.selectById(ctx.getSubscriptionId());
        if (sub != null) {
            sub.setMonthUsed(0);
            userSubscriptionMapper.updateById(sub);
        }
    }

    @Override
    public String name() {
        return "db";
    }

    private long orZero(Integer value) {
        return value == null ? 0L : value;
    }
}
