package com.hwprice.ai;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.hwprice.config.AppProperties;
import com.hwprice.service.AiConfigService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.time.Duration;

/**
 * OpenAI 兼容大模型客户端：
 * 支持任意 OpenAI 协议网关（OpenAI / DeepSeek / 通义 / Kimi 等），
 * 文本走标准 messages，图片走多模态 content 数组格式。
 *
 * 运行时配置来自 AiConfigService（管理员页面配置，存 t_app_config）：
 * 密钥、接口地址与模型名均由管理员填写，**没有任何默认地址**；
 * 未配置密钥时由 ConfigLlmClient 直接回落本地 Mock 演示模型。
 */
@Slf4j
@Component
public class OpenAiCompatLlmClient implements LlmClient {

    private final AppProperties properties;
    private final AiConfigService aiConfigService;
    private final ObjectMapper objectMapper;

    public OpenAiCompatLlmClient(AppProperties properties, AiConfigService aiConfigService,
                                 ObjectMapper objectMapper) {
        this.properties = properties;
        this.aiConfigService = aiConfigService;
        this.objectMapper = objectMapper;
    }

    /** 每次调用按当前运行时配置构建 RestClient（baseUrl 可能被管理员修改） */
    private RestClient restClient(AiConfigService.Snapshot conf) {
        JdkClientHttpRequestFactory factory = new JdkClientHttpRequestFactory();
        Duration timeout = Duration.ofSeconds(properties.getAi().getTimeoutSeconds());
        factory.setReadTimeout(timeout);
        return RestClient.builder()
                .baseUrl(conf.baseUrl())
                .requestFactory(factory)
                .build();
    }

    @Override
    public String chat(String systemPrompt, String userText, String imageUrl) {
        AiConfigService.Snapshot conf = aiConfigService.current();
        if (conf.apiKey() == null || conf.apiKey().isBlank()) {
            throw new IllegalStateException("未配置 AI API 密钥（请管理员在管理页输入密钥）");
        }
        if (conf.baseUrl() == null || conf.baseUrl().isBlank()) {
            throw new IllegalStateException("未配置接口地址（无默认地址，请管理员在管理页填写）");
        }

        ObjectNode body = objectMapper.createObjectNode();
        body.put("model", conf.model());
        body.put("max_tokens", 800);
        body.put("temperature", 0.3);
        ArrayNode messages = body.putArray("messages");
        messages.addObject().put("role", "system").put("content", systemPrompt);

        ObjectNode user = messages.addObject();
        user.put("role", "user");
        if (imageUrl != null && !imageUrl.isBlank()) {
            // 多模态格式：文本 + 图片
            ArrayNode content = user.putArray("content");
            content.addObject().put("type", "text").put("text", userText);
            content.addObject().put("type", "image_url")
                    .putObject("image_url").put("url", imageUrl);
        } else {
            user.put("content", userText);
        }

        log.debug("调用大模型: model={}, hasImage={}", conf.model(), imageUrl != null && !imageUrl.isBlank());
        JsonNode response = restClient(conf).post()
                .uri("/chat/completions")
                .contentType(MediaType.APPLICATION_JSON)
                .header("Authorization", "Bearer " + conf.apiKey())
                .body(body.toString())
                .retrieve()
                .body(JsonNode.class);

        if (response == null) {
            throw new IllegalStateException("大模型返回空响应");
        }
        JsonNode contentNode = response.path("choices").path(0).path("message").path("content");
        if (contentNode.isMissingNode()) {
            throw new IllegalStateException("大模型响应格式异常: " + response);
        }
        return contentNode.asText();
    }
}
