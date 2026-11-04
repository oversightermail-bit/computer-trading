# -*- coding: utf-8 -*-
"""采集引擎：单轮编排（调度 → 采集 → 解析 → 清洗 → 入库 → 推荐 → 监控）。

mode 说明：
  - auto（默认）：先真实抓取；检测到封禁信号 / 解析零数据 / 网络失败时，
    自动把该平台切换为模拟行情（文档 §四(二) 监控与自动切换策略）；
  - real：只走真实抓取，失败不降级；
  - mock：直接使用模拟行情（演示/回填）。
"""
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

from . import cleaner, config, mockmarket, monitor, recommend, storage
from .items import RawItem
from .monitor import PlatformStats
from .spiders import base

log = logging.getLogger("hwspider.engine")

PLATFORM_SPIDER_NAME = {"京东": "jd", "天猫": "tmall", "淘宝": "taobao",
                        "中关村在线": "zol"}


def collect_platform(platform: str, hardware_types: List[str],
                     mode: str, target_date: date,
                     limit_pages: Optional[int] = None) -> tuple:
    """采集单个平台，返回 (原始条目列表, 平台统计)。"""
    stats = PlatformStats(platform)
    if mode == "mock":
        items = mockmarket.items_for(platform, target_date)
        stats.source = "mock"
        stats.requested = len(items)
        stats.parsed = len(items)
        return items, stats

    collector = base.collectors().get(platform)
    if collector is None:
        stats.error = "未注册的平台采集器"
        return [], stats
    items, raw = collector(hardware_types, limit_pages)
    stats.requested = raw["requested"]
    stats.parsed = raw["parsed"]
    stats.failed = raw["failed"]
    stats.banned = raw["banned"]
    stats.error = raw["error"]

    empty = len(items) == 0
    if empty or stats.banned:
        if mode == "real":
            stats.error = stats.error or ("封禁" if stats.banned else "零解析结果")
        else:  # auto：自动切换策略
            stats.switched_to_mock = True
            items = mockmarket.items_for(platform, target_date)
            log.warning("[%s] 真实抓取失败（封禁=%s 解析=%d），已自动切换模拟行情",
                        platform, stats.banned, stats.parsed)
    return items, stats


def ingest(items_by_platform: Dict[str, List[RawItem]],
           stats_list: List[PlatformStats],
           sink: str = "mysql", out_path: Optional[Path] = None,
           overwrite: bool = True, round_id: str = "",
           target_date: Optional[str] = None, mode: str = "auto") -> dict:
    """清洗 → 入库 → 推荐 → 监控告警（直抓与 Scrapy 两条路径共用）。"""
    all_items: List[RawItem] = []
    for its in items_by_platform.values():
        all_items.extend(its)

    cleaned = cleaner.clean(all_items)
    if target_date and not cleaned.empty:
        cleaned = cleaner.overwrite_date(cleaned, target_date)

    store = storage.Storage(sink=sink, out_path=out_path)
    written_rows: List[dict] = []
    try:
        store.open()
        for _, row in cleaned.iterrows():
            store.write_price({
                "hardware_type": row["hardware_type"], "brand": row["brand"],
                "model": row["model"], "spec": row["spec"],
                "platform": row["platform"], "price": float(row["price"]),
                "date": row["date"],
            }, overwrite=overwrite)
            written_rows.append(row.to_dict())
    finally:
        store.close()

    # 推荐购买平台（清洗结果即当日入库口径，与后端聚合结果一致）
    report_path = None
    if not cleaned.empty:
        report_path = recommend.write_report(
            recommend.compute(written_rows, target_date),
            target_date=target_date or cleaned["date"].max(),
            platform_stats={s.platform: s.to_dict() for s in stats_list})

    # 监控统计与告警（mode=mock 的主动演示/回填轮次不计入连续失败）
    monitor.save_run(round_id, stats_list,
                     written=store.stats["prices_written"],
                     products=store.stats["products_upserted"], mode=mode)
    previous_failures = monitor.consecutive_failures(monitor.read_recent_stats())
    alerts = monitor.check_alerts(stats_list, previous_failures)
    alert_path = monitor.fire_alerts(alerts, round_id)

    return {
        "round_id": round_id,
        "cleaned_rows": len(cleaned),
        "prices_written": store.stats["prices_written"],
        "prices_skipped": store.stats["prices_skipped"],
        "products_upserted": store.stats["products_upserted"],
        "stats": stats_list,
        "recommend_report": report_path,
        "alert_file": alert_path,
    }


def run_once(platforms: List[str], mode: str = "auto",
             sink: str = "mysql", out_path: Optional[Path] = None,
             target_date: Optional[str] = None, overwrite: bool = True,
             limit_pages: Optional[int] = None, hardware_types: Optional[List[str]] = None
             ) -> dict:
    """执行一轮完整采集（单平台失败不影响其他平台）。"""
    target = date.fromisoformat(target_date) if target_date else date.today()
    hardware_types = hardware_types or sorted({i["type"] for i in config.CATALOG})
    round_id = datetime.now().strftime("%Y%m%d%H%M%S")

    items_by_platform: Dict[str, List[RawItem]] = {}
    stats_list: List[PlatformStats] = []
    for platform in platforms:
        try:
            items, stats = collect_platform(platform, hardware_types, mode, target,
                                            limit_pages)
        except Exception as e:  # 单平台异常不拖垮整轮
            log.exception("[%s] 采集异常", platform)
            stats = PlatformStats(platform)
            stats.error = str(e)
            items = []
            if mode == "auto":
                stats.switched_to_mock = True
                items = mockmarket.items_for(platform, target)
        items_by_platform[platform] = items
        stats_list.append(stats)

    return ingest(items_by_platform, stats_list, sink=sink, out_path=out_path,
                  overwrite=overwrite, round_id=round_id,
                  target_date=target.isoformat(), mode=mode)


def run_backfill(days: int = 30, platforms: List[str] = None,
                 sink: str = "mysql", out_path: Optional[Path] = None,
                 overwrite: bool = False) -> dict:
    """回填最近 days 天价格时序（模拟行情，幂等；已有历史默认不覆盖）。

    首次部署时执行一次即可让折线图拥有完整 30 天窗口；
    之后由每日多次调度持续追加新日期。
    """
    platforms = platforms or config.PLATFORMS
    from datetime import timedelta
    end = date.today()
    start = end - timedelta(days=days - 1)

    items_by_platform: Dict[str, List[RawItem]] = {}
    stats_list: List[PlatformStats] = []
    for platform in platforms:
        items = mockmarket.history_for(platform, start, end)
        stats = PlatformStats(platform)
        stats.source = "mock"
        stats.requested = len(items)
        stats.parsed = len(items)
        items_by_platform[platform] = items
        stats_list.append(stats)

    round_id = datetime.now().strftime("%Y%m%d%H%M%S")
    return ingest(items_by_platform, stats_list, sink=sink, out_path=out_path,
                  overwrite=overwrite, round_id=round_id, mode="mock")
