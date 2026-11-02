# -*- coding: utf-8 -*-
"""Scrapy 下载器中间件：UA 轮换、代理池、封禁信号检测（文档 §四(二) 反爬）。"""
import logging
import random

from . import config

log = logging.getLogger("hwspider.middlewares")

try:
    from scrapy import signals  # type: ignore
    HAS_SCRAPY = True
except ImportError:  # pragma: no cover
    HAS_SCRAPY = False


if HAS_SCRAPY:

    class UaRotateMiddleware:
        """每次请求从 UA 池随机取一个，模拟多用户访问。"""

        @classmethod
        def from_crawler(cls, crawler):
            return cls()

        def process_request(self, request, spider):
            ua = random.choice(config.ANTI_CRAWL["user_agents"])
            request.headers.setdefault("User-Agent", ua)
            request.headers.setdefault("Accept-Language", "zh-CN,zh;q=0.9")

    class ProxyPoolMiddleware:
        """代理池轮换（config.ANTI_CRAWL.proxies 为空时直连）。"""

        @classmethod
        def from_crawler(cls, crawler):
            return cls()

        def process_request(self, request, spider):
            proxies = config.ANTI_CRAWL.get("proxies") or []
            if proxies:
                request.meta["proxy"] = random.choice(proxies)

    class BanDetectMiddleware:
        """检测响应中的封禁特征，命中即记录信号（调度层据此告警 + 切换策略）。"""

        @classmethod
        def from_crawler(cls, crawler):
            s = cls()
            crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
            return s

        def __init__(self):
            self.banned = False

        def process_response(self, request, response, spider):
            text = getattr(response, "text", "")[:4000].lower()
            markers = config.ANTI_CRAWL["ban_markers"]
            if any(m.lower() in text for m in markers):
                self.banned = True
                setattr(spider, "banned", True)
                log.warning("[%s] 检测到封禁特征：%s", spider.name, response.url)
            return response

        def spider_closed(self, spider):
            if self.banned:
                log.warning("[%s] 本轮抓取存在封禁信号，建议切换代理池或降级模拟行情",
                            spider.name)
