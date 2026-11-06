package com.hwprice.ai;

/**
 * 大模型网关抽象：后端统一封装，支持文本与图片（多模态）问答。
 */
public interface LlmClient {

    /**
     * 调用大模型。
     *
     * @param systemPrompt 系统提示词（含网站实时价格上下文）
     * @param userText     用户输入文本
     * @param imageUrl     图片地址，null 表示纯文本
     * @param paid         true=付费账户（走付费档 API 配置），false=免费账户（走免费档 API 配置）
     * @return 模型原始回答
     */
    String chat(String systemPrompt, String userText, String imageUrl, boolean paid);
}
