# -*- coding: utf-8 -*-
"""平台采集器：中关村在线 ZOL（参考报价）。

策略（2026-11 实测有效）：
  1. 抓每个硬件类目的分类列表页（单页全量、不分页），解析 (商品名, 型号页链接)；
  2. 用归一化匹配把型号页链接对应回 config.CATALOG 的 58 个 SKU
     （兼容 "i5 12400F" vs "i5-12400F"、"R5 5600" vs "Ryzen 5 5600" 等写法差异）；
  3. 逐型号抓详情页，取"参考报价"（<b class="price-type">1830</b>）；
  4. 全程限速 + 重试；识别 service.zol.com.cn/checking 防刷页并上报封禁信号。

注意：ZOL 页面为 GBK 编码；ZOL 有防刷限流，切勿提高并发。
"""
import logging
import re
import time
from typing import List, Optional, Tuple

from lxml import html as lxml_html

from .. import config
from ..fetcher import fetch
from ..items import RawItem
from ..loader import catalog_by_type

PLATFORM = "中关村在线"
HOST = "https://detail.zol.com.cn"

# 品牌别名：ZOL 标题里的品牌写法 → 目录品牌（小写归一后匹配）
_BRAND_ALIAS = {
    "西数": ["西部数据", "wd", "western"],
    "Intel": ["intel", "英特尔"],
    "AMD": ["amd", "超威"],
    "NVIDIA": ["nvidia", "英伟达"],
    "金士顿": ["金士顿", "kingston"],
    "英睿达": ["英睿达", "crucial", "镁光"],
    "三星": ["三星", "samsung"],
    "西部数据": ["西部数据", "西数", "wd", "western"],
    "雷蛇": ["雷蛇", "razer"],
    "罗技": ["罗技", "logitech"],
    "小米": ["小米", "xiaomi", "红米", "redmi"],
    "达尔优": ["达尔优"],
    "双飞燕": ["双飞燕"],
    "希捷": ["希捷", "seagate"],
    "东芝": ["东芝", "toshiba"],
    "闪迪": ["闪迪", "sandisk"],
    "致态": ["致态", "zhitai"],
    "铠侠": ["铠侠", "kioxia"],
    "光威": ["光威"],
    "威刚": ["威刚", "adata"],
    "LG": ["lg"],
    "AOC": ["aoc"],
    "ATK": ["atk"],
}

_NORM_RE = re.compile(r"[\s\-_./＋+（）()·,，:：×xX]")

# 目录型号 → ZOL 标题里的实际写法（个别型号在 ZOL 的命名不同/更全）
_TITLE_OVERRIDE = {
    ("雷蛇", "黑寡妇V4"): ["黑寡妇"],           # ZOL: 黑寡妇蜘蛛V4
    ("致态", "移动固态"): ["灵·潮流版"],         # ZOL: 致态灵·潮流版（致态移动固态 1TB）
    ("金士顿", "FURY 16GB"): ["FURY Beast 16GB"],  # ZOL: 金士顿FURY Beast 16GB DDR5...
    ("金士顿", "FURY 32GB"): ["FURY Beast 32GB"],  # ZOL: 金士顿FURY Beast 32GB DDR5 6000
    ("铠侠", "RC20"): ["EXCERIA G2"],           # 铠侠 RC20 在 ZOL 名为 EXCERIA G2
    ("威刚", "XPG 32GB"): ["DDR5 6400 32GB"],   # ZOL: 威刚XPG 威龙 D500 DDR5 6400 32GB
}


def _norm(s: str) -> str:
    """归一化：小写、去分隔符、展开常见型号缩写（R5→ryzen5）。"""
    s = _NORM_RE.sub("", str(s).lower())
    s = s.replace("r5", "ryzen5").replace("r7", "ryzen7").replace("r9", "ryzen9")
    return s


def search_url(hardware_type: str) -> str:
    return config.ZOL_CATEGORIES.get(hardware_type, "")


def detect_ban(html: str, final_url: str) -> bool:
    """封禁信号：ZOL 防刷验证页（service.zol.com.cn/checking）。"""
    if "checking" in (final_url or "").lower() and "zol" in (final_url or "").lower():
        return True
    low = (html or "")[:4000].lower()
    return "防刷验证" in low or "您正在进行防刷验证" in low


