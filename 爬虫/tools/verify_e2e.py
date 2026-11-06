# -*- coding: utf-8 -*-
"""爬虫子模块端到端验证脚本（开发自检用，不影响生产库）。

流程：
  1. mock 模式生成"当日采集"与"回填 30 天"两份幂等 SQL；
  2. 在临时库 hw_price_crawl_test 建表并导入（模拟无历史数据的全新部署）；
  3. 断言：45 商品、4050 价格行（3 平台 × 45 型号 × 30 天）；
  4. 同一份 SQL 再导入一遍 → 行数不变（幂等/不重复）；
  5. 打印推荐购买平台报告与抓取统计；
  6. 删除临时库，不触碰真实 hw_price 库。

用法：python tools/verify_e2e.py
"""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hwspider import engine, monitor  # noqa: E402
from dbconn import password  # noqa: E402

MYSQL = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
TEST_DB = "hw_price_crawl_test"
USER = "root"
LOGS = Path(__file__).resolve().parent.parent / "logs"

DDL = """
CREATE TABLE t_product (
    id BIGINT NOT NULL AUTO_INCREMENT,
    hardware_type VARCHAR(30) NOT NULL,
    brand VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    spec VARCHAR(100) NOT NULL DEFAULT '',
    PRIMARY KEY (id), KEY idx_hardware_type (hardware_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE t_price_history (
    id BIGINT NOT NULL AUTO_INCREMENT,
    product_id BIGINT NOT NULL,
    platform VARCHAR(30) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    date DATE NOT NULL,
    PRIMARY KEY (id), KEY idx_product_date (product_id, date), KEY idx_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


def mysql(sql_text: str, use_db: bool = True, input_file: str = None):
    cmd = [MYSQL, "--user=" + USER, "--password=" + password(), "--host=127.0.0.1",
           "--default-character-set=utf8mb4", "--batch", "--skip-column-names"]
    if input_file:
        with open(input_file, "rb") as f:
            data = f.read()
        data = data.replace(b"USE hw_price;", ("USE %s;" % TEST_DB).encode())
        r = subprocess.run(cmd, input=data, capture_output=True)
    else:
        r = subprocess.run(cmd, input=sql_text.encode("utf-8"), capture_output=True)
    if r.returncode != 0:
        raise RuntimeError("mysql 失败: %s" % r.stderr.decode("utf-8", errors="replace"))
    return r.stdout.decode("utf-8", errors="replace").strip()


def count(table: str) -> int:
    return int(mysql("USE %s; SELECT COUNT(*) FROM %s;" % (TEST_DB, table)))


def main():
    logs_ok = True
    try:
        LOGS.mkdir(parents=True, exist_ok=True)
        (LOGS / "probe.txt").write_text("x", encoding="utf-8")
    except OSError:
        logs_ok = False

    print("=" * 70)
    print("爬虫子模块端到端验证（临时库 %s）" % TEST_DB)
    print("=" * 70)

    # 1) 生成当日采集 SQL（mock 模式，45 型号 × 3 平台）
    once_sql = LOGS / "verify_once.sql"
    s1 = engine.run_once(platforms=["京东", "天猫", "淘宝"], mode="mock",
                         sink="sql", out_path=once_sql, overwrite=True)
    print("[1] 当日采集：清洗 %d 行，SQL -> %s" % (s1["cleaned_rows"], once_sql))

    # 2) 生成回填 30 天 SQL
    backfill_sql = LOGS / "verify_backfill.sql"
    s2 = engine.run_backfill(days=30, platforms=["京东", "天猫", "淘宝"],
                             sink="sql", out_path=backfill_sql, overwrite=False)
    print("[2] 回填 30 天：清洗 %d 行，SQL -> %s" % (s2["cleaned_rows"], backfill_sql))

    # 3) 临时库建表导入
    mysql("DROP DATABASE IF EXISTS %s;" % TEST_DB)
    mysql("CREATE DATABASE %s DEFAULT CHARACTER SET utf8mb4;" % TEST_DB)
    mysql("USE %s; %s" % (TEST_DB, DDL))
    mysql(None, input_file=str(once_sql))
    print("[3] 当日 SQL 导入后：商品 %d，价格 %d" % (count("t_product"),
                                                     count("t_price_history")))
    mysql(None, input_file=str(backfill_sql))
    products1, prices1 = count("t_product"), count("t_price_history")
    print("[4] 回填 SQL 导入后：商品 %d，价格 %d（期望 45 / 4050）"
          % (products1, prices1))

    # 4) 幂等复跑：同一份 SQL 再导一遍，行数不变
    mysql(None, input_file=str(backfill_sql))
    mysql(None, input_file=str(once_sql))
    products2, prices2 = count("t_product"), count("t_price_history")
    ok_idem = (products2 == products1 == 45) and (prices2 == prices1 == 4050)
    print("[5] 幂等复跑后：商品 %d，价格 %d -> %s"
          % (products2, prices2, "PASS" if ok_idem else "FAIL"))

    # 5) 数据质量抽查：无负价/零价、日期窗口 30 天、平台名合法
    qa = mysql("USE %s; SELECT MIN(price), MAX(price), COUNT(DISTINCT date), "
               "COUNT(DISTINCT platform) FROM t_price_history;" % TEST_DB)
    minp, maxp, days, plats = qa.split("\t")
    ok_qa = float(minp) > 0 and int(days) == 30 and int(plats) == 3
    print("[6] 质量抽查：最低 %.2f / 最高 %.2f / 覆盖 %s 天 / %s 平台 -> %s"
          % (float(minp), float(maxp), days, plats, "PASS" if ok_qa else "FAIL"))

    # 6) 推荐报告与统计
    import datetime as dt
    rep = LOGS / ("recommend_%s.txt" % dt.date.today().isoformat())
    if rep.exists():
        print("[7] 推荐购买平台报告（前 8 行）：")
        for line in rep.read_text(encoding="utf-8").splitlines()[:8]:
            print("    " + line)
    stats = monitor.read_recent_stats(limit=2)
    print("[8] 最近统计轮数：%d（crawl_stats.jsonl）" % len(stats))

    # 7) 清理临时库
    mysql("DROP DATABASE IF EXISTS %s;" % TEST_DB)
    print("[9] 临时库已删除，真实库 hw_price 未受影响")

    ok = ok_idem and ok_qa and products1 == 45 and prices1 == 4050
    print("=" * 70)
    print("总体结论：%s" % ("ALL PASS ✔" if ok else "存在失败项 ✘"))
    print("=" * 70)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
