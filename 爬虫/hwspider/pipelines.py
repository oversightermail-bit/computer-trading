# -*- coding: utf-8 -*-
"""Scrapy 清洗入库管道（文档 §四(二) Pipeline）。

缓冲 Spider 产出的 RawItem，在 spider_closed 时复用直抓路径同一套
清洗 → 标准化 → 去重 → 入库 → 推荐 → 监控 逻辑（engine.ingest），
保证 Scrapy 与直抓两种引擎落库口径完全一致。
"""
import logging
from datetime import datetime

from . import config
from .engine import ingest
from .monitor import PlatformStats

log = logging.getLogger("hwspider.pipelines")

try:
    from scrapy import signals  # type: ignore
    HAS_SCRAPY = True
except ImportError:  # pragma: no cover
    HAS_SCRAPY = False

if HAS_SCRAPY:

    class CleanStorePipeline:
        """收集条目 → spider 结束时统一清洗入库（默认 mysql sink）。"""

        def __init__(self):
            self.items = []
            self.banned = False

        @classmethod
        def from_crawler(cls, crawler):
            p = cls()
            crawler.signals.connect(p.spider_opened, signal=signals.spider_opened)
            crawler.signals.connect(p.spider_closed, signal=signals.spider_closed)
            return p

        def spider_opened(self, spider):
            self.items = []

        def process_item(self, item, spider):
            self.items.append(item)
            return item

        def spider_closed(self, spider):
            if not self.items:
                return
            platform = _platform_of(spider)
            stats = PlatformStats(platform)
            stats.requested = getattr(spider, "crawler", None) and \
                spider.crawler.stats.get_value("downloader/request_count", 0) or 0
            stats.parsed = len(self.items)
            stats.banned = bool(getattr(spider, "banned", False))
            if stats.banned or stats.parsed == 0:
                # 与直抓 auto 模式一致：封禁/零数据自动切换模拟行情
                from . import mockmarket
                self.items = mockmarket.items_for(platform)
                stats.switched_to_mock = True
            try:
                summary = ingest({platform: self.items}, [stats],
                                 sink="mysql", round_id=datetime.now().strftime("%Y%m%d%H%M%S"))
                log.info("[%s] 入库完成：清洗 %d 条，写入 %d 条",
                         platform, summary["cleaned_rows"], summary["prices_written"])
            except Exception as e:  # 入库失败不中断其他平台
                log.exception("[%s] 入库失败：%s", platform, e)


def _platform_of(spider) -> str:
    name = getattr(spider, "name", "")
    return {"jd": "京东", "taobao": "淘宝", "tmall": "天猫"}.get(name, name or config.PLATFORMS[0])
