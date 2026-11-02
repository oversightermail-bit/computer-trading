package com.hwprice.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * AI 问答请求。
 * 纯文本问答计 1 次额度；携带 imageUrl 的多模态问答计 2 次。
 */
@Data
public class AiChatReq {

    @NotBlank(message = "提问内容不能为空")
    private String content;

    /** 图片地址（配置单/硬件照片），为空表示纯文本问答 */
    private String imageUrl;
}
