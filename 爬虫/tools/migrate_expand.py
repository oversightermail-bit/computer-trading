# -*- coding: utf-8 -*-
"""目录扩容后的数据库迁移：
  1. 5 个替换型号：原位更新 t_product（保留 id），清空其旧历史；
  2. 13 个新增型号：显式 id 46-58 插入 t_product；
  3. 重建历史演示时序（date < 今天，58 型号 × 29 天）；18 个新/换型号补今天的演示行；
  4. 今天已有的 40 条真实采集行原样保留。
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
PRODUCTS = g.PRODUCTS          # 58 个（已更新）
PLATFORM = g.PLATFORMS[0]
FACTOR = g.PLATFORM_FACTOR[PLATFORM]

# 旧 SKU（用于定位 id）→ 新定义完整元组 (type, brand, model, spec, base, perf)
REPLACED = [
    (("ssd", "西部数据", "SN770", "1TB"), ("ssd", "金士顿", "KC3000", "1TB", 599, 80)),
    (("hdd_usb", "东芝", "新小黑", "4TB"), ("hdd_usb", "东芝", "Basics A3", "2TB", 429, 50)),
    (("mem_laptop", "三星", "32GB", "DDR5 5600"), ("mem_laptop", "英睿达", "32GB", "DDR5 5600", 899, 80)),
    (("keyboard", "达尔优", "A98", "无线机械"), ("keyboard", "狼蛛", "F87 Pro", "无线机械", 249, 58)),
    (("keyboard", "ATK", "68", "有线磁轴"), ("keyboard", "洛斐", "小顺 Flow", "68键线性轴", 599, 60)),
]

conn = pymysql.connect(host="127.0.0.1", port=3306, user="root",
                       password=password(), database="hw_price",
                       charset="utf8mb4", autocommit=True)
cur = conn.cursor()

# ---- 1) 替换 5 个（原位更新，id 不变；清空旧历史） ----
replaced_ids = []
for (ht, ob, om, ospec), new in REPLACED:
    cur.execute("SELECT id FROM t_product WHERE hardware_type=%s AND brand=%s AND model=%s AND spec=%s",
                (ht, ob, om, ospec))
    row = cur.fetchone()
    if not row:
        print("警告：未找到旧型号 %s %s %s，跳过" % (ob, om, ospec))
        continue
    pid = row[0]
    replaced_ids.append(pid)
    cur.execute("UPDATE t_product SET brand=%s, model=%s, spec=%s, perf_score=%s WHERE id=%s",
                (new[1], new[2], new[3], new[5], pid))
    cur.execute("DELETE FROM t_price_history WHERE product_id=%s", (pid,))
    print("替换 id=%d -> %s %s %s" % (pid, new[1], new[2], new[3]))

# ---- 2) 新增 13 个（显式 id 46-58） ----
cur.execute("SELECT MAX(id) FROM t_product")
maxid = cur.fetchone()[0]
new_ids = []
if maxid < 46:
    for i, p in enumerate(PRODUCTS[45:], start=46):
        cur.execute("INSERT INTO t_product (id, hardware_type, brand, model, spec, perf_score) "
                    "VALUES (%s,%s,%s,%s,%s,%s)", (i, p[0], p[1], p[2], p[3], p[5]))
        new_ids.append(i)
    print("新增 13 个型号 id 46-58")
else:
    new_ids = list(range(46, 59))
    print("新增型号已存在，跳过插入（id 46-58）")

# ---- 3) 重建历史演示时序 ----
cur.execute("DELETE FROM t_price_history WHERE date < CURDATE()")
print("已清空历史演示时序（date < 今天）")

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
today_has = set()
cur.execute("SELECT product_id FROM t_price_history WHERE date=CURDATE()")
today_has = {r[0] for r in cur.fetchall()}

rows = []
for i, p in enumerate(PRODUCTS):
    pid = i + 1
    base = p[4]
    start = base * FACTOR * (1 + random.Random(pid).uniform(-0.02, 0.02))
    series = price_series(pid * 31, start)
    for n, price in enumerate(series):
        if n == DAYS - 1:  # 今天：只给没有真实行的型号补演示行
            if pid in today_has:
                continue
        else:
            price = price  # 历史全量
        ago = DAYS - 1 - n
        rows.append((pid, PLATFORM, price, (today - timedelta(days=ago)).isoformat()))

cur.executemany("INSERT INTO t_price_history (product_id, platform, price, date) VALUES (%s,%s,%s,%s)", rows)
print("插入演示时序 %d 行（历史 58×29 + 今日补 %d 行）" % (len(rows), len([1 for r in rows if r[3] == today.isoformat()])))

cur.execute("SELECT COUNT(*), MIN(date), MAX(date) FROM t_price_history")
print("t_price_history 现状:", cur.fetchone())
conn.close()
print("DONE")
