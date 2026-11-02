package com.hwprice.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import java.util.concurrent.Executor;

/**
 * 异步配置：额度流水异步落库，不阻塞 AI 主流程。
 */
@Configuration
@EnableAsync
public class AsyncConfig {

    @Bean("quotaLogExecutor")
    public Executor quotaLogExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(2);
        executor.setMaxPoolSize(4);
        executor.setQueueCapacity(500);
        executor.setThreadNamePrefix("quota-log-");
        executor.initialize();
        return executor;
    }
}
