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
    private Crawler crawler = new Crawler();
    private Security security = new Security();

    @Data
    public static class Jwt {
        /** HS256 签名密钥，>= 32 字节 */
        private String secret;
        /** token 有效期（小时） */
        private int expireHours = 168;
    }

    @Data
    public static class Ai {
        /** 回答压缩最大字符数 */
        private int compressMaxChars = 500;
        /** 大模型调用超时（秒） */
        private int timeoutSeconds = 30;
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
        /** 支付模块配置（模拟支付 + 可切换真实接口） */
        private Payment payment = new Payment();
    }

    @Data
    public static class Payment {
        /** 支付通道：mock=模拟支付（比赛演示，demo 演示账号即走此通道）；
         *  alipay / wechat=真实支付接口（营业执照办理后切换即可启用） */
        private String channel = "mock";
        /** 真实支付接口参数占位（办理营业执照后填写，切换 channel 后生效） */
        private String alipayAppId = "";
        private String alipayNotifyUrl = "";
        private String alipayReturnUrl = "";
        private String alipayPublicKey = "";
        private String appPrivateKey = "";
        private String wechatAppId = "";
        private String wechatMchId = "";
        private String wechatNotifyUrl = "";
        private String wechatApiKey = "";
    }

    @Data
    public static class Crawler {
        /** 爬虫子模块工作目录（相对后端运行目录或绝对路径） */
        private String workDir = "../爬虫";
        /** 启动爬虫的命令（管理页"启动爬虫"按钮，单轮抓取） */
        private String command = "python run.py once --mode real";
        /** 启动定时抓取的命令（管理页"开启定时抓取"按钮，服务器常驻：每日 08/12/18/22 点各抓一轮） */
        private String scheduleCommand = "python run.py schedule --mode real";
    }

    @Data
    public static class Security {
        /** 根管理员 Controler 初始密码（环境变量注入，不入库；为空则跳过初始化，绝不使用默认口令） */
        private String adminInitPassword = "";
        /** CORS 允许来源（逗号分隔，环境变量注入；为空 = 开发期全放行，file:// 演示需要） */
        private java.util.List<String> corsAllowedOrigins = new java.util.ArrayList<>();
    }
}
