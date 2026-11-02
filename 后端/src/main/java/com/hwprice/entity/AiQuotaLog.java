package com.hwprice.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * AI 额度消耗流水表 t_ai_quota_log（对账/申诉/明细展示；
 * Redis 计数器失效时可凭流水重建）
 */
@Data
@TableName("t_ai_quota_log")
public class AiQuotaLog {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long userId;

    /** 关联 AI 会话 id（返还记录与消耗记录共用同一会话） */
    private Long sessionId;

    /** 消耗额度：正数=消耗，负数=返还 */
    private Integer cost;

    /** AI_CHAT=正常消耗 / AI_REFUND=失败返还 */
    private String quotaType;

    private LocalDateTime createTime;
}
