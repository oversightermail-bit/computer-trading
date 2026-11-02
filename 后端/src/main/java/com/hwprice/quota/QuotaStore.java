package com.hwprice.quota;

/**
 * 额度计数器存储抽象：
 * {@link RedisQuotaStore}（Redis Lua 原子扣减，生产方案）与
 * {@link DbQuotaStore}（MySQL 条件更新，无 Redis 时的降级方案）。
 */
public interface QuotaStore {

    /**
     * 尝试占用额度：日/月任一维度不足则整体不扣。
     *
     * @return true = 扣减成功；false = 额度不足
     */
    boolean tryOccupy(QuotaContext ctx, int cost);

    /** 返还额度（AI 调用失败时调用） */
    void refund(QuotaContext ctx, int cost);

    /** 查询已用额度：[0]=日已用，[1]=月已用 */
    long[] used(QuotaContext ctx);

    /** 手动重置日/月计数（跨日/跨月由 key 过期与归属判断自动完成） */
    void resetDaily(QuotaContext ctx);

    void resetMonthly(QuotaContext ctx);

    /** 存储名：redis / db */
    String name();
}
