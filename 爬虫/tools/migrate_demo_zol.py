# -*- coding: utf-8 -*-
"""一次性迁移脚本：把 t_price_history 的旧三平台演示数据换成中关村在线口径。

与新生成的 sql/init_data.sql 完全同源（同种子同算法）：
  1. 清空 t_price_history（旧演示行：京东/天猫/淘宝 × 1350）；
  2. 按 gen_sample_data 的随机游走重生成 45 商品 × 1 平台 × 30 天并入库；
  3. 当天数据随后由真实采集轮次覆盖（storage 同日刷新）。
"""
import random
import sys
from datetime import date, timedelta

import pymysql
from dbconn import password

sys.path.insert(0, r"D:\AI电脑购买指导项目\后端\tools")
sys.stdout.reconfigure(encoding="utf-8")
import gen_sample_data as g  # noqa: E402

DAYS = g.DAYS
PRODUCTS = g.PRODUCTS
PLATFORM = g.PLATFORMS[0]
FACTOR = g.PLATFORM_FACTOR[PLATFORM]


def price_series(seed, base):
    rng = random.Random(seed)
    price = base
    out = []
    for _ in range(DAYS):
        drift = rng.uniform(-0.02, 0.02)
        price = max(base * 0.92, min(base * 1.08, price * (1 + drift)))
        out.append(round(price, 2))
    return out


conn = pymysql.connect(host="127.0.0.1", port=3306, user="root",
                       password=password(), database="hw_price",
                       charset="utf8mb4", autocommit=True)
cur = conn.cursor()
cur.execute("DELETE FROM t_price_history")
print("已清空 t_price_history 旧演示行")

rows = []
today = date.today()
for i, p in enumerate(PRODUCTS):
    product_id = i + 1
    base = p[4]
    start = base * FACTOR * (1 + random.Random(product_id).uniform(-0.02, 0.02))
    series = price_series(product_id * 31, start)
    for n, price in enumerate(series):
        ago = DAYS - 1 - n
        rows.append((product_id, PLATFORM, price, (today - timedelta(days=ago)).isoformat()))

cur.executemany(
    "INSERT INTO t_price_history (product_id, platform, price, date) "
    "VALUES (%s, %s, %s, %s)", rows)
print("已写入 ZOL 演示时序 %d 行（%s 平台 × 30 天）" % (len(rows), PLATFORM))

cur.execute("SELECT platform, COUNT(*) FROM t_price_history GROUP BY platform")
print("当前分布:", cur.fetchall())
conn.close()
print("DONE")
