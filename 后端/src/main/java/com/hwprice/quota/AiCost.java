package com.hwprice.quota;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;

/**
 * AI 问答额度成本计算：纯文本 1 次，含图片（多模态）2 次。
 */
@Slf4j
public final class AiCost {

    public static final int TEXT_COST = 1;
    public static final int IMAGE_COST = 2;

    private AiCost() {
    }

    /**
     * 从请求体 JSON 判断成本。
     *
     * @return 成本；JSON 无法解析或不是 AI 请求时按文本计 1
     */
    public static int of(String jsonBody, ObjectMapper objectMapper) {
        if (jsonBody == null || jsonBody.isBlank()) {
            return TEXT_COST;
        }
        try {
            JsonNode node = objectMapper.readTree(jsonBody);
            JsonNode image = node.get("imageUrl");
            if (image != null && !image.asText().isBlank()) {
                return IMAGE_COST;
            }
        } catch (Exception e) {
            log.debug("解析请求体失败，按文本问答计费: {}", e.getMessage());
        }
        return TEXT_COST;
    }
}
