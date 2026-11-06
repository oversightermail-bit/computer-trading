package com.hwprice.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

/**
 * AI 问答请求。
 * 纯文本问答计 1 次额度；携带 imageUrl 的多模态问答计 2 次。
 */
@Data
public class AiChatReq {

    @NotBlank(message = "提问内容不能为空")
    @Size(max = 2000, message = "提问内容过长（最多 2000 字）")
    private String content;

    /** 图片地址（配置单/硬件照片，base64 数据），为空表示纯文本问答 */
    @Size(max = 2_000_000, message = "图片数据过大")
    private String imageUrl;
}
