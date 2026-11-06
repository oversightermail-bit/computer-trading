package com.hwprice.config;

import com.hwprice.quota.QuotaInterceptor;
import com.hwprice.security.RateLimitInterceptor;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * MVC 配置：AI 额度拦截器 + 登录/注册限流拦截器。
 */
@Configuration
@RequiredArgsConstructor
public class WebConfig implements WebMvcConfigurer {

    private final QuotaInterceptor quotaInterceptor;
    private final RateLimitInterceptor rateLimitInterceptor;

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        // 仅 AI 问答接口消耗额度：JWT 校验之后、调用大模型之前执行
        registry.addInterceptor(quotaInterceptor).addPathPatterns("/api/auth/ai/**");
        // 登录/注册限流：防爆破（同 IP 30 秒 5 次）
        registry.addInterceptor(rateLimitInterceptor)
                .addPathPatterns("/api/public/login", "/api/public/register");
    }
}
