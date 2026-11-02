# -*- coding: utf-8 -*-
"""平台 Spider：京东。

结构：search.jd.com/Search 搜索列表页（li.gl-item），价格缺失时走
p.3.cn/prices/mgets 价格接口（轻量页面，requests 处理）。

真实环境大概率触发登录墙/验证码 → 上报封禁信号，由调度层自动切换模拟行情。
"""
from typing import List, Optional, Tuple

from lxml import html as lxml_html

from .. import config
from ..fetcher import fetch
from ..items import RawItem
from ..loader import keywords_for, match_catalog

PLATFORM = "京东"
SEARCH_URL = "https://search.jd.com/Search?keyword={kw}&enc=utf-8&page={page}"
PRICE_API = "https://p.3.cn/prices/mgets?skuIds=J_{sku}"
LOGIN_HOST = "passport.jd.com"


def search_url(keyword: str, page: int = 1) -> str:
    return SEARCH_URL.format(kw=keyword.replace(" ", "+"), page=page)


def detect_ban(html: str, final_url: str) -> bool:
    """封禁信号：验证码/风险页/强制登录跳转。"""
    if LOGIN_HOST in final_url:
        return True
    low = (html or "")[:4000].lower()
    return any(m in low for m in ["captcha", "验证码", "安全验证", "风险控制"])


def parse_search(html: str, base_url: str, hardware_type: str) -> Tuple[List[RawItem], bool]:
    """解析京东搜索结果页：标题 + 价格 + 店铺 + SKU，返回 (条目, 封禁)。"""
    banned = detect_ban(html, base_url)
    if banned or not html:
        return [], banned
    items: List[RawItem] = []
    try:
        tree = lxml_html.fromstring(html)
    except Exception:
        return [], banned

    for li in tree.xpath("//li[contains(@class,'gl-item')]"):
        sku = li.get("data-sku", "")
        name_node = li.xpath(".//div[contains(@class,'p-name')]//a//em") \
            or li.xpath(".//div[contains(@class,'p-name')]//a")
        title = (name_node[0].text_content() if name_node else "").strip()
        title = title or (name_node[0].get("title", "") if name_node else "")
        price_node = li.xpath(".//div[contains(@class,'p-price')]//i")
        price_text = (price_node[0].text_content() if price_node else "").strip()
        shop_node = li.xpath(".//div[contains(@class,'p-shop')]//a")
        shop = (shop_node[0].get("title", "") or shop_node[0].text_content()).strip() \
            if shop_node else ""

        matched = match_catalog(title, hardware_type)
        if not matched:
            continue
        # 列表页价格为空（京东常见）→ 走价格接口补价
        if not price_text and sku:
            price_text = _fetch_sku_price(sku)
        items.append(RawItem(
            platform=PLATFORM, hardware_type=hardware_type,
            brand=matched["brand"], model=matched["model"], spec=matched["spec"],
            price=None, price_text=price_text, shop=shop,
            url="https://item.jd.com/%s.html" % sku if sku else base_url,
            source="real"))
    return items, banned


def _fetch_sku_price(sku: str) -> str:
    """京东价格接口（轻量 JSON 页面）：[{"p":"2299.00",...}]"""
    text, _, err = fetch(PRICE_API.format(sku=sku))
    if err or not text:
        return ""
    import json
    try:
        data = json.loads(text.strip())
        return data[0].get("p", "") if data else ""
    except (json.JSONDecodeError, IndexError, KeyError):
        return ""


def collect(hardware_types: List[str], limit_pages: int = None) -> Tuple[List[RawItem], dict]:
    """无 Scrapy 环境下的直接抓取：遍历关键词翻页，返回 (条目, 统计)。

    供 engine 调用；Scrapy 环境下由 JdSpider 走下载器完成同样工作。
    """
    limit_pages = limit_pages or config.ANTI_CRAWL["page_size"]
    items: List[RawItem] = []
    stats = {"requested": 0, "parsed": 0, "failed": 0, "banned": False, "error": ""}
    for hw_type in hardware_types:
        for kw in keywords_for(hw_type):
            for page in range(1, limit_pages + 1):
                if stats["requested"] >= config.ANTI_CRAWL["max_requests_per_platform"]:
                    break
                url = search_url(kw, page)
                stats["requested"] += 1
                html, final_url, err = fetch(url)
                if err:
                    stats["failed"] += 1
                    continue
                page_items, banned = parse_search(html, final_url, hw_type)
                stats["banned"] = stats["banned"] or banned
                if banned:
                    break
                items.extend(page_items)
                stats["parsed"] += len(page_items)
    return items, stats


# ---------------- Scrapy Spider（文档 §四(二) 主路径） ----------------
try:
    import scrapy  # type: ignore

    class JdSpider(scrapy.Spider):
        name = "jd"
        allowed_domains = ["jd.com", "3.cn"]
        custom_settings = {
            "DOWNLOAD_DELAY": config.ANTI_CRAWL["download_delay"],
            "RANDOM_UA_ROTATE": True,
        }
        banned = False

        def __init__(self, hardware_types=None, limit_pages=None, **kwargs):
            super().__init__(**kwargs)
            self.hardware_types = hardware_types or sorted(
                {i["type"] for i in config.CATALOG})
            self.limit_pages = int(limit_pages or config.ANTI_CRAWL["page_size"])

        def start_requests(self):
            for hw_type in self.hardware_types:
                for kw in keywords_for(hw_type):
                    for page in range(1, self.limit_pages + 1):
                        yield scrapy.Request(
                            search_url(kw, page),
                            callback=self.parse,
                            meta={"hardware_type": hw_type},
                            dont_filter=True)

        def parse(self, response):
            page_items, banned = parse_search(
                response.text, response.url, response.meta["hardware_type"])
            self.banned = self.banned or banned
            for it in page_items:
                yield it

except ImportError:  # 未安装 Scrapy：engine 走 collect() 直抓路径
    class JdSpider:  # type: ignore
        name = "jd"
        banned = False
