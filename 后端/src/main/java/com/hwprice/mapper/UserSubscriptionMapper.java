package com.hwprice.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.hwprice.entity.UserSubscription;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

public interface UserSubscriptionMapper extends BaseMapper<UserSubscription> {

    /** 用户当前生效订阅（NULL 过期时间视为永久） */
    @Select("SELECT * FROM t_user_subscription " +
            "WHERE user_id = #{userId} AND status = 1 " +
            "AND (expire_time IS NULL OR expire_time > NOW()) " +
            "ORDER BY id DESC LIMIT 1")
    UserSubscription selectActive(@Param("userId") Long userId);

    /**
     * 数据库额度计数器：日/月双维度原子校验 + 扣减（无 Redis 时的降级方案）。
     * 日/月归属变化（跨天/跨月）时计数自动清零；任一维度超限则整条不更新。
     *
     * @return 受影响行数：1 = 扣减成功，0 = 额度不足
     */
    @Update("UPDATE t_user_subscription SET " +
            "day_used = IF(day_key = #{dayKey}, day_used + #{cost}, #{cost}), " +
            "day_key = #{dayKey}, " +
            "month_used = IF(month_key = #{monthKey}, month_used + #{cost}, #{cost}), " +
            "month_key = #{monthKey} " +
            "WHERE id = #{id} AND status = 1 " +
            "AND (#{quotaDay} <= 0 OR (IF(day_key = #{dayKey}, day_used, 0) + #{cost} <= #{quotaDay})) " +
            "AND (IF(month_key = #{monthKey}, month_used, 0) + #{cost} <= #{quotaMonth})")
    int tryOccupy(@Param("id") Long subscriptionId,
                  @Param("dayKey") String dayKey,
                  @Param("monthKey") String monthKey,
                  @Param("cost") int cost,
                  @Param("quotaDay") int quotaDay,
                  @Param("quotaMonth") int quotaMonth);

    /** 数据库额度计数器：返还额度（下限 0） */
    @Update("UPDATE t_user_subscription SET " +
            "day_used = GREATEST(day_used - #{cost}, 0), " +
            "month_used = GREATEST(month_used - #{cost}, 0) " +
            "WHERE id = #{id}")
    int refund(@Param("id") Long subscriptionId, @Param("cost") int cost);
}
