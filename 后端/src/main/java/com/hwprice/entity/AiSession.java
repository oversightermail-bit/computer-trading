package com.hwprice.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * AI 问答会话表 t_ai_session
 */
@Data
@TableName("t_ai_session")
public class AiSession {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long userId;

    /** 用户输入文本 */
    private String input;

    /** 用户上传的图片地址（多模态问答） */
    private String imageUrl;

    /** AI 回答 */
    private String answer;

    /** 本次消耗额度（文本 1 / 图片 2） */
    private Integer cost;

    private LocalDateTime createTime;
}
