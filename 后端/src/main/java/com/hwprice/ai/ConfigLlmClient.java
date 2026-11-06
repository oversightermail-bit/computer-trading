package com.hwprice.ai;

import com.hwprice.service.AiConfigService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Component;

/**
 * 大模型网关路由（运行时切换，默认 Bean）：
 * <ul>
 *   <li>免费账户：管理员配置了免费档密钥（t_app_config.ai.free.apiKey）→ 走云端大模型；</li>
 *   <li>付费账户：管理员配置了付费档密钥（t_app_config.ai.paid.apiKey）→ 走云端大模型；</li>
 *   <li>某档未配置密钥 → 仅该档回落本地 Mock 演示模型（无外网可演示）。</li>
 * </ul>
 * 两档各自独立、即时生效，无需重启；AiService 注入 LlmClient 时使用本实现。
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
    public String chat(String systemPrompt, String userText, String imageUrl, boolean paid) {
        if (aiConfigService.hasApiKey(paid)) {
            return openAiClient.chat(systemPrompt, userText, imageUrl, paid);
        }
        log.debug("{}档未配置云端大模型密钥，使用本地 Mock 演示模型", paid ? "付费" : "免费");
        return mockClient.chat(systemPrompt, userText, imageUrl, paid);
    }
}
