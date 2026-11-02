# -*- coding: utf-8 -*-
"""Spider 公共基类与注册表。

每个平台一个 Spider（文档 §四(二)），继承公共的反爬开关与统计属性；
无 Scrapy 环境时按平台名取 collect() 直抓函数。
"""
from typing import Dict, List, Tuple

from .. import config
from ..items import RawItem

try:
    import scrapy  # type: ignore

    class BasePriceSpider(scrapy.Spider):
        """公共逻辑：限速、翻页、封禁信号上报（详见各平台子类）。"""
        allowed_domains: List[str] = []
        banned = False  # 封禁信号：调度层据此触发告警与自动切换策略

        custom_settings = {
            "DOWNLOAD_DELAY": config.ANTI_CRAWL["download_delay"],
            "CONCURRENT_REQUESTS": config.ANTI_CRAWL["concurrent_requests"],
            "RETRY_TIMES": config.ANTI_CRAWL["retry_times"],
        }

except ImportError:  # pragma: no cover
    class BasePriceSpider:  # type: ignore
        banned = False


def collectors() -> Dict[str, object]:
    """平台名 → collect(hardware_types, limit_pages) 直抓函数。"""
    from . import jd, taobao, tmall
    return {"京东": jd.collect, "天猫": tmall.collect, "淘宝": taobao.collect}
