package com.hwprice.vo;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 额度消耗明细视图
 */
@Data
public class QuotaLogVO {

    private Long id;

    private Long sessionId;

    /** 正数=消耗，负数=返还 */
    private Integer cost;

    /** AI_CHAT / AI_REFUND */
    private String quotaType;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime createTime;

    /** 关联会话的提问内容预览（关联会话存在时） */
    private String sessionInput;
}
