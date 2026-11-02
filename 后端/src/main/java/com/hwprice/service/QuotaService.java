package com.hwprice.service;

import com.hwprice.config.AppProperties;
import com.hwprice.entity.AiQuotaLog;
import com.hwprice.mapper.AiQuotaLogMapper;
import com.hwprice.quota.DbQuotaStore;
import com.hwprice.quota.QuotaContext;
import com.hwprice.quota.QuotaStore;
import com.hwprice.quota.RedisQuotaStore;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.RedisConnectionFailureException;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.concurrent.atomic.AtomicReference;

/**
 * AI 使用额度服务：
 * <ul>
 *   <li>计数器优先走 Redis（Lua 原子"判断+扣减"），连不上时自动降级为数据库计数器；</li>
 *   <li>遵循"先扣减、后调用、失败返还"策略；</li>
 *   <li>每次消耗/返还异步落库 t_ai_quota_log，可对账，也可在计数器失效时按流水重建。</li>
 * </ul>
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class QuotaService {

    private final RedisQuotaStore redisQuotaStore;
    private final DbQuotaStore dbQuotaStore;
    private final AiQuotaLogMapper aiQuotaLogMapper;
    private final AppProperties properties;

    /** 当前生效的额度存储，运行期 Redis 故障时自动切换 */
    private final AtomicReference<QuotaStore> current = new AtomicReference<>();

    /** 初始化存储：auto 模式探测 Redis 可用性 */
    public QuotaStore init() {
        String mode = properties.getQuota().getStore();
        QuotaStore store = switch (mode) {
            case "db" -> dbQuotaStore;
            case "redis" -> redisQuotaStore;
            default -> redisAvailable() ? redisQuotaStore : dbQuotaStore;
        };
        current.set(store);
        log.info("额度计数器使用 [{}] 存储（配置 store={}）", store.name(), mode);
        return store;
    }

    public QuotaStore currentStore() {
        QuotaStore store = current.get();
        if (store == null) {
            store = init();
        }
        return store;
    }

    private boolean redisAvailable() {
        try {
            redisQuotaStore.used(new QuotaContext(0L, 0L, 0L, "probe", 1, 1, false, null));
            return true;
        } catch (Exception e) {
            log.warn("Redis 不可用（{}），额度计数器降级为数据库方案", e.getMessage());
            return false;
        }
    }

    /**
     * 尝试占用额度（日/月双维度）。
     */
    public boolean tryOccupy(QuotaContext ctx, int cost) {
        QuotaStore store = currentStore();
        try {
            return store.tryOccupy(ctx, cost);
        } catch (RedisConnectionFailureException | org.springframework.data.redis.RedisSystemException e) {
            log.warn("Redis 运行期故障，切换为数据库额度计数器: {}", e.getMessage());
            current.set(dbQuotaStore);
            return dbQuotaStore.tryOccupy(ctx, cost);
        }
    }

    /** 返还额度（AI 调用失败） */
    public void refund(QuotaContext ctx, int cost) {
        try {
            currentStore().refund(ctx, cost);
        } catch (Exception e) {
            log.error("额度返还失败，需要人工核对: userId={}, cost={}", ctx.getUserId(), cost, e);
        }
    }

    /** 查询已用额度：[0]=日，[1]=月 */
    public long[] used(QuotaContext ctx) {
        try {
            return currentStore().used(ctx);
        } catch (Exception e) {
            log.warn("查询 Redis 额度失败，按 0 处理: {}", e.getMessage());
            return new long[]{0L, 0L};
        }
    }

    /** 手动重置日额度（Redis：删除日 key；数据库：清零日计数） */
    public void resetDailyQuota(QuotaContext ctx) {
        currentStore().resetDaily(ctx);
    }

    /** 手动重置月额度 */
    public void resetMonthlyQuota(QuotaContext ctx) {
        currentStore().resetMonthly(ctx);
    }

    /** 异步记录消耗流水（正数） */
    @Async("quotaLogExecutor")
    public void recordCharge(Long userId, Long sessionId, int cost) {
        insertLog(userId, sessionId, cost, "AI_CHAT");
    }

    /** 异步记录返还流水（负数） */
    @Async("quotaLogExecutor")
    public void recordRefund(Long userId, Long sessionId, int cost) {
        insertLog(userId, sessionId, -cost, "AI_REFUND");
    }

    private void insertLog(Long userId, Long sessionId, int cost, String type) {
        try {
            AiQuotaLog logRow = new AiQuotaLog();
            logRow.setUserId(userId);
            logRow.setSessionId(sessionId);
            logRow.setCost(cost);
            logRow.setQuotaType(type);
            logRow.setCreateTime(LocalDateTime.now());
            aiQuotaLogMapper.insert(logRow);
        } catch (Exception e) {
            log.error("额度流水落库失败: userId={}, sessionId={}, cost={}", userId, sessionId, cost, e);
        }
    }
}
