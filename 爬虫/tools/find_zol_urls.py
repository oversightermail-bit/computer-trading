# -*- coding: utf-8 -*-
"""自动为目录型号查找 ZOL 详情页链接（Bing 站内搜索 + 标题校验）。

流程：对每个 CATALOG 条目 → Bing 搜 site:detail.zol.com.cn <品牌> <型号> <规格>
     → 候选链接逐个抓取 ZOL 页标题 → 用 zol.match_catalog 校验（品牌/型号/规格）
     → 通过则记为该 SKU 的 zol_url。
结果写入 tools/zol_urls_found.json，供后续写回 config.CATALOG。
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

from hwspider import config  # noqa: E402
from hwspider.spiders import zol  # noqa: E402

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

INDEX_RE = re.compile(r"detail\.zol\.com\.cn/([a-z0-9_]+)/index\d+\.shtml")


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        enc = resp.headers.get_content_charset() or "utf-8"
        return raw.decode(enc, errors="replace")


def bing_candidates(brand, model, spec):
    q = "site:detail.zol.com.cn %s %s %s" % (brand, model, spec)
    url = "https://www.bing.com/search?q=%s&format=rss&mkt=zh-CN" % urllib.parse.quote(q)
    try:
        xml = fetch(url, timeout=20)
    except Exception as e:
        print("  [Bing 失败] %r" % e)
        return []
    return INDEX_RE.findall(xml)[:4]


def main():
    found = {}
    for i, item in enumerate(config.CATALOG, 1):
        sku = "%s|%s|%s" % (item["brand"], item["model"], item["spec"])
        hw = item["type"]
        print("[%02d/45] %s %s %s ..." % (i, hw, item["brand"], item["model"]), flush=True)
        time.sleep(2.5)  # Bing 限速
        cands = bing_candidates(item["brand"], item["model"], item["spec"])
        if not cands:
            print("        无 Bing 候选，跳过")
            continue
        ok = None
        for slug_idx in cands:
            zurl = "https://detail.zol.com.cn/%s" % slug_idx
            time.sleep(2.5)  # ZOL 限速
            try:
                html = fetch(zurl, timeout=20)
            except Exception as e:
                print("        抓取失败 %s: %r" % (zurl, e))
                continue
            m = re.search(r"<title>(.*?)</title>", html)
            title = m.group(1).strip() if m else ""
            hit = zol.match_catalog(title, hw)
            if hit == item:
                ok = zurl
                break
            print("        标题不符: %s ... %s" % (title[:44], zurl))
        if ok:
            print("        ✅ %s" % ok)
            found[sku] = ok
        else:
            print("        未找到可信页面（候选 %d 个）" % len(cands))

    with open("tools/zol_urls_found.json", "w", encoding="utf-8") as f:
        json.dump(found, f, ensure_ascii=False, indent=2)
    print("\n共找到 %d 个可信 zol_url -> tools/zol_urls_found.json" % len(found))


if __name__ == "__main__":
    main()
