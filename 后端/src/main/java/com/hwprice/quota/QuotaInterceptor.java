package com.hwprice.quota;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.hwprice.common.ErrorCode;
import com.hwprice.common.Result;
import com.hwprice.security.LoginUser;
import com.hwprice.security.SecurityUtils;
import com.hwprice.service.QuotaService;
import com.hwprice.service.SubscriptionService;
import com.hwprice.service.UserService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import java.nio.charset.StandardCharsets;

/**
 * AI 额度拦截器：在调用大模型之前完成"登录 + 订阅额度"双重门禁。
 * <ul>
 *   <li>成本判定：纯文本 1 次，含图片 2 次；</li>
 *   <li>免费级不支持图片问答（按套餐 multimodal 开关拦截）；</li>
 *   <li>额度不足返回 HTTP 429 + 业务码 42901，并附带当前等级、已用量与可升级套餐，前端据此弹升级窗；</li>
 *   <li>扣减成功后把成本写入 request 属性，供模型异常时返还额度。</li>
 * </ul>
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class QuotaInterceptor implements HandlerInterceptor {

    public static final String ATTR_AI_COST = "aiCost";

    private final QuotaService quotaService;
    private final SubscriptionService subscriptionService;
    private final UserService userService;
    private final ObjectMapper objectMapper;

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler)
            throws Exception {
        LoginUser user = SecurityUtils.currentUser();

        // 读取缓存下来的请求体，判断成本（1 文本 / 2 图片）
        String body = readBody(request);
        int cost = AiCost.of(body, objectMapper);
        String imageUrl = imageUrlOf(body);
        String content = contentOf(body);

        // 参数校验前置：内容为空直接拒绝，不扣额度
        if (content == null || content.isBlank()) {
            writeJson(response, HttpStatus.BAD_REQUEST.value(), Result.fail(ErrorCode.PARAM_ERROR, "提问内容不能为空"));
            return false;
        }
        // 长度校验前置：超长内容/图片在扣额度之前拒绝（与 @Size 校验一致，避免白扣额度）
        if (content.length() > 2000) {
            writeJson(response, HttpStatus.BAD_REQUEST.value(), Result.fail(ErrorCode.PARAM_ERROR, "提问内容过长（最多 2000 字）"));
            return false;
        }
        if (imageUrl != null && imageUrl.length() > 2_000_000) {
            writeJson(response, HttpStatus.BAD_REQUEST.value(), Result.fail(ErrorCode.PARAM_ERROR, "图片数据过大"));
            return false;
        }

        QuotaContext ctx = subscriptionService.current(user.getUserId());

        // 多模态门禁：免费级不支持图片问答
        boolean hasImage = imageUrl != null && !imageUrl.isBlank();
        if (hasImage && !ctx.isMultimodal()) {
            writeJson(response, HttpStatus.FORBIDDEN.value(),
                    Result.fail(ErrorCode.FORBIDDEN, "当前套餐不支持图片问答，升级订阅即可解锁多模态识别"));
            return false;
        }

        // 先扣减：日/月任一级别额度不足则整体不扣，返回 429 引导升级
        if (!quotaService.tryOccupy(ctx, cost)) {
            long[] used = quotaService.used(ctx);
            var quotaVO = userService.quotaView(ctx, true);
            quotaVO.setDayUsed(used[0]);
            quotaVO.setMonthUsed(used[1]);
            writeJson(response, HttpStatus.TOO_MANY_REQUESTS.value(),
                    Result.fail(ErrorCode.QUOTA_EXCEEDED, ErrorCode.QUOTA_EXCEEDED.getDefaultMessage(), quotaVO));
            return false;
        }

        // 记录成本，供 AI 调用失败时返还额度
        request.setAttribute(ATTR_AI_COST, cost);
        return true;
    }

    /** 沿请求包装链找到 CachedBodyRequest，取出缓存的请求体（不消耗流） */
    private String readBody(HttpServletRequest request) {
        HttpServletRequest current = request;
        while (current instanceof jakarta.servlet.http.HttpServletRequestWrapper wrapper) {
            if (current instanceof com.hwprice.security.CachedBodyRequest cached) {
                return new String(cached.getBody(), StandardCharsets.UTF_8);
            }
            current = (HttpServletRequest) wrapper.getRequest();
        }
        return null;
    }

    private String contentOf(String body) {
        return field(body, "content");
    }

    private String imageUrlOf(String body) {
        return field(body, "imageUrl");
    }

    private String field(String body, String name) {
        if (body == null || body.isBlank()) {
            return null;
        }
        try {
            JsonNode node = objectMapper.readTree(body).get(name);
            return node == null ? null : node.asText();
        } catch (Exception e) {
            return null;
        }
    }

    private void writeJson(HttpServletResponse response, int status, Result<?> result) throws Exception {
        response.setStatus(status);
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.setCharacterEncoding(StandardCharsets.UTF_8.name());
        response.getWriter().write(objectMapper.writeValueAsString(result));
    }
}
