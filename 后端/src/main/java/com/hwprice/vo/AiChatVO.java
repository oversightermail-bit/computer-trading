package com.hwprice.vo;

import lombok.Data;

/**
 * AI 问答响应
 */
@Data
public class AiChatVO {

    /** 大白话压缩后的回答 */
    private String answer;

    /** 本次消耗额度（文本 1 / 图片 2） */
    private int cost;

    /** 会话 id（可回溯） */
    private Long sessionId;

    /** 剩余额度（日 / 月） */
    private long dayRemain;
    private long monthRemain;

    /** 每日不限（quota_day=0 的付费方案）：前端只展示月额度 */
    private boolean dayUnlimited;
}
