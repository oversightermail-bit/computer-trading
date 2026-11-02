# -*- coding: utf-8 -*-
"""Scrapy 全局设置（文档 §四(二) 反爬参数：UA 轮换、代理池、限速、重试）。

无 Scrapy 环境时本文件仅作为配置参考（engine 直抓路径读取 config.py 同名参数）。
"""
from . import config

BOT_NAME = "hwspider"
SPIDER_MODULES = ["hwspider.spiders"]
NEWSPIDER_MODULE = "hwspider.spiders"

# 合规与礼貌抓取：限速 + 限并发 + 重试（真实站点反爬严，速度换稳定）
ROBOTSTXT_OBEY = False
DOWNLOAD_DELAY = config.ANTI_CRAWL["download_delay"]
CONCURRENT_REQUESTS = config.ANTI_CRAWL["concurrent_requests"]
CONCURRENT_REQUESTS_PER_DOMAIN = config.ANTI_CRAWL["concurrent_requests"]
DOWNLOAD_TIMEOUT = config.ANTI_CRAWL["timeout"]
RETRY_ENABLED = True
RETRY_TIMES = config.ANTI_CRAWL["retry_times"]
RETRY_HTTP_CODES = [403, 429, 500, 502, 503]

# UA 轮换 + 代理池 + 封禁检测
DOWNLOADER_MIDDLEWARES = {
    "hwspider.middlewares.UaRotateMiddleware": 400,
    "hwspider.middlewares.ProxyPoolMiddleware": 410,
    "hwspider.middlewares.BanDetectMiddleware": 420,
}

# 清洗入库管道（与直抓路径共用同一套清洗/存储逻辑）
ITEM_PIPELINES = {
    "hwspider.pipelines.CleanStorePipeline": 300,
}

# 日志与编码
LOG_LEVEL = "INFO"
FEED_EXPORT_ENCODING = "utf-8"
