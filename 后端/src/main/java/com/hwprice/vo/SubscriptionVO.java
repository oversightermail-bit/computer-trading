package com.hwprice.vo;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 我的订阅视图
 */
@Data
public class SubscriptionVO {

    private Long subscriptionId;

    private Long planId;

    private String planName;

    /** 等级快照额度 */
    private Integer quotaDay;
    private Integer quotaMonth;

    private boolean multimodal;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime startTime;

    /** 到期时间；免费版为 null（永久） */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime expireTime;

    /** 1=生效 */
    private Integer status;
}
