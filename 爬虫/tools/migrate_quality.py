# -*- coding: utf-8 -*-
"""一次性质量迁移（2026-11-05）：
1. t_product 增加 perf_basis / perf_updated 列（记录性能分依据与日期）；
2. t_price_history 增加 source 列（real=真实采集 mock=模拟演示），并清空全部历史
   （既有行都是模拟演示价 / 少量错配真实价，将由修复后的爬虫重新真实采集）；
3. 按 ../../perf_benchmarks.json 用可验证基准（PassMark/3DMark/官方规格）
   覆盖全部型号性能分，并写入依据与更新日期；
4. 创建 t_app_config（管理员配置：AI API 密钥等）。

幂等：重复执行安全。
用法：python tools/migrate_quality.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import pymysql  # type: ignore
except ImportError:
    print("未安装 pymysql，请先 pip install -r requirements.txt")
    sys.exit(1)

from hwspider import config  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent
BENCH = json.loads((ROOT / "perf_benchmarks.json").read_text(encoding="utf-8"))
ITEMS = {it["sku"]: it for it in BENCH["items"]}

conn = pymysql.connect(
    host=config.DATABASE["host"], port=config.DATABASE["port"],
    user=config.DATABASE["user"], password=config.DATABASE["password"],
    database=config.DATABASE["database"], charset=config.DATABASE["charset"],
    autocommit=True)
cur = conn.cursor()


def has_column(table: str, column: str) -> bool:
    cur.execute("SELECT COUNT(*) FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s",
                (config.DATABASE["database"], table, column))
    return cur.fetchone()[0] > 0


# 1) t_product 新列
if not has_column("t_product", "perf_basis"):
    cur.execute("ALTER TABLE t_product ADD COLUMN perf_basis VARCHAR(200) NOT NULL DEFAULT '' "
                "COMMENT '性能分依据（基准/官方规格与公式）' AFTER perf_score")
    print("t_product 新增 perf_basis")
if not has_column("t_product", "perf_updated"):
    cur.execute("ALTER TABLE t_product ADD COLUMN perf_updated DATE NULL "
                "COMMENT '性能分更新日期' AFTER perf_basis")
    print("t_product 新增 perf_updated")

# 2) t_price_history source 列 + 清空历史
if not has_column("t_price_history", "source"):
    cur.execute("ALTER TABLE t_price_history ADD COLUMN source VARCHAR(10) NOT NULL DEFAULT 'real' "
                "COMMENT 'real=真实采集 mock=模拟演示（后端只聚合 real）' AFTER date")
    print("t_price_history 新增 source")
cur.execute("DELETE FROM t_price_history")
print("t_price_history 已清空（旧模拟价/错配价将由修复后的爬虫重新真实采集）")

# 3) 性能分基准化
cur.execute("SELECT id, hardware_type, brand, model, spec, perf_score FROM t_product")
rows = cur.fetchall()
applied = skipped = 0
for pid, hw_type, brand, model, spec, old in rows:
    sku = "%s|%s|%s" % (brand, model, spec)
    item = ITEMS.get(sku)
    if item is None:
        skipped += 1
        print("  [跳过] 基准缺失：%s（保留原分 %s）" % (sku, old))
        continue
    cur.execute("UPDATE t_product SET perf_score=%s, perf_basis=%s, perf_updated=%s WHERE id=%s",
                (item["score"], item["basis"], item["updated"], pid))
    applied += 1
print("性能分基准化：应用 %d 条，跳过 %d 条（依据与日期已写入 perf_basis/perf_updated）"
      % (applied, skipped))

# 4) t_app_config
cur.execute("""
CREATE TABLE IF NOT EXISTS t_app_config (
    id          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键',
    cfg_key     VARCHAR(64)  NOT NULL COMMENT '配置键，如 ai.apiKey',
    cfg_value   VARCHAR(1000) NOT NULL DEFAULT '' COMMENT '配置值',
    update_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_cfg_key (cfg_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='应用配置（管理员维护，如 AI API 密钥）';
""")
print("t_app_config 已就绪（AI API 密钥等管理员配置）")

# 输出核对
cur.execute("SELECT hardware_type, COUNT(*), MIN(perf_score), MAX(perf_score) "
            "FROM t_product GROUP BY hardware_type ORDER BY hardware_type")
print("\n性能分分布核对（类目, 型号数, 最低, 最高）：")
for r in cur.fetchall():
    print("   %-12s %2d %3d %3d" % r)
conn.close()
print("\n迁移完成。下一步：python run.py once 重新真实采集。")
