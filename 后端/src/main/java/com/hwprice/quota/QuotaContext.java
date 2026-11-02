package com.hwprice.quota;

import lombok.AllArgsConstructor;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 额度上下文：当前生效订阅的等级快照与订阅记录 id。
 */
@Data
@AllArgsConstructor
public class QuotaContext {

    private Long userId;

    /** t_user_subscription.id（数据库计数器的更新目标行） */
    private Long subscriptionId;

    private Long planId;

    private String planName;

    /** 日额度上限 */
    private int quotaDay;

    /** 月额度上限 */
    private int quotaMonth;

    /** 是否支持多模态 */
    private boolean multimodal;

    /** 订阅到期时间（免费版为 null） */
    private LocalDateTime expireTime;
}