def parse_listing(html: str, hardware_type: str) -> Tuple[List[Tuple[str, str]], bool, List[Tuple[str, str]]]:
    """解析分类页，返回 ([(商品名, 型号页URL)], 封禁, [(系列名, 系列页URL)])。

    ZOL 分类页不分页，单页列出该类目全部商品；条目形如
    <a href="//detail.zol.com.cn/cpu/index1440585.shtml">AMD Ryzen 5 5600</a>，
    部分条目文字为空（"去看看>>"），商品名在 img alt 或 a title 上。
    系列筛选链接（如 "RTX 4080 SUPER" → /vga/s11033/）一并返回，
    供型号未直接列出时进系列页二次定位。
    """
    banned = detect_ban(html, "")
    if banned or not html:
        return [], banned
    try:
        tree = lxml_html.fromstring(html)
    except Exception:
        return [], banned

    out: List[Tuple[str, str]] = []
    seen = set()
    for a in tree.xpath("//a[contains(@href,'index') and contains(@href,'.shtml')]"):
        href = (a.get("href") or "").strip()
        m = re.search(r"(?:detail\.zol\.com\.cn)?(/[a-z0-9_]+/index\d+\.shtml)", href)
        if not m:
            continue
        url = HOST + m.group(1)
        if url in seen:
            continue
        name = (a.text_content() or "").strip()
        if name in ("", "去看看>>", "去看看", "查看"):  # 商品名在 img alt / title 上
            imgs = a.xpath(".//img")
            name = (imgs[0].get("alt") or "").strip() if imgs else ""
            name = name or (a.get("title") or "").strip()
        if not name:
            continue
        seen.add(url)
        out.append((name, url))

    # 系列筛选链接（如 /vga/s11033/ → "RTX 4080 SUPER"）：型号未直接列出时进系列页定位
    series: List[Tuple[str, str]] = []
    seen_s = set()
    for a in tree.xpath("//a[contains(@href,'/s')]"):
        href = (a.get("href") or "").strip()
        m = re.search(r"(?:detail\.zol\.com\.cn)?(/[a-z0-9_]+/s\d+/)", href)
        if not m:
            continue
        url = HOST + m.group(1)
        if url in seen_s:
            continue
        name = (a.text_content() or "").strip()
        if not name:
            continue
        seen_s.add(url)
        series.append((name, url))
    return out, False, series


def match_catalog(title: str, hardware_type: str) -> Optional[dict]:
    """把 ZOL 商品名匹配回目录条目（归一化包含匹配，品牌可别名）。

    GPU 例外：目录品牌是芯片商（NVIDIA/AMD），ZOL 标题用板卡品牌（七彩虹/华硕等），
    因此 GPU 只按型号匹配，不校验品牌。
    """
    if not title:
        return None
    tn = _norm(title)
    pool = catalog_by_type().get(hardware_type, [])
    hits = []
    for item in pool:
        tokens = [_norm(item["model"])]
        tokens.extend(_norm(t) for t in _TITLE_OVERRIDE.get(
            (item["brand"], item["model"]), []))
        if not any(t and t in tn for t in tokens):
            continue
        if hardware_type != "gpu":
            brands = _BRAND_ALIAS.get(item["brand"], [_norm(item["brand"])])
            if not any(b in tn for b in brands):
                continue
        hits.append(item)
    if not hits:
        return None
    if len(hits) > 1:
        # 长型号优先：避免 "RTX 4060" 子串误配 "RTX 4060 Ti"
        hits.sort(key=lambda i: -len(_norm(i["model"])))
    if len(hits) == 1:
        return _reject_conflicting_spec(hits[0], title, tn)
    # 同型号多规格：用规格词（DDR4/DDR5、1TB/2TB、16GB/32GB…）在标题里细分
    for item in hits:
        spec_word = re.split(r"[ /]", item["spec"])[0]
        if spec_word and _norm(spec_word) in tn:
            return item
    return hits[0]


def _reject_conflicting_spec(item: dict, raw_title: str, title_norm: str) -> Optional[dict]:
    """单命中时防误配：标题里若出现同族但不同的规格（1TB vs 2TB、DDR4 vs DDR5），拒绝。

    容量/代际判断用原始标题（归一化会把 "T7（1TB）" 粘成 "t71tb" 造成误判）。
    标题不含规格词（如"罗技G102"）默认接受。
    """
    sw = re.split(r"[ /]", item["spec"])[0]
    sn = _norm(sw)
    cap = re.search(r"(\d+)\s*(tb|gb)", raw_title.lower())
    if cap and re.match(r"^\d+(tb|gb)$", sn):
        m = re.match(r"^(\d+)", sn)
        if m and cap.group(1) != m.group(1):
            return None  # 标题是另一个容量规格
    if sn and sn in ("ddr3", "ddr4", "ddr5"):
        other = re.search(r"ddr[345]", raw_title.lower())
        if other and other.group(0) != sn:
            return None  # 标题是另一种内存代际
    return item


