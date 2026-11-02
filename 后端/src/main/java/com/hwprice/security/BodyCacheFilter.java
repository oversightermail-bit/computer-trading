package com.hwprice.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.util.StreamUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

/**
 * 请求体缓存过滤器：把带请求体的写请求（POST/PUT/PATCH）包装为
 * {@link CachedBodyRequest}，让额度拦截器（QuotaInterceptor）在调用大模型之前
 * 就能读取 JSON 体判断本次 AI 问答是纯文本（计 1 次）还是含图片（计 2 次），
 * 同时不影响控制器 {@code @RequestBody} 的正常解析。
 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class BodyCacheFilter extends OncePerRequestFilter {

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                    FilterChain chain) throws ServletException, IOException {
        if (request instanceof CachedBodyRequest) {
            chain.doFilter(request, response);
            return;
        }
        if (isBodyReadable(request)) {
            byte[] body = StreamUtils.copyToByteArray(request.getInputStream());
            chain.doFilter(new CachedBodyRequest(request, body), response);
        } else {
            chain.doFilter(request, response);
        }
    }

    private boolean isBodyReadable(HttpServletRequest request) {
        String method = request.getMethod();
        if (!"POST".equalsIgnoreCase(method) && !"PUT".equalsIgnoreCase(method)
                && !"PATCH".equalsIgnoreCase(method)) {
            return false;
        }
        String contentType = request.getContentType();
        // 文件上传等流式场景不走内存缓存
        return contentType == null || !contentType.toLowerCase().startsWith("multipart/");
    }
}
