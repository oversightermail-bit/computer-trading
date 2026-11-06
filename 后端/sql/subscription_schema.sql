-- =========================================================
-- 订阅模块建表脚本（文档《订阅模块本地开发实现指南》要求的独立脚本）
-- 包含 3 张核心表 + 4 个套餐初始化数据，可独立执行：
--   mysql -u root -p < sql/subscription_schema.sql
-- （全量 9 张表的脚本见 schema.sql；两者重复执行互不影响）
-- =========================================================
CREATE DATABASE IF NOT EXISTS hw_price DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE hw_price;

-- ---------- 1. 套餐配置表 ----------
CREATE TABLE IF NOT EXISTS t_subscription_plan (
    id          BIGINT         NOT NULL AUTO_INCREMENT COMMENT '主键',
    plan_name   VARCHAR(50)    NOT NULL COMMENT '套餐名',
    price_month DECIMAL(10, 2) NOT NULL DEFAULT 0 COMMENT '月付价格（元）',
    quota_day   INT            NOT NULL COMMENT '每日 AI 额度（次）',
    quota_month INT            NOT NULL COMMENT '每月 AI 额度（次）',
    multimodal  TINYINT        NOT NULL DEFAULT 0 COMMENT '是否支持图片解析：1=支持',
    status      TINYINT        NOT NULL DEFAULT 1 COMMENT '1=上架 0=下架',
    description VARCHAR(500)   NOT NULL DEFAULT '' COMMENT '权益描述',
    sort_order  INT            NOT NULL DEFAULT 0 COMMENT '排序（等级高低）',
    PRIMARY KEY (id),
    UNIQUE KEY uk_plan_name (plan_name)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '订阅套餐配置';

-- ---------- 2. 用户订阅表（记录当前套餐、有效期及额度计量） ----------
CREATE TABLE IF NOT EXISTS t_user_subscription (
    id          BIGINT      NOT NULL AUTO_INCREMENT COMMENT '主键',
    user_id     BIGINT      NOT NULL COMMENT '用户 id',
    plan_id     BIGINT      NOT NULL COMMENT '套餐 id',
    plan_name   VARCHAR(50) NOT NULL COMMENT '等级快照：套餐名',
    quota_day   INT         NOT NULL DEFAULT 0 COMMENT '等级快照：日额度',
    quota_month INT         NOT NULL DEFAULT 0 COMMENT '等级快照：月额度',
    multimodal  TINYINT     NOT NULL DEFAULT 0 COMMENT '等级快照：是否支持多模态',
    start_time  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '生效时间',
    expire_time DATETIME    NULL COMMENT '到期时间；NULL=永久（免费级）',
    status      TINYINT     NOT NULL DEFAULT 1 COMMENT '1=生效 0=已关闭/已过期',
    day_used    INT         NOT NULL DEFAULT 0 COMMENT '数据库额度计数器：当日已用',
    month_used  INT         NOT NULL DEFAULT 0 COMMENT '数据库额度计数器：当月已用',
    day_key     VARCHAR(8)  NOT NULL DEFAULT '' COMMENT '日计数归属 yyyyMMdd',
    month_key   VARCHAR(7)  NOT NULL DEFAULT '' COMMENT '月计数归属 yyyyMM',
    PRIMARY KEY (id),
    KEY idx_user_status (user_id, status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '用户订阅记录';

-- ---------- 3. 额度使用日志表（记录每次 AI 调用的消耗明细） ----------
CREATE TABLE IF NOT EXISTS t_ai_quota_log (
    id          BIGINT      NOT NULL AUTO_INCREMENT COMMENT '主键',
    user_id     BIGINT      NOT NULL COMMENT '用户 id',
    session_id  BIGINT      COMMENT '关联会话 id',
    cost        INT         NOT NULL COMMENT '额度变化：正数=消耗，负数=返还',
    quota_type  VARCHAR(20) NOT NULL COMMENT 'AI_CHAT=消耗 / AI_REFUND=返还',
    create_time DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发生时间',
    PRIMARY KEY (id),
    KEY idx_user_time (user_id, create_time),
    KEY idx_session (session_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = 'AI 额度消耗流水';

-- ---------- 订阅支付单（支付模块：模拟支付 + 可切换真实接口） ----------
CREATE TABLE IF NOT EXISTS t_pay_order (
    id          BIGINT        NOT NULL AUTO_INCREMENT COMMENT '主键',
    order_no    VARCHAR(40)   NOT NULL COMMENT '业务订单号',
    user_id     BIGINT        NOT NULL COMMENT '下单用户',
    plan_id     BIGINT        NOT NULL COMMENT '套餐 id',
    plan_name   VARCHAR(50)   NOT NULL COMMENT '套餐名快照',
    amount      DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT '应付金额（元）',
    channel     VARCHAR(20)   NOT NULL DEFAULT 'mock' COMMENT '支付通道：mock/alipay/wechat',
    status      TINYINT       NOT NULL DEFAULT 0 COMMENT '0=待支付 1=已支付 2=已关闭',
    pay_params  TEXT          NULL COMMENT '支付参数（mock：模拟收款码内容；真实：预下单返回串）',
    create_time DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '下单时间',
    pay_time    DATETIME      NULL COMMENT '支付时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_order_no (order_no),
    KEY idx_user (user_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '订阅支付单（模拟支付 + 真实接口预留）';

-- ---------- 初始化 4 个套餐（固定 id，INSERT IGNORE 可重复执行） ----------
INSERT IGNORE INTO t_subscription_plan (id, plan_name, price_month, quota_day, quota_month, multimodal, status, description, sort_order) VALUES
(1, '免费版', 0.00,  3,   15,   0, 1, '全部价格与折线浏览；仅文本问答；无图片解析', 1),
(2, '基础版', 9.90,  0,  100,  1, 1, '文本问答 + 配置单图片解析（图片计 2 次）；配置单保存（只限每月次数）', 2),
(3, '专业版', 29.90, 0,  300,  1, 1, '全部 AI 能力 + 多硬件对比 + 历史会话回溯 + 优先响应（只限每月次数）', 3),
(4, '旗舰版', 69.90, 0,  600,  1, 1, '长上下文 + 优先并发 + 配置清单导出（CSV）（只限每月次数）', 4);
