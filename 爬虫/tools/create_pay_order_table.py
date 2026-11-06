# -*- coding: utf-8 -*-
"""一次性脚本：在 hw_price 库创建订阅支付单表 t_pay_order（支付模块）。

依赖：pip install pymysql（本机 PATH python 已装）
"""
import pymysql
from dbconn import password

DDL = """
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
"""

conn = pymysql.connect(host="127.0.0.1", port=3306, user="root", password=password(),
                       database="hw_price", charset="utf8mb4", autocommit=True)
try:
    cur = conn.cursor()
    cur.execute(DDL)
    cur.execute("SHOW TABLES LIKE 't_pay_order'")
    print("t_pay_order exists:", cur.fetchone() is not None)
    print("DONE")
finally:
    conn.close()
