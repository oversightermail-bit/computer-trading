package com.hwprice.ai;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.hwprice.config.AppProperties;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.MediaType;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.time.Duration;

/**
 * OpenAI 兼容大模型客户端（app.ai.provider=openai）：
 * 支持任意 OpenAI 协议网关（OpenAI / DeepSeek / 通义 / Kimi 等），
 * 文本走标准 messages，图片走多模态 content 数组格式。
 */
@Slf4j
@Component
@ConditionalOnProperty(prefix = "app.ai", name = "provider", havingValue = "openai")
public class OpenAiCompatLlmClient implements LlmClient {

    private final AppProperties properties;
    private final ObjectMapper objectMapper;
    private final RestClient restClient;

    public OpenAiCompatLlmClient(AppProperties properties, ObjectMapper objectMapper) {
        this.properties = properties;
        this.objectMapper = objectMapper;
        JdkClientHttpRequestFactory factory = new JdkClientHttpRequestFactory();
        Duration timeout = Duration.ofSeconds(properties.getAi().getTimeoutSeconds());
        factory.setReadTimeout(timeout);
        this.restClient = RestClient.builder()
                .baseUrl(properties.getAi().getOpenai().getBaseUrl())
                .requestFactory(factory)
                .build();
    }

    @Override
    public String chat(String systemPrompt, String userText, String imageUrl) {
        AppProperties.Ai.OpenAi conf = properties.getAi().getOpenai();
        if (conf.getApiKey() == null || conf.getApiKey().isBlank()) {
            throw new IllegalStateException("app.ai.provider=openai 但未配置 app.ai.openai.api-key");
        }

        ObjectNode body = objectMapper.createObjectNode();
        body.put("model", conf.getModel());
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

        log.debug("调用大模型: model={}, hasImage={}", conf.getModel(), imageUrl != null && !imageUrl.isBlank());
        JsonNode response = restClient.post()
                .uri("/chat/completions")
                .contentType(MediaType.APPLICATION_JSON)
                .header("Authorization", "Bearer " + conf.getApiKey())
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
