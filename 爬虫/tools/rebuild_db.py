# -*- coding: utf-8 -*-
"""把数据库重建为规范状态：
  - 删除 id>=46 的商品与全部价格时序（含错序/重复行）
  - 按规范顺序插入 13 个新型号（id 46-58）
  - 重建 58 型号 × 30 天演示时序（今天的真实行后续由采集轮次写回）
"""
import random
import sys
from datetime import date, timedelta

import pymysql

sys.path.insert(0, r"D:\AI电脑购买指导项目\后端\tools")
sys.stdout.reconfigure(encoding="utf-8")
import gen_sample_data as g  # noqa: E402

DAYS = g.DAYS
PRODUCTS = g.PRODUCTS  # 58 个（已规范：1-45 含替换，46-58 新增）
PLATFORM = g.PLATFORMS[0]
FACTOR = g.PLATFORM_FACTOR[PLATFORM]

conn = pymysql.connect(host="127.0.0.1", port=3306, user="root",
                       password="123456", database="hw_price",
                       charset="utf8mb4", autocommit=True)
cur = conn.cursor()

cur.execute("DELETE FROM t_price_history")
cur.execute("DELETE FROM t_product WHERE id >= 46")
print("已清空价格时序与 id>=46 的商品")

# 规范插入新型号（PRODUCTS 第 45 项起 = 13 个新增）
for i, p in enumerate(PRODUCTS[45:], start=46):
    cur.execute("INSERT INTO t_product (id, hardware_type, brand, model, spec, perf_score) "
                "VALUES (%s,%s,%s,%s,%s,%s)", (i, p[0], p[1], p[2], p[3], p[5]))
print("已插入新型号 id 46-58")


def price_series(seed, base):
    rng = random.Random(seed)
    price = base
    out = []
    for _ in range(DAYS):
        drift = rng.uniform(-0.02, 0.02)
        price = max(base * 0.92, min(base * 1.08, price * (1 + drift)))
        out.append(round(price, 2))
    return out


today = date.today()
rows = []
for i, p in enumerate(PRODUCTS):
    pid = i + 1
    base = p[4]
    start = base * FACTOR * (1 + random.Random(pid).uniform(-0.02, 0.02))
    series = price_series(pid * 31, start)
    for n, price in enumerate(series):
        ago = DAYS - 1 - n
        rows.append((pid, PLATFORM, price, (today - timedelta(days=ago)).isoformat()))

cur.executemany("INSERT INTO t_price_history (product_id, platform, price, date) VALUES (%s,%s,%s,%s)", rows)
print("已重建演示时序 %d 行（58 型号 × 30 天）" % len(rows))

cur.execute("SELECT COUNT(*) FROM t_product")
print("t_product 行数:", cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM t_price_history")
print("t_price_history 行数:", cur.fetchone()[0])
conn.close()
print("DONE")
