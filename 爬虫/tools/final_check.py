# -*- coding: utf-8 -*-
"""最终核对：今天 t_price_history 的价格分布（真实抓取 vs 演示填充）。"""
import sys

import pymysql
from dbconn import password

sys.stdout.reconfigure(encoding="utf-8")

conn = pymysql.connect(host="127.0.0.1", port=3306, user="root",
                       password=password(), database="hw_price", charset="utf8mb4")
cur = conn.cursor()
cur.execute("""
    SELECT p.id, p.hardware_type, p.brand, p.model, p.spec, h.price
    FROM t_product p JOIN t_price_history h
      ON h.product_id = p.id AND h.date = CURDATE()
    ORDER BY p.id
""")
rows = cur.fetchall()
n = 0
for pid, ht, br, mo, sp, price in rows:
    print("%2d %-12s %-8s %-14s %-10s %8.2f" % (pid, ht, br, mo, sp, float(price)))
    n += 1
print("\n今日共 %d 行" % n)

cur.execute("SELECT COUNT(DISTINCT date) FROM t_price_history")
print("覆盖日期数:", cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM t_price_history")
print("总行数:", cur.fetchone()[0])
conn.close()
