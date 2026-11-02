package com.hwprice.quota;

import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.ClassPathResource;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.scripting.support.ResourceScriptSource;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.time.YearMonth;
import java.time.format.DateTimeFormatter;
import java.util.Arrays;
import java.util.List;

/**
 * Redis 额度计数器：
 * key 为 quota:{userId}:{planId}:day:{yyyyMMdd} 与 quota:{userId}:{planId}:month:{yyyyMM}，
 * 通过 Lua 脚本保证"判断 + 扣减"的原子性；key 的 TTL 设为到日/月末的剩余秒数，
 * 跨日/跨月自动过期清零，无需定时任务重置。
 */
@Slf4j
@Component
public class RedisQuotaStore implements QuotaStore {

    private static final DateTimeFormatter DAY = DateTimeFormatter.ofPattern("yyyyMMdd");
    private static final DateTimeFormatter MONTH = DateTimeFormatter.ofPattern("yyyyMM");

    private final StringRedisTemplate redisTemplate;

    private final DefaultRedisScript<Long> occupyScript;
    private final DefaultRedisScript<Long> refundScript;

    public RedisQuotaStore(StringRedisTemplate redisTemplate) {
        this.redisTemplate = redisTemplate;
        this.occupyScript = loadScript("lua/quota_occupy.lua");
        this.refundScript = loadScript("lua/quota_refund.lua");
    }

    private static DefaultRedisScript<Long> loadScript(String path) {
        DefaultRedisScript<Long> script = new DefaultRedisScript<>();
        script.setResultType(Long.class);
        script.setScriptSource(new ResourceScriptSource(new ClassPathResource(path)));
        return script;
    }

    private static String dayKey(QuotaContext ctx) {
        return "quota:" + ctx.getUserId() + ":" + ctx.getPlanId() + ":day:" + LocalDate.now().format(DAY);
    }

    private static String monthKey(QuotaContext ctx) {
        return "quota:" + ctx.getUserId() + ":" + ctx.getPlanId() + ":month:" + YearMonth.now().format(MONTH);
    }

    /** 到当日 24:00 的剩余秒数（至少 1 秒，防 key 立即过期） */
    private static long secondsUntilEndOfDay() {
        LocalDateTime now = LocalDateTime.now();
        long seconds = Duration.between(now.toLocalTime(), LocalTime.MAX).getSeconds();
        return Math.max(seconds, 1);
    }

    /** 到当月最后一天 24:00 的剩余秒数 */
    private static long secondsUntilEndOfMonth() {
        LocalDate today = LocalDate.now();
        LocalDateTime end = today.withDayOfMonth(today.lengthOfMonth()).atTime(LocalTime.MAX);
        long seconds = Duration.between(LocalDateTime.now(), end).getSeconds();
        return Math.max(seconds, 1);
    }

    @Override
    public boolean tryOccupy(QuotaContext ctx, int cost) {
        List<String> keys = Arrays.asList(dayKey(ctx), monthKey(ctx));
        Long result = redisTemplate.execute(occupyScript, keys,
                String.valueOf(cost),
                String.valueOf(ctx.getQuotaDay()),
                String.valueOf(ctx.getQuotaMonth()),
                String.valueOf(secondsUntilEndOfDay()),
                String.valueOf(secondsUntilEndOfMonth()));
        return result != null && result == 1L;
    }

    @Override
    public void refund(QuotaContext ctx, int cost) {
        List<String> keys = Arrays.asList(dayKey(ctx), monthKey(ctx));
        redisTemplate.execute(refundScript, keys, String.valueOf(cost));
    }

    @Override
    public long[] used(QuotaContext ctx) {
        String d = redisTemplate.opsForValue().get(dayKey(ctx));
        String m = redisTemplate.opsForValue().get(monthKey(ctx));
        return new long[]{parseLong(d), parseLong(m)};
    }

    @Override
    public void resetDaily(QuotaContext ctx) {
        redisTemplate.delete(dayKey(ctx));
    }

    @Override
    public void resetMonthly(QuotaContext ctx) {
        redisTemplate.delete(monthKey(ctx));
    }

    @Override
    public String name() {
        return "redis";
    }

    private long parseLong(String value) {
        if (value == null) {
            return 0L;
        }
        try {
            return Long.parseLong(value);
        } catch (NumberFormatException e) {
            return 0L;
        }
    }
}
