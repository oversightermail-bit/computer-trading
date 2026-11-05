# -*- coding: utf-8 -*-
"""爬虫子系统命令行入口。

用法示例（在 爬虫/ 目录下）：
  python run.py once                          # 单轮真实采集（默认；采不到不降级，显示暂无数据）
  python run.py once --mode mock              # 强制模拟行情（仅比赛演示；入库 source='mock'）
  python run.py once --mode real              # 只走真实抓取（与默认一致）
  python run.py once --sink sql --out logs/crawl.sql   # 输出幂等 SQL（无 pymysql 时自动如此）
  python run.py backfill --days 30            # 回填最近 30 天模拟时序（仅演示，幂等）
  python run.py schedule                      # 每日 08/12/18/22 点定时采集
  python run.py report                        # 查看最近抓取统计与推荐报告
  python run.py init                          # 检查/创建 t_product、t_price_history

依赖安装：pip install -r requirements.txt

口径说明（2026-11-05 起）：默认只写真实采集价；与目录基准价偏差超 ±30% 的
价格按错配/脏数据丢弃（当日不写入 → 后端自动沿用上一真实价），
型号页标题回校验不匹配的同样丢弃。模拟价仅在显式 --mode mock 时写入，
且 source='mock'，后端聚合只读 source='real'，绝不会冒充真实价。
"""
import argparse
import logging
import sys
from datetime import date
from pathlib import Path

try:  # Windows 控制台默认 GBK，统一 UTF-8 输出避免中文乱码
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from hwspider import config, engine, monitor, storage  # noqa: E402


def _setup_logging(level: str) -> None:
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    handlers = [logging.StreamHandler(sys.stdout)]
    try:  # 日志目录不可写时（如受限沙箱）降级为仅控制台，不阻断采集
        handlers.append(logging.FileHandler(str(config.LOG_DIR / "crawler.log"),
                                            encoding="utf-8"))
    except OSError:
        print("[提示] 日志目录不可写，本轮日志仅输出到控制台：%s" % config.LOG_DIR)
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def _resolve_sink(args) -> str:
    """sink=mysql 但未安装 pymysql 时，自动降级为 sql 文件（保证任何环境可跑）。"""
    if args.sink == "mysql" and not storage.HAS_PYMYSQL:
        out = args.out or (config.LOG_DIR / "crawl_sql.sql")
        print("[提示] 未安装 pymysql，自动改用 SQL 脚本输出：%s\n"
              "       执行 pip install -r requirements.txt 后可直接入库。" % out)
        args.out = Path(out)
        return "sql"
    return args.sink


def _print_summary(s: dict) -> None:
    print("\n" + "=" * 62)
    print("采集轮次 %s 完成" % s["round_id"])
    print("-" * 62)
    print("%-6s %-8s %8s %8s %6s %6s %-10s %s" %
          ("平台", "来源", "请求", "解析", "失败", "错配", "封禁", "备注"))
    for st in s["stats"]:
        note = "自动切换模拟行情" if st.switched_to_mock else (st.error or "-")
        print("%-6s %-8s %8d %8d %6d %6d %-10s %s" %
              (st.platform, st.source, st.requested, st.parsed, st.failed,
               st.mismatch, "是" if st.banned else "否", note))
    print("-" * 62)
    print("清洗后有效行数：%d ｜ 写入价格：%d ｜ 跳过（已存在）：%d ｜ 商品 upsert：%d"
          % (s["cleaned_rows"], s["prices_written"], s["prices_skipped"],
             s["products_upserted"]))
    if s.get("mode") != "mock":
        print("未采到真实价的 SKU：沿用上一真实价 %d ｜ 暂无数据 %d"
              % (s.get("carry_over", 0), s.get("no_data", 0)))
    if s.get("recommend_report"):
        print("推荐购买平台报告：%s" % s["recommend_report"])
    if s.get("alert_file"):
        print("⚠ 告警文件：%s" % s["alert_file"])
    print("=" * 62)


def cmd_once(args) -> None:
    sink = _resolve_sink(args)
    platforms = [p.strip() for p in (args.platforms or ",".join(config.PLATFORMS)).split(",")]
    hardware_types = [t.strip() for t in args.types.split(",")] if args.types else None
    s = engine.run_once(
        platforms=platforms, mode=args.mode, sink=sink,
        out_path=args.out, target_date=args.date, overwrite=not args.no_overwrite,
        limit_pages=args.pages, hardware_types=hardware_types)
    _print_summary(s)


def cmd_backfill(args) -> None:
    sink = _resolve_sink(args)
    platforms = [p.strip() for p in (args.platforms or ",".join(config.PLATFORMS)).split(",")]
    s = engine.run_backfill(days=args.days, platforms=platforms,
                            sink=sink, out_path=args.out, overwrite=args.overwrite)
    _print_summary(s)


