package com.hwprice.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 用户订阅记录与有效期表 t_user_subscription。
 * 含等级快照（套餐名/额度/多模态），订阅到期后由定时任务回落免费级。
 * day_used / month_used / day_key / month_key 用于无 Redis 时的数据库额度计数器。
 */
@Data
@TableName("t_user_subscription")
public class UserSubscription {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long userId;

    private Long planId;

    /** 等级快照：套餐名 */
    private String planName;

    /** 等级快照：日额度 */
    private Integer quotaDay;

    /** 等级快照：月额度 */
    private Integer quotaMonth;

    /** 等级快照：是否支持多模态 */
    private Integer multimodal;

    private LocalDateTime startTime;

    /** 到期时间；NULL 表示永久（免费级） */
    private LocalDateTime expireTime;

    /** 1=生效 0=已关闭/已过期 */
    private Integer status;

    // ---- 数据库额度计数器（Redis 不可用时的降级方案） ----
    private Integer dayUsed;
    private Integer monthUsed;
    /** 当前日计数归属 yyyyMMdd */
    private String dayKey;
    /** 当前月计数归属 yyyyMM */
    private String monthKey;
}
