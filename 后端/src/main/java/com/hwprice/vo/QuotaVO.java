package com.hwprice.vo;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 当前订阅等级与剩余额度视图。
 * 字段名与前端 quota.js 约定一致：plan / dayUsed / dayTotal / monthUsed / monthTotal。
 */
@Data
public class QuotaVO {

    /** 当前套餐名（前端直接展示"当前：xxx"） */
    private String plan;

    private Long planId;

    /** 日维度 */
    private long dayUsed;
    private long dayTotal;
    private long dayRemain;

    /** 月维度 */
    private long monthUsed;
    private long monthTotal;
    private long monthRemain;

    /** 是否支持图片问答 */
    private boolean multimodal;

    /** 订阅到期时间（免费版为 null） */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime expireTime;

    /** 可升级套餐列表（额度用尽 429 时弹窗展示） */
    private List<PlanVO> upgradable;
}
