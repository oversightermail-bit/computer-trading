# -*- coding: utf-8 -*-
"""核查扩容后的商品表与今日价格一致性。"""
import sys

import pymysql
from dbconn import password

sys.stdout.reconfigure(encoding="utf-8")
conn = pymysql.connect(host="127.0.0.1", port=3306, user="root",
                       password=password(), database="hw_price", charset="utf8mb4")
cur = conn.cursor()
cur.execute("SELECT COUNT(*), MAX(id) FROM t_product")
print("t_product: %s 行, 最大 id=%s" % cur.fetchone())

cur.execute("""SELECT hardware_type, brand, model, spec, COUNT(*), GROUP_CONCAT(id)
               FROM t_product GROUP BY hardware_type, brand, model, spec
               HAVING COUNT(*) > 1""")
dups = cur.fetchall()
if dups:
    print("重复 SKU 行：")
    for ht, br, mo, sp, c, ids in dups:
        print("  %s | %s %s %s x%d ids=%s" % (ht, br, mo, sp, c, ids))
else:
    print("无重复 SKU 行 ✓")

cur.execute("SELECT COUNT(DISTINCT product_id) FROM t_price_history WHERE date=CURDATE()")
print("今日有价格的型号数:", cur.fetchone()[0])
conn.close()
