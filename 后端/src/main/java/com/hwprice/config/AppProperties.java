package com.hwprice.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * 应用自定义配置（前缀 app.*）。
 */
@Data
@ConfigurationProperties(prefix = "app")
public class AppProperties {

    private Jwt jwt = new Jwt();
    private Ai ai = new Ai();
    private Cache cache = new Cache();
    private Quota quota = new Quota();
    private Subscribe subscribe = new Subscribe();

    @Data
    public static class Jwt {
        /** HS256 签名密钥，>= 32 字节 */
        private String secret;
        /** token 有效期（小时） */
        private int expireHours = 168;
    }

    @Data
    public static class Ai {
        /** mock = 本地内置演示模型；openai = OpenAI 兼容接口 */
        private String provider = "mock";
        /** 回答压缩最大字符数 */
        private int compressMaxChars = 500;
        /** 大模型调用超时（秒） */
        private int timeoutSeconds = 30;
        private OpenAi openai = new OpenAi();

        @Data
        public static class OpenAi {
            private String baseUrl = "https://api.openai.com/v1";
            private String apiKey = "";
            private String model = "gpt-4o-mini";
        }
    }

    @Data
    public static class Cache {
        /** 价格折线缓存时间（分钟） */
        private int priceTtlMinutes = 5;
    }

    @Data
    public static class Quota {
        /** auto = Redis 优先、连不上自动降级数据库；redis = 强制 Redis；db = 强制数据库 */
        private String store = "auto";
    }

    @Data
    public static class Subscribe {
        /** 比赛模式：跳过支付，下单即激活 */
        private boolean skipPayment = true;
        /** 到期回落免费级定时任务 cron */
        private String expireCheckCron = "0 0 * * * ?";
    }
}