def cmd_schedule(args) -> None:
    from hwspider import scheduler
    print("定时调度已启动：每日 %s（时区 %s），Ctrl+C 退出"
          % (" / ".join(config.SCHEDULE["times"]), config.SCHEDULE["timezone"]))
    if args.mode:
        print("抓取模式：%s" % args.mode)

    def job():
        try:
            s = engine.run_once(platforms=config.PLATFORMS, mode=args.mode or config.DEFAULT_MODE)
            _print_summary(s)
        except Exception:
            logging.getLogger("hwspider").exception("定时任务异常")

    sched = scheduler.start(job)
    try:
        while True:
            import time
            time.sleep(3600)
    except KeyboardInterrupt:
        print("\n收到退出信号，停止调度")
        scheduler.stop(sched)


def cmd_report(args) -> None:
    stats = monitor.read_recent_stats(limit=args.limit or 10)
    if not stats:
        print("暂无抓取统计（先执行一次 python run.py once）")
        return
    print("最近 %d 轮抓取统计：" % len(stats))
    print("-" * 100)
    print("%-15s %-20s %-6s %-8s %6s %6s %7s %-8s" %
          ("轮次", "时间", "平台", "来源", "请求", "解析", "成功率", "切换"))
    for rec in stats:
        for p in rec.get("platforms", []):
            print("%-15s %-20s %-6s %-8s %6d %6d %6.0f%% %-8s" %
                  (rec["round_id"], rec["time"], p["platform"], p["source"],
                   p["requested"], p["parsed"], p["success_rate"] * 100,
                   "是" if p["switched_to_mock"] else "-"))
    print("-" * 100)
    today = date.today().isoformat()
    txt = config.REPORT_DIR / ("recommend_%s.txt" % today)
    if txt.exists():
        print("\n" + txt.read_text(encoding="utf-8"))


def cmd_init(args) -> None:
    for msg in storage.ensure_tables():
        print(msg)
    if args.add_unique_key:
        print(storage.add_unique_key())


def main() -> None:
    parser = argparse.ArgumentParser(description="硬件价格比价网站 · 数据采集子系统")
    sub = parser.add_subparsers(dest="command", required=True)

    p_once = sub.add_parser("once", help="单轮采集")
    _add_common(p_once)
    p_once.add_argument("--date", help="采集日期 YYYY-MM-DD（mock/jsonl/sql 用；真实抓取固定为今天）")

    p_back = sub.add_parser("backfill", help="回填最近 N 天价格时序（幂等）")
    _add_common(p_back)
    p_back.add_argument("--days", type=int, default=config.SCHEDULE["backfill_days"])
    p_back.add_argument("--overwrite", action="store_true",
                        help="覆盖已有历史价格（默认跳过已有日期）")

    p_sch = sub.add_parser("schedule", help="启动每日多次定时调度")
    p_sch.add_argument("--mode", choices=["auto", "real", "mock"], default="auto")

    sub.add_parser("report", help="查看统计与推荐报告").add_argument("--limit", type=int)

    p_init = sub.add_parser("init", help="检查/创建数据库表")
    p_init.add_argument("--add-unique-key", action="store_true",
                        help="给 t_product 增加业务唯一键（可选优化）")

    args = parser.parse_args()
    _setup_logging(getattr(args, "log_level", "info"))
    if args.command == "once":
        cmd_once(args)
    elif args.command == "backfill":
        cmd_backfill(args)
    elif args.command == "schedule":
        cmd_schedule(args)
    elif args.command == "report":
        cmd_report(args)
    elif args.command == "init":
        cmd_init(args)


def _add_common(p) -> None:
    p.add_argument("--mode", choices=["auto", "real", "mock"], default=config.DEFAULT_MODE,
                   help="real=只写真实采集价（默认）；auto=同 real（保留兼容）；"
                        "mock=仅比赛演示/回填，入库 source='mock'")
    p.add_argument("--platforms", help="平台列表，逗号分隔，如 中关村在线")
    p.add_argument("--types", help="硬件类型编码，逗号分隔，如 cpu,gpu")
    p.add_argument("--sink", choices=["mysql", "sql", "jsonl"], default="mysql")
    p.add_argument("--out", type=Path, help="sink=sql/jsonl 时的输出文件")
    p.add_argument("--pages", type=int, help="每关键词最大翻页数（默认取配置）")
    p.add_argument("--no-overwrite", action="store_true",
                   help="当日已存在的价格不覆盖（默认覆盖为最新价）")
    p.add_argument("--log-level", default="info")


if __name__ == "__main__":
    main()
