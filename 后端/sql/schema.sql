-- =========================================================
-- 硬件价格比价与智能推荐网站 - 完整建表脚本（9 张表）
-- 执行方式：mysql -u root -p < sql/schema.sql
-- 之后执行：mysql -u root -p hw_price < sql/init_data.sql 导入演示数据
-- 订阅模块 3 张表的独立脚本见 subscription_schema.sql
-- =========================================================
CREATE DATABASE IF NOT EXISTS hw_price DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE hw_price;

-- ---------- 用户/账户 ----------
DROP TABLE IF EXISTS t_user;
CREATE TABLE t_user (
    id            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键',
    username      VARCHAR(50)  NOT NULL COMMENT '用户名（唯一）',
    password_hash VARCHAR(100) NOT NULL COMMENT 'BCrypt 加盐密码哈希',
    role          VARCHAR(20)  NOT NULL DEFAULT 'USER' COMMENT '角色：USER/ADMIN',
    create_time   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_username (username)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '用户表';

-- ---------- 硬件类目与文案 ----------
DROP TABLE IF EXISTS t_hardware;
CREATE TABLE t_hardware (
    id         BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键',
    type       VARCHAR(30)  NOT NULL COMMENT '类型编码，如 cpu/gpu/keyboard',
    name       VARCHAR(50)  NOT NULL COMMENT '硬件名称，如 CPU（台式机）',
    func_desc  VARCHAR(500) NOT NULL DEFAULT '' COMMENT '功能作用解释',
    scene      VARCHAR(500) NOT NULL DEFAULT '' COMMENT '适用场景',
    pitfall    VARCHAR(500) NOT NULL DEFAULT '' COMMENT '易踩坑点',
    sort_order INT          NOT NULL DEFAULT 0 COMMENT '首页排序',
    PRIMARY KEY (id),
    UNIQUE KEY uk_type (type)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '硬件类目与文案';

-- ---------- 商品/型号主数据 ----------
DROP TABLE IF EXISTS t_product;
CREATE TABLE t_product (
    id            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键',
    hardware_type VARCHAR(30)  NOT NULL COMMENT '所属硬件类型，对应 t_hardware.type',
    brand         VARCHAR(50)  NOT NULL COMMENT '品牌',
    model         VARCHAR(100) NOT NULL COMMENT '型号',
    spec          VARCHAR(100) NOT NULL DEFAULT '' COMMENT '规格，如 12GB / DDR5 6000 / 1TB',
    PRIMARY KEY (id),
    KEY idx_hardware_type (hardware_type)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '商品/型号主数据';

-- ---------- 价格时序（爬虫写入，后端只读聚合） ----------
DROP TABLE IF EXISTS t_price_history;
CREATE TABLE t_price_history (
    id         BIGINT         NOT NULL AUTO_INCREMENT COMMENT '主键',
    product_id BIGINT         NOT NULL COMMENT '商品 id',
    platform   VARCHAR(30)    NOT NULL COMMENT '平台：淘宝/京东/天猫等',
    price      DECIMAL(10, 2) NOT NULL COMMENT '当日价格（元）',
    date       DATE           NOT NULL COMMENT '采集日期',
    PRIMARY KEY (id),
    KEY idx_product_date (product_id, date),
    KEY idx_date (date)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '价格时序表';

-- ---------- 二手交易（本期暂不开发，仅预留表结构） ----------
DROP TABLE IF EXISTS t_trade;
CREATE TABLE t_trade (
    id            BIGINT         NOT NULL AUTO_INCREMENT COMMENT '主键',
    user_id       BIGINT         NOT NULL COMMENT '发布用户',
    hardware_type VARCHAR(30)    NOT NULL COMMENT '硬件类型，复用 t_hardware.type',
    title         VARCHAR(200)   NOT NULL COMMENT '标题',
    price         DECIMAL(10, 2) NOT NULL COMMENT '售价',
    status        TINYINT        NOT NULL DEFAULT 0 COMMENT '0=待售 1=已售 2=下架',
    create_time   DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发布时间',
    PRIMARY KEY (id),
    KEY idx_user (user_id),
    KEY idx_status (status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '二手硬件交易表（预留）';

-- ---------- AI 问答会话 ----------
DROP TABLE IF EXISTS t_ai_session;
CREATE TABLE t_ai_session (
    id          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键',
    user_id     BIGINT       NOT NULL COMMENT '提问用户',
    input       TEXT         COMMENT '用户输入文本',
    image_url   VARCHAR(500) COMMENT '图片地址（多模态）',
    answer      TEXT         COMMENT 'AI 回答',
    cost        INT          NOT NULL DEFAULT 1 COMMENT '本次消耗额度（1 文本 / 2 图片）',
    create_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    KEY idx_user_time (user_id, create_time)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = 'AI 问答会话';

-- ---------- 订阅等级与额度定义 ----------
DROP TABLE IF EXISTS t_subscription_plan;
CREATE TABLE t_subscription_plan (
    id          BIGINT         NOT NULL AUTO_INCREMENT COMMENT '主键',
    plan_name   VARCHAR(50)    NOT NULL COMMENT '套餐名：免费版/基础版/专业版/旗舰版',
    price_month DECIMAL(10, 2) NOT NULL DEFAULT 0 COMMENT '月付价格（元）',
    quota_day   INT            NOT NULL COMMENT '每日 AI 额度（次）',
    quota_month INT            NOT NULL COMMENT '每月 AI 额度（次）',
    multimodal  TINYINT        NOT NULL DEFAULT 0 COMMENT '是否支持图片解析：1=支持 0=不支持',
    status      TINYINT        NOT NULL DEFAULT 1 COMMENT '1=上架 0=下架',
    description VARCHAR(500)   NOT NULL DEFAULT '' COMMENT '权益描述',
    sort_order  INT            NOT NULL DEFAULT 0 COMMENT '排序（等级高低）',
    PRIMARY KEY (id),
    UNIQUE KEY uk_plan_name (plan_name)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '订阅套餐配置';

-- ---------- 用户订阅记录与有效期（含等级快照与数据库额度计数器） ----------
DROP TABLE IF EXISTS t_user_subscription;
CREATE TABLE t_user_subscription (
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

-- ---------- AI 额度消耗流水（对账/明细） ----------
DROP TABLE IF EXISTS t_ai_quota_log;
CREATE TABLE t_ai_quota_log (
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
