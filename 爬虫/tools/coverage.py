# -*- coding: utf-8 -*-
"""核对今日采集覆盖：列出 45 个型号中哪些有今日真实价、哪些仍缺。"""
import sys

import pymysql
from dbconn import password

sys.stdout.reconfigure(encoding="utf-8")
conn = pymysql.connect(host="127.0.0.1", port=3306, user="root",
                       password=password(), database="hw_price", charset="utf8mb4")
cur = conn.cursor()
cur.execute("""SELECT p.id, p.hardware_type, p.brand, p.model, p.spec, h.price
               FROM t_product p LEFT JOIN t_price_history h
                 ON h.product_id = p.id AND h.date = CURDATE()
               ORDER BY p.id""")
hit = miss = 0
for pid, ht, br, mo, sp, price in rows if False else cur.fetchall():
    if price is not None:
        hit += 1
        print("✓ %-6s %-8s %-14s %-10s %8.2f" % (ht, br, mo, sp, float(price)))
    else:
        miss += 1
        print("✗ %-6s %-8s %-14s %-10s" % (ht, br, mo, sp))
print("\n今日有价 %d / 45，缺 %d" % (hit, miss))
conn.close()
