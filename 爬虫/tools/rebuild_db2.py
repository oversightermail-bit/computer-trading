# -*- coding: utf-8 -*-
"""最终重建：清 __pycache__，直接解析 gen_sample_data.py 源文本（不经 import），
按规范顺序重建 t_product(46-58) 与全部演示时序。"""
import ast
import random
import re
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path

import pymysql

sys.stdout.reconfigure(encoding="utf-8")

SRC = Path(r"D:\AI电脑购买指导项目\后端\tools\gen_sample_data.py")
# 1) 清除字节码缓存，杜绝 stale pyc
for pyc in Path(SRC.parent, "__pycache__").glob("gen_sample_data*.pyc"):
    try:
        pyc.unlink()
        print("删除缓存:", pyc.name)
    except Exception as e:
        print("缓存删除失败:", e)

# 2) 解析源文本
text = SRC.read_text(encoding="utf-8")
m = re.search(r"PRODUCTS = \[(.*?)\n\]", text, re.S)
body = m.group(1)
tuples = [tuple(ast.literal_eval("(" + mm.group(1) + ")"))
          for mm in re.finditer(r"\((\([^()]*\))\)", body)]
# 简化：逐行 literal_eval
tuples = []
for line in body.splitlines():
    line = line.strip()
    if not line.startswith("("):
        continue
    tuples.append(ast.literal_eval(line.rstrip(",")))
print("解析 PRODUCTS 数量:", len(tuples))
print("第45项(index44):", tuples[44])
print("第46项(index45):", tuples[45])
print("最后一项:", tuples[-1])
assert len(tuples) == 58

PLATFORM = "中关村在线"
FACTOR = 0.99
DAYS = 30

conn = pymysql.connect(host="127.0.0.1", port=3306, user="root",
                       password="123456", database="hw_price",
                       charset="utf8mb4", autocommit=True)
cur = conn.cursor()
cur.execute("DELETE FROM t_price_history")
cur.execute("DELETE FROM t_product WHERE id >= 46")
print("已清空时序与 id>=46")

for i, p in enumerate(tuples[45:], start=46):
    cur.execute("INSERT INTO t_product (id, hardware_type, brand, model, spec, perf_score) "
                "VALUES (%s,%s,%s,%s,%s,%s)", (i, p[0], p[1], p[2], p[3], p[5]))
print("插入 id 46-58，末项 =", tuples[-1][1], tuples[-1][2])


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
for i, p in enumerate(tuples):
    pid = i + 1
    base = p[4]
    start = base * FACTOR * (1 + random.Random(pid).uniform(-0.02, 0.02))
    series = price_series(pid * 31, start)
    for n, price in enumerate(series):
        ago = DAYS - 1 - n
        rows.append((pid, PLATFORM, price, (today - timedelta(days=ago)).isoformat()))
cur.executemany("INSERT INTO t_price_history (product_id, platform, price, date) VALUES (%s,%s,%s,%s)", rows)

cur.execute("SELECT id, brand, model FROM t_product WHERE id IN (45,46,47,57,58) ORDER BY id")
print("关键行:", cur.fetchall())
cur.execute("SELECT COUNT(*) FROM t_product")
print("t_product:", cur.fetchone()[0])
conn.close()
print("DONE")
