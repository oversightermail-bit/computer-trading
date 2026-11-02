package com.hwprice.config;

import com.hwprice.quota.QuotaInterceptor;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * MVC 配置：把 AI 额度拦截器挂到 AI 问答接口上。
 */
@Configuration
@RequiredArgsConstructor
public class WebConfig implements WebMvcConfigurer {

    private final QuotaInterceptor quotaInterceptor;

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        // 仅 AI 问答接口消耗额度：JWT 校验之后、调用大模型之前执行
        registry.addInterceptor(quotaInterceptor).addPathPatterns("/api/auth/ai/**");
    }
}
