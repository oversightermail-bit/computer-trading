# -*- coding: utf-8 -*-
"""排查多余商品行：查看 id>=46 的商品与实际目录尾部。"""
import sys

import pymysql

sys.stdout.reconfigure(encoding="utf-8")
conn = pymysql.connect(host="127.0.0.1", port=3306, user="root",
                       password="123456", database="hw_price", charset="utf8mb4")
cur = conn.cursor()
cur.execute("SELECT id, hardware_type, brand, model, spec, perf_score FROM t_product WHERE id>=45 ORDER BY id")
print("== DB id>=45 ==")
for r in cur.fetchall():
    print(r)
cur.execute("SELECT COUNT(*) FROM t_price_history WHERE date=CURDATE()")
print("今日价格行数:", cur.fetchone()[0])
conn.close()

sys.path.insert(0, r"D:\AI电脑购买指导项目\后端\tools")
import gen_sample_data as g
print("\n== gen_sample_data PRODUCTS 尾部（序号 40+）==")
for i, p in enumerate(g.PRODUCTS):
    if i >= 40:
        print(i + 1, p)
