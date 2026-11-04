# -*- coding: utf-8 -*-
"""一次性迁移：t_product 增加 perf_score 列并写入 45 个型号的性能分。

性能分与 后端/tools/gen_sample_data.py 的 PRODUCTS 同源（第 6 列）。
"""
import sys

import pymysql

sys.path.insert(0, r"D:\AI电脑购买指导项目\后端\tools")
sys.stdout.reconfigure(encoding="utf-8")
import gen_sample_data as g  # noqa: E402

conn = pymysql.connect(host="127.0.0.1", port=3306, user="root",
                       password="123456", database="hw_price",
                       charset="utf8mb4", autocommit=True)
cur = conn.cursor()

cur.execute("SELECT COLUMN_NAME FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA='hw_price' AND TABLE_NAME='t_product' "
            "AND COLUMN_NAME='perf_score'")
if cur.fetchone() is None:
    cur.execute("ALTER TABLE t_product ADD COLUMN perf_score INT NOT NULL DEFAULT 0 "
                "COMMENT '性能分 1-100（人工维护，用于高性价比推荐）' AFTER spec")
    print("已新增 t_product.perf_score 列")
else:
    print("perf_score 列已存在，跳过 ALTER")

n = 0
for i, p in enumerate(g.PRODUCTS):
    cur.execute("UPDATE t_product SET perf_score=%s WHERE id=%s", (p[5], i + 1))
    n += cur.rowcount
print("已写入性能分：%d / 45 行" % n)

cur.execute("SELECT perf_score, COUNT(*) FROM t_product GROUP BY perf_score ORDER BY perf_score")
print("分布:", cur.fetchall())
conn.close()
print("DONE")
