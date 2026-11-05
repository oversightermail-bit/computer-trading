package com.hwprice.ai;

import com.hwprice.service.AiConfigService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Component;

/**
 * 大模型网关路由（运行时切换，默认 Bean）：
 * <ul>
 *   <li>管理员配置了 API 密钥（t_app_config.ai.apiKey）→ 走 OpenAI 兼容云端大模型；</li>
 *   <li>未配置密钥 → 自动回落本地 Mock 演示模型（无外网可演示）。</li>
 * </ul>
 * 切换即时生效，无需重启；AiService 注入 LlmClient 时使用本实现。
 */
@Slf4j
@Primary
@Component
@RequiredArgsConstructor
public class ConfigLlmClient implements LlmClient {

    private final AiConfigService aiConfigService;
    private final OpenAiCompatLlmClient openAiClient;
    private final MockLlmClient mockClient;

    @Override
    public String chat(String systemPrompt, String userText, String imageUrl) {
        if (aiConfigService.hasApiKey()) {
            return openAiClient.chat(systemPrompt, userText, imageUrl);
        }
        log.debug("未配置云端大模型密钥，使用本地 Mock 演示模型");
        return mockClient.chat(systemPrompt, userText, imageUrl);
    }
}
