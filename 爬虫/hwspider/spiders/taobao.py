# -*- coding: utf-8 -*-
"""平台 Spider：淘宝。

搜索页 s.taobao.com/search 为服务端渲染，商品数据藏在页面内嵌 JSON
（g_page_config / __INIT_DATA__）中，用正则抽出后解析。

淘宝反爬最严：未登录直接跳登录页 → 检测到即上报封禁信号，自动切换模拟行情。
"""
import json
import re
from typing import List, Tuple

from .. import config
from ..fetcher import fetch
from ..items import RawItem
from ..loader import keywords_for, match_catalog

PLATFORM = "淘宝"
SEARCH_URL = "https://s.taobao.com/search?q={kw}&page={page}"
LOGIN_HOSTS = ("login.taobao.com", "login.taobao.com/member/login")

# 页面内嵌数据提取（两种主流结构）
_JSON_RE = re.compile(
    r'(?:g_page_config\s*=|window\.__INIT_DATA__\s*=)\s*(\{.*?\});?\s*</script>',
    re.S)


def search_url(keyword: str, page: int = 1) -> str:
    return SEARCH_URL.format(kw=keyword.replace(" ", "+"), page=page)


def detect_ban(html: str, final_url: str) -> bool:
    if any(h in final_url for h in LOGIN_HOSTS):
        return True
    low = (html or "")[:4000].lower()
    return any(m in low for m in ["captcha", "验证码", "亲，请登录", "安全验证"])


def parse_search(html: str, base_url: str, hardware_type: str) -> Tuple[List[RawItem], bool]:
    """解析淘宝搜索页内嵌 JSON 中的商品列表，返回 (条目, 封禁)。"""
    banned = detect_ban(html, base_url)
    if banned or not html:
        return [], banned

    auctions = _extract_auctions(html)
    items: List[RawItem] = []
    for a in auctions:
        title = (a.get("raw_title") or a.get("title") or "").strip()
        price_text = str(a.get("view_price") or a.get("price") or "")
        shop = (a.get("nick") or a.get("shopName") or "").strip()
        matched = match_catalog(title, hardware_type)
        if not matched:
            continue
        items.append(RawItem(
            platform=PLATFORM, hardware_type=hardware_type,
            brand=matched["brand"], model=matched["model"], spec=matched["spec"],
            price=None, price_text=price_text, shop=shop,
            url=a.get("detail_url") or base_url, source="real"))
    return items, banned


def _extract_auctions(html: str) -> List[dict]:
    """从页面内嵌 JSON 中抽出商品列表（auctions / itemsArray）。"""
    m = _JSON_RE.search(html)
    if not m:
        return []
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return []
    # 主路径：mods.itemlist.data.auctions
    node = data.get("mods", {}).get("itemlist", {}).get("data", {})
    auctions = node.get("auctions") or node.get("itemsArray") or []
    if auctions:
        return auctions
    # 兜底：递归找包含 title/raw_title 的列表
    return _deep_find_auctions(data)


def _deep_find_auctions(node, depth: int = 0) -> List[dict]:
    if depth > 6 or not isinstance(node, (dict, list)):
        return []
    if isinstance(node, list):
        if node and all(isinstance(x, dict) and ("raw_title" in x or "view_price" in x)
                        for x in node[:3]):
            return node
        for child in node:
            found = _deep_find_auctions(child, depth + 1)
            if found:
                return found
    else:
        for v in node.values():
            found = _deep_find_auctions(v, depth + 1)
            if found:
                return found
    return []


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

    class TaobaoSpider(scrapy.Spider):
        name = "taobao"
        allowed_domains = ["taobao.com"]
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
    class TaobaoSpider:  # type: ignore
        name = "taobao"
        banned = False
