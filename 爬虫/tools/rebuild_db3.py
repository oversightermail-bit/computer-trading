# -*- coding: utf-8 -*-
"""最终修正：按 gen_sample_data.py 源文本的顺序对齐 t_product id 1-58 并重建时序。"""
import ast
import random
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import pymysql
from dbconn import password

sys.stdout.reconfigure(encoding="utf-8")

text = Path(r"D:\AI电脑购买指导项目\后端\tools\gen_sample_data.py").read_text(encoding="utf-8")
m = re.search(r"PRODUCTS = \[(.*?)\n\]", text, re.S)
tuples = []
for line in m.group(1).splitlines():
    line = line.strip()
    if line.startswith("("):
        tuples.append(ast.literal_eval(line.rstrip(",")))
assert len(tuples) == 58, len(tuples)
print("index44 =", tuples[44][1], tuples[44][2], "| index45 =", tuples[45][1], tuples[45][2],
      "| last =", tuples[-1][1], tuples[-1][2])

conn = pymysql.connect(host="127.0.0.1", port=3306, user="root",
                       password=password(), database="hw_price",
                       charset="utf8mb4", autocommit=True)
cur = conn.cursor()

# 1) id 45 = 原 OP-520 位置 → 改为 i5-14600KF
p = tuples[44]
cur.execute("UPDATE t_product SET hardware_type=%s, brand=%s, model=%s, spec=%s, perf_score=%s "
            "WHERE id=45", (p[0], p[1], p[2], p[3], p[5]))
print("id 45 更新为:", p[1], p[2])

# 2) 清掉 id>=46 的重插（顺序错 + OP-520 重复），按规范顺序插入 46-58
cur.execute("DELETE FROM t_product WHERE id >= 46")
for i, p in enumerate(tuples[45:], start=46):
    cur.execute("INSERT INTO t_product (id, hardware_type, brand, model, spec, perf_score) "
                "VALUES (%s,%s,%s,%s,%s,%s)", (i, p[0], p[1], p[2], p[3], p[5]))
print("重插 id 46-58，末项 =", tuples[-1][1], tuples[-1][2])

# 3) 重建全部时序（58 × 30，规范 pid）
cur.execute("DELETE FROM t_price_history")
PLATFORM, FACTOR, DAYS = "中关村在线", 0.99, 30


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
    start = p[4] * FACTOR * (1 + random.Random(pid).uniform(-0.02, 0.02))
    for n, price in enumerate(price_series(pid * 31, start)):
        rows.append((pid, PLATFORM, price, (today - timedelta(days=DAYS - 1 - n)).isoformat()))
cur.executemany("INSERT INTO t_price_history (product_id, platform, price, date) VALUES (%s,%s,%s,%s)", rows)
print("时序重建 %d 行" % len(rows))

# 4) 验证
cur.execute("SELECT id, brand, model FROM t_product WHERE id IN (44,45,46,57,58) ORDER BY id")
print("关键行:", cur.fetchall())
cur.execute("SELECT COUNT(*) FROM t_product")
print("t_product:", cur.fetchone()[0])
cur.execute("""SELECT COUNT(*) FROM (SELECT hardware_type, brand, model, spec, COUNT(*) c
               FROM t_product GROUP BY hardware_type, brand, model, spec HAVING c > 1) x""")
print("重复 SKU 组:", cur.fetchone()[0])
conn.close()
print("DONE")
