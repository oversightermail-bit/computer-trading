package com.hwprice.security;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.hwprice.common.ErrorCode;
import com.hwprice.common.Result;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import java.nio.charset.StandardCharsets;
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 登录/注册接口限流：同 IP 30 秒窗口内最多 5 次（内存滑动窗口，单实例足够比赛演示；
 * 多实例部署可替换为 Redis 计数器）。超限返回 HTTP 429 + 业务码 42902。
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class RateLimitInterceptor implements HandlerInterceptor {

    private static final int WINDOW_SECONDS = 30;
    private static final int MAX_ATTEMPTS = 5;

    private final ObjectMapper objectMapper;
    private final ConcurrentHashMap<String, Deque<Long>> attempts = new ConcurrentHashMap<>();

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler)
            throws Exception {
        String ip = clientIp(request);
        Deque<Long> deque = attempts.computeIfAbsent(ip, k -> new ArrayDeque<>());
        long now = System.currentTimeMillis();
        synchronized (deque) {
            while (!deque.isEmpty() && now - deque.peekFirst() > WINDOW_SECONDS * 1000L) {
                deque.pollFirst();
            }
            if (deque.size() >= MAX_ATTEMPTS) {
                log.warn("登录/注册限流触发: ip={}", ip);
                response.setStatus(HttpStatus.TOO_MANY_REQUESTS.value());
                response.setContentType(MediaType.APPLICATION_JSON_VALUE);
                response.setCharacterEncoding(StandardCharsets.UTF_8.name());
                response.getWriter().write(objectMapper.writeValueAsString(
                        Result.fail(ErrorCode.TOO_MANY_REQUESTS)));
                return false;
            }
            deque.addLast(now);
        }
        return true;
    }

    /** 客户端 IP（优先 X-Forwarded-For 首段，适配反向代理部署） */
    private String clientIp(HttpServletRequest request) {
        String xff = request.getHeader("X-Forwarded-For");
        if (xff != null && !xff.isBlank()) {
            return xff.split(",")[0].trim();
        }
        return request.getRemoteAddr();
    }
}
