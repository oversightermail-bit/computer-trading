# -*- coding: utf-8 -*-
"""存储层（文档 §四(四) 时序存储）。

清洗后的价格写入 MySQL t_price_history（按 日期+平台+型号），后端据此聚合折线；
t_product 商品主数据按 (hardware_type, brand, model, spec) 幂等 upsert，
与后端演示数据已有 id（1-45）自动合并复用，不产生重复商品。

支持三种 sink，便于无数据库驱动的环境同样可验证：
  - mysql：pymysql 直连（默认，requirements.txt 已含）；
  - sql：   生成幂等 SQL 脚本（INSERT..SELECT WHERE NOT EXISTS + UPDATE），
            可用 mysql 客户端导入，等价于 mysql sink 的效果；
  - jsonl： 落盘原始清洗结果（dry-run / 审计）。
"""
import json
from pathlib import Path
from typing import Dict, List, Optional

from . import config

try:
    import pymysql  # type: ignore
    HAS_PYMYSQL = True
except ImportError:  # pragma: no cover
    HAS_PYMYSQL = False


def _esc(s: str) -> str:
    return str(s).replace("\\", "\\\\").replace("'", "\\'")


class Storage:
    """一次运行共享一个实例，缓存 product_id 解析结果。"""

    def __init__(self, sink: str = "mysql", out_path: Optional[Path] = None):
        self.sink = sink
        if sink in ("sql", "jsonl") and out_path is None:
            out_path = config.LOG_DIR / ("crawl_sql.sql" if sink == "sql"
                                         else "crawl_items.jsonl")
        self.out_path = out_path
        self._conn = None
        self._sql_lines: List[str] = []
        self._jsonl_file = None
        self._pid_cache: Dict[str, Optional[int]] = {}
        self.stats = {"products_upserted": 0, "prices_written": 0, "prices_skipped": 0}

    # ---------------- 连接管理 ----------------
    def open(self) -> None:
        if self.sink == "mysql":
            if not HAS_PYMYSQL:
                raise RuntimeError("未安装 pymysql：请先 pip install -r requirements.txt，"
                                   "或改用 --sink sql/jsonl")
            self._conn = pymysql.connect(
                host=config.DATABASE["host"], port=config.DATABASE["port"],
                user=config.DATABASE["user"], password=config.DATABASE["password"],
                database=config.DATABASE["database"], charset=config.DATABASE["charset"],
                autocommit=True,
            )
        elif self.sink == "sql":
            self._sql_lines = ["-- 由爬虫子系统生成（幂等，可重复导入）",
                               "USE %s;" % config.DATABASE["database"]]
        elif self.sink == "jsonl":
            self._jsonl_file = open(str(self.out_path), "w", encoding="utf-8")

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
        if self.sink == "sql" and self.out_path:
            try:
                self.out_path.parent.mkdir(parents=True, exist_ok=True)
                self.out_path.write_text("\n".join(self._sql_lines) + "\n", encoding="utf-8")
            except OSError as e:
                print("[提示] SQL 脚本写出失败（%s），本轮统计仍有效：%s" % (e, self.out_path))
        if self._jsonl_file is not None:
            try:
                self._jsonl_file.close()
            except Exception:
                pass

    # ---------------- 商品主数据 ----------------
    def _pid_mysql(self, row: dict) -> int:
        key = "%s|%s|%s|%s" % (row["hardware_type"], row["brand"], row["model"], row["spec"])
        if key in self._pid_cache:
            return self._pid_cache[key]
        cur = self._conn.cursor()
        cur.execute(
            "SELECT id FROM t_product WHERE hardware_type=%s AND brand=%s "
            "AND model=%s AND spec=%s LIMIT 1",
            (row["hardware_type"], row["brand"], row["model"], row["spec"]))
        pid = cur.fetchone()
        if pid:
            self._pid_cache[key] = pid[0]
            return pid[0]
        cur.execute(
            "INSERT INTO t_product (hardware_type, brand, model, spec) VALUES (%s,%s,%s,%s)",
            (row["hardware_type"], row["brand"], row["model"], row["spec"]))
        self._pid_cache[key] = cur.lastrowid
        self.stats["products_upserted"] += 1
        return cur.lastrowid

    def _pid_sql(self, row: dict) -> str:
        """SQL sink 的商品解析：条件插入 + 回读 id，幂等。"""
        w = self._sql_lines.append
        ht, br, mo, sp = row["hardware_type"], row["brand"], row["model"], row["spec"]
        w("SET @pid = (SELECT id FROM t_product WHERE hardware_type='%s' AND brand='%s' "
          "AND model='%s' AND spec='%s' LIMIT 1);" % (_esc(ht), _esc(br), _esc(mo), _esc(sp)))
        w("INSERT INTO t_product (hardware_type, brand, model, spec) "
          "SELECT '%s','%s','%s','%s' FROM DUAL "
          "WHERE @pid IS NULL AND NOT EXISTS (SELECT 1 FROM t_product "
          "WHERE hardware_type='%s' AND brand='%s' AND model='%s' AND spec='%s');"
          % (_esc(ht), _esc(br), _esc(mo), _esc(sp), _esc(ht), _esc(br), _esc(mo), _esc(sp)))
        w("SET @pid = COALESCE(@pid, (SELECT id FROM t_product WHERE hardware_type='%s' "
          "AND brand='%s' AND model='%s' AND spec='%s' LIMIT 1));"
          % (_esc(ht), _esc(br), _esc(mo), _esc(sp)))
        self.stats["products_upserted"] += 1
        return "@pid"

    # ---------------- 价格时序 ----------------
    def write_price(self, row: dict, overwrite: bool = True) -> None:
        """写入/更新一条价格：product_id × platform × date 幂等。

        overwrite=True：当日重复采集时刷新为最新价（同一天内价格变化）；
        overwrite=False（回填历史）：已有记录则跳过，不覆盖既有历史。
        """
        if self.sink == "mysql":
            pid = self._pid_mysql(row)
            cur = self._conn.cursor()
            cur.execute(
                "SELECT id FROM t_price_history WHERE product_id=%s AND platform=%s "
                "AND date=%s LIMIT 1", (pid, row["platform"], row["date"]))
            exists = cur.fetchone()
            if exists and overwrite:
                cur.execute("UPDATE t_price_history SET price=%s WHERE id=%s",
                            (row["price"], exists[0]))
                self.stats["prices_written"] += 1
            elif exists:
                self.stats["prices_skipped"] += 1
            else:
                cur.execute(
                    "INSERT INTO t_price_history (product_id, platform, price, date) "
                    "VALUES (%s,%s,%s,%s)",
                    (pid, row["platform"], row["price"], row["date"]))
                self.stats["prices_written"] += 1
        elif self.sink == "sql":
            pid = self._pid_sql(row)
            w = self._sql_lines.append
            pf, pr, dt = _esc(row["platform"]), float(row["price"]), _esc(str(row["date"]))
            w("INSERT INTO t_price_history (product_id, platform, price, date) "
              "SELECT %s, '%s', %.2f, '%s' FROM DUAL WHERE NOT EXISTS "
              "(SELECT 1 FROM t_price_history WHERE product_id=%s AND platform='%s' "
              "AND date='%s');" % (pid, pf, pr, dt, pid, pf, dt))
            if overwrite:
                w("UPDATE t_price_history SET price=%.2f "
                  "WHERE product_id=%s AND platform='%s' AND date='%s';"
                  % (pr, pid, pf, dt))
            self.stats["prices_written"] += 1
        elif self.sink == "jsonl":
            self._jsonl_file.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
            self.stats["prices_written"] += 1


