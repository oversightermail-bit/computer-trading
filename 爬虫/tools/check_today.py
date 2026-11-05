# -*- coding: utf-8 -*-
"""核对今日采集入库结果。"""
import sys

import pymysql

sys.stdout.reconfigure(encoding="utf-8")
conn = pymysql.connect(host="127.0.0.1", port=3306, user="root",
                       password="123456", database="hw_price", charset="utf8mb4")
cur = conn.cursor()
cur.execute("SELECT COUNT(*), MIN(price), MAX(price) FROM t_price_history WHERE date=CURDATE()")
n, lo, hi = cur.fetchone()
print("今日行数: %d | 价格区间: %.2f ~ %.2f" % (n, float(lo), float(hi)))
cur.execute("""SELECT p.hardware_type, COUNT(*)
               FROM t_price_history h JOIN t_product p ON p.id=h.product_id
               WHERE h.date=CURDATE() GROUP BY p.hardware_type ORDER BY p.hardware_type""")
print("今日各类目行数:")
for t, c in cur.fetchall():
    print("  %-14s %d" % (t, c))
conn.close()
