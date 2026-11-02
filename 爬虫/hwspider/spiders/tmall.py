# -*- coding: utf-8 -*-
"""平台 Spider：天猫。

搜索页 list.tmall.com/search_product.htm 为普通 HTML 列表，
用 lxml（等价文档所述 BeautifulSoup 方案）按 CSS 选择器解析。
"""
from typing import List, Tuple

from lxml import html as lxml_html

from .. import config
from ..fetcher import fetch
from ..items import RawItem
from ..loader import keywords_for, match_catalog

PLATFORM = "天猫"
SEARCH_URL = "https://list.tmall.com/search_product.htm?q={kw}&s={offset}"
LOGIN_HOSTS = ("login.tmall.com", "login.taobao.com")


def search_url(keyword: str, page: int = 1) -> str:
    return SEARCH_URL.format(kw=keyword.replace(" ", "+"), offset=(page - 1) * 60)


def detect_ban(html: str, final_url: str) -> bool:
    if any(h in final_url for h in LOGIN_HOSTS):
        return True
    low = (html or "")[:4000].lower()
    return any(m in low for m in ["captcha", "验证码", "亲，请登录", "安全验证"])


def parse_search(html: str, base_url: str, hardware_type: str) -> Tuple[List[RawItem], bool]:
    """解析天猫搜索结果页：.product-iWrap 卡片 → 标题/价格/店铺。"""
    banned = detect_ban(html, base_url)
    if banned or not html:
        return [], banned
    items: List[RawItem] = []
    try:
        tree = lxml_html.fromstring(html)
    except Exception:
        return [], banned

    for card in tree.xpath("//*[contains(@class,'product-iWrap')]"):
        title_node = card.xpath(".//*[contains(@class,'productTitle')]//a")
        title = (title_node[0].get("title", "") or
                 title_node[0].text_content()).strip() if title_node else ""
        price_node = card.xpath(".//*[contains(@class,'productPrice')]//em")
        price_text = (price_node[0].get("title", "") or
                      price_node[0].text_content()).strip() if price_node else ""
        shop_node = card.xpath(".//*[contains(@class,'productShop-name')]")
        shop = shop_node[0].text_content().strip() if shop_node else ""
        matched = match_catalog(title, hardware_type)
        if not matched:
            continue
        url = ""
        if title_node:
            url = title_node[0].get("href", "")
            if url.startswith("//"):
                url = "https:" + url
        items.append(RawItem(
            platform=PLATFORM, hardware_type=hardware_type,
            brand=matched["brand"], model=matched["model"], spec=matched["spec"],
            price=None, price_text=price_text, shop=shop, url=url, source="real"))
    return items, banned


def collect(hardware_types: List[str], limit_pages: int = None) -> Tuple[List[RawItem], dict]:
    """无 Scrapy 环境下的直接抓取。"""
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


try:
    import scrapy  # type: ignore

    class TmallSpider(scrapy.Spider):
        name = "tmall"
        allowed_domains = ["tmall.com"]
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
                            search_url(kw, page), callback=self.parse,
                            meta={"hardware_type": hw_type}, dont_filter=True)

        def parse(self, response):
            page_items, banned = parse_search(
                response.text, response.url, response.meta["hardware_type"])
            self.banned = self.banned or banned
            for it in page_items:
                yield it

except ImportError:  # pragma: no cover
    class TmallSpider:  # type: ignore
        name = "tmall"
        banned = False