# ---------------- 建表（init 命令用，与后端 schema.sql 同构） ----------------
DDL_PRODUCT = """
CREATE TABLE IF NOT EXISTS t_product (
    id            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键',
    hardware_type VARCHAR(30)  NOT NULL COMMENT '所属硬件类型，对应 t_hardware.type',
    brand         VARCHAR(50)  NOT NULL COMMENT '品牌',
    model         VARCHAR(100) NOT NULL COMMENT '型号',
    spec          VARCHAR(100) NOT NULL DEFAULT '' COMMENT '规格',
    PRIMARY KEY (id),
    KEY idx_hardware_type (hardware_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品/型号主数据';
"""

DDL_PRICE_HISTORY = """
CREATE TABLE IF NOT EXISTS t_price_history (
    id         BIGINT         NOT NULL AUTO_INCREMENT COMMENT '主键',
    product_id BIGINT         NOT NULL COMMENT '商品 id',
    platform   VARCHAR(30)    NOT NULL COMMENT '平台：淘宝/京东/天猫等',
    price      DECIMAL(10, 2) NOT NULL COMMENT '当日价格（元）',
    date       DATE           NOT NULL COMMENT '采集日期',
    PRIMARY KEY (id),
    KEY idx_product_date (product_id, date),
    KEY idx_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='价格时序表';
"""

# 可选优化：给商品表加业务唯一键，让 upsert 可以走 ON DUPLICATE KEY，
# 彻底杜绝并发下的重复商品（init --add-unique-key 可执行）
DDL_UNIQUE_KEY = """
ALTER TABLE t_product ADD UNIQUE KEY uk_product_sku (hardware_type, brand, model, spec);
"""


def ensure_tables() -> List[str]:
    """确认/创建爬虫依赖的两张表，返回执行的说明信息。"""
    if not HAS_PYMYSQL:
        return ["未安装 pymysql，无法检查数据库；表结构请直接执行 后端/sql/schema.sql（通常已建好）"]
    msgs = []
    conn = pymysql.connect(
        host=config.DATABASE["host"], port=config.DATABASE["port"],
        user=config.DATABASE["user"], password=config.DATABASE["password"],
        database=config.DATABASE["database"], charset=config.DATABASE["charset"],
        autocommit=True)
    try:
        cur = conn.cursor()
        cur.execute("SHOW TABLES LIKE 't_product'")
        if not cur.fetchone():
            cur.execute(DDL_PRODUCT)
            msgs.append("已创建 t_product")
        cur.execute("SHOW TABLES LIKE 't_price_history'")
        if not cur.fetchone():
            cur.execute(DDL_PRICE_HISTORY)
            msgs.append("已创建 t_price_history")
        if not msgs:
            msgs.append("t_product / t_price_history 均已存在，无需创建")
    finally:
        conn.close()
    return msgs


def add_unique_key() -> str:
    """为 t_product 增加业务唯一键（可选优化）。"""
    if not HAS_PYMYSQL:
        return DDL_UNIQUE_KEY.strip()
    conn = pymysql.connect(
        host=config.DATABASE["host"], port=config.DATABASE["port"],
        user=config.DATABASE["user"], password=config.DATABASE["password"],
        database=config.DATABASE["database"], charset=config.DATABASE["charset"],
        autocommit=True)
    try:
        cur = conn.cursor()
        try:
            cur.execute(DDL_UNIQUE_KEY)
            return "已为 t_product 添加唯一键 uk_product_sku"
        except Exception as e:
            return "唯一键已存在或执行失败：%s" % e
    finally:
        conn.close()