def parse_title(html: str) -> str:
    """解析详情页 <title>，用于回校验：确认抓的页面确实属于目标 SKU。"""
    if not html:
        return ""
    try:
        tree = lxml_html.fromstring(html)
    except Exception:
        return ""
    title = (tree.xpath("string(//title)") or "").strip()
    # ZOL 标题常见格式： 【华硕 TUF RTX 4060 Ti ...】报价_参数_图片_论坛
    title = title.split("_参数")[0].split("】")[0].replace("【", "").strip()
    return title


def parse_product(html: str, base_url: str) -> Tuple[str, bool]:
    """解析型号详情页，返回 (参考报价文本, 封禁)。

    报价结构（实测）：
      <strong class="head-title">参考报价：</strong><b class="price-sign">￥</b>
      <b class="price-type">1830</b>
    """
    banned = detect_ban(html, base_url)
    if banned or not html:
        return "", banned
    try:
        tree = lxml_html.fromstring(html)
    except Exception:
        return "", banned
    price = (tree.xpath('string(//b[@class="price-type"])') or "").strip()
    if not price:
        price = (tree.xpath('string(//span[@class="price-type"])') or "").strip()
    if any(w in price for w in ("暂无", "面议", "停产", "无货", "即将上市")):
        return "", banned
    return price, banned


def _sleep() -> None:
    time.sleep(max(config.ANTI_CRAWL["download_delay"], 2.0))


def collect(hardware_types: List[str], limit_pages: Optional[int] = None) -> Tuple[List[RawItem], dict]:
    """无 Scrapy 环境的直抓：分类页定位 → 详情页取价。

    limit_pages 保留仅为接口兼容（ZOL 分类页不分页）。
    """
    items: List[RawItem] = []
    stats = {"requested": 0, "parsed": 0, "failed": 0, "banned": False,
             "matched": 0, "no_price": 0, "mismatch": 0, "error": ""}

    for hw_type in hardware_types:
        cat_url = search_url(hw_type)
        if not cat_url:
            stats["error"] = "类目 %s 未配置 ZOL 分类页 URL" % hw_type
            continue
        catalog_items = catalog_by_type().get(hw_type, [])
        _sleep()
        stats["requested"] += 1
        html, final_url, err = fetch(cat_url, referer="https://www.zol.com.cn/")
        if err:
            stats["failed"] += 1
            if not stats["error"]:
                stats["error"] = "分类页抓取失败：%s" % err
            continue
        listings, banned, series = parse_listing(html, hw_type)
        if banned:
            stats["banned"] = True
            break
        if not listings:
            if not stats["error"]:
                stats["error"] = "类目 %s 分类页未解析出商品" % hw_type
            continue

        # 目录条目 → 型号页 URL
        url_by_sku = {}
        for name, url in listings:
            matched = match_catalog(name, hw_type)
            if matched is None:
                continue
            sku = "%s|%s|%s" % (matched["brand"], matched["model"], matched["spec"])
            url_by_sku.setdefault(sku, url)  # 同名多链接取第一条

        # 系列筛选链接兜底：型号不在商品条目里时（如 "RTX 4080 SUPER" 只出现在
        # /vga/s11033/ 系列链接），跟进系列页再匹配一次。
        missing = [i for i in catalog_items
                   if "%s|%s|%s" % (i["brand"], i["model"], i["spec"]) not in url_by_sku]
        if missing:
            fetched_series = set()
            for sname, surl in series:
                target = [i for i in missing if match_catalog(sname, hw_type) == i]
                if not target or surl in fetched_series:
                    continue
                fetched_series.add(surl)
                _sleep()
                stats["requested"] += 1
                shtml, _, serr = fetch(surl, referer=cat_url)
                if serr:
                    stats["failed"] += 1
                    continue
                slist, sbanned, _ = parse_listing(shtml, hw_type)
                if sbanned:
                    stats["banned"] = True
                    break
                for name, url in slist:
                    matched = match_catalog(name, hw_type)
                    if matched is None:
                        continue
                    sku = "%s|%s|%s" % (matched["brand"], matched["model"], matched["spec"])
                    url_by_sku.setdefault(sku, url)
            if stats["banned"]:
                break

        # ZOL 类目页偶发返回精简版（商品不全）：匹配缺口大时重取一次并合并
        if len(url_by_sku) < len(catalog_items) and not stats["banned"]:
            _sleep()
            stats["requested"] += 1
            html2, _, err2 = fetch(cat_url, referer="https://www.zol.com.cn/")
            if not err2:
                listings2, banned2, _ = parse_listing(html2, hw_type)
                if banned2:
                    stats["banned"] = True
                    break
                for name, url in listings2:
                    matched = match_catalog(name, hw_type)
                    if matched is None:
                        continue
                    sku = "%s|%s|%s" % (matched["brand"], matched["model"], matched["spec"])
                    url_by_sku.setdefault(sku, url)

        for item in catalog_items:
            sku = "%s|%s|%s" % (item["brand"], item["model"], item["spec"])
            # 优先类目页匹配到的链接；没有则用目录里人工指定的 zol_url 直采
            url = url_by_sku.get(sku) or item.get("zol_url")
            if not url:
                continue
            stats["matched"] += 1
            _sleep()
            stats["requested"] += 1
            html, final_url, err = fetch(url, referer=cat_url)
            if err:
                stats["failed"] += 1
                continue
            # 回校验：详情页标题必须匹配回该 SKU（防类目页/系列页错配链接，
            # 例如把 RTX 4060 Ti 记成别的卡的价格；配不上的直接丢弃）
            page_sku = None
            matched_item = match_catalog(parse_title(html), hw_type)
            if matched_item is not None:
                page_sku = "%s|%s|%s" % (matched_item["brand"], matched_item["model"],
                                         matched_item["spec"])
            if page_sku != sku:
                stats["mismatch"] += 1
                logging.getLogger("hwspider.zol").warning(
                    "型号页回校验失败（SKU 不匹配），丢弃：期望 %s，页面 %s，url=%s",
                    sku, page_sku or "未匹配", url)
                continue
            price_text, banned = parse_product(html, final_url)
            if banned:
                stats["banned"] = True
                break
            if not price_text:
                stats["no_price"] += 1
                continue
            stats["parsed"] += 1
            items.append(RawItem(
                platform=PLATFORM, hardware_type=hw_type,
                brand=item["brand"], model=item["model"], spec=item["spec"],
                price=None, price_text=price_text, shop="中关村在线参考报价",
                url=url, source="real"))
        if stats["banned"]:
            break
    return items, stats


