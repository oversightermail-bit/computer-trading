package com.hwprice.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.hwprice.entity.SubscriptionPlan;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

public interface SubscriptionPlanMapper extends BaseMapper<SubscriptionPlan> {

    /** 免费套餐（注册默认等级） */
    @Select("SELECT * FROM t_subscription_plan WHERE price_month = 0 AND status = 1 ORDER BY sort_order, id LIMIT 1")
    SubscriptionPlan selectFreePlan();

    @Select("SELECT * FROM t_subscription_plan WHERE id = #{id} AND status = 1")
    SubscriptionPlan selectActiveById(@Param("id") Long id);
}