# ---------------- Scrapy Spider（文档 §四(二) 主路径，与直抓等价） ----------------
try:
    import scrapy  # type: ignore

    class ZolSpider(scrapy.Spider):
        name = "zol"
        allowed_domains = ["zol.com.cn"]
        custom_settings = {
            "DOWNLOAD_DELAY": max(config.ANTI_CRAWL["download_delay"], 2.0),
            "CONCURRENT_REQUESTS": 1,   # ZOL 防刷，务必单并发
            "RETRY_TIMES": config.ANTI_CRAWL["retry_times"],
        }
        banned = False

        def __init__(self, hardware_types=None, limit_pages=None, **kwargs):
            super().__init__(**kwargs)
            self.hardware_types = hardware_types or sorted(
                {i["type"] for i in config.CATALOG})

        def start_requests(self):
            for hw_type in self.hardware_types:
                url = search_url(hw_type)
                if url:
                    yield scrapy.Request(url, callback=self.parse,
                                         meta={"hardware_type": hw_type})

        def parse(self, response):
            listings, banned, series = parse_listing(
                response.text, response.meta["hardware_type"])
            self.banned = self.banned or banned
            for name, url in listings:
                matched = match_catalog(name, response.meta["hardware_type"])
                if matched:
                    yield scrapy.Request(url, callback=self.parse_product,
                                         meta={"item": matched})
            # 系列筛选链接兜底（直抓路径同逻辑，Scrapy 版简化：仅跟进能匹配目录的系列）
            for sname, surl in series:
                if match_catalog(sname, response.meta["hardware_type"]):
                    yield scrapy.Request(surl, callback=self.parse,
                                         meta={"hardware_type": response.meta["hardware_type"]})

        def parse_product(self, response):
            item = response.meta["item"]
            sku = "%s|%s|%s" % (item["brand"], item["model"], item["spec"])
            # 回校验：页面标题必须匹配目标 SKU（与直抓路径同口径）
            matched = match_catalog(parse_title(response.text), item["type"])
            page_sku = None
            if matched is not None:
                page_sku = "%s|%s|%s" % (matched["brand"], matched["model"], matched["spec"])
            if page_sku != sku:
                return
            price_text, banned = parse_product(response.text, response.url)
            self.banned = self.banned or banned
            if price_text:
                yield RawItem(
                    platform=PLATFORM, hardware_type=item["type"],
                    brand=item["brand"], model=item["model"], spec=item["spec"],
                    price=None, price_text=price_text,
                    shop="中关村在线参考报价", url=response.url, source="real")

except ImportError:  # pragma: no cover
    class ZolSpider:  # type: ignore
        name = "zol"
        banned = False
