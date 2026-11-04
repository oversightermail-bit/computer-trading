# -*- coding: utf-8 -*-
"""临时探针 17：逐类目诊断未命中 SKU 的原因（每个类目页只取一次，10 请求）。"""
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

from hwspider import config
from hwspider.spiders import zol
from hwspider.loader import catalog_by_type


def norm_of(s):
    return zol._norm(s)


total_miss = 0
for hw in sorted(config.ZOL_CATEGORIES):
    if hw not in catalog_by_type():
        continue
    items_cat = catalog_by_type()[hw]
    url = config.ZOL_CATEGORIES[hw]
    html, final, err = zol.fetch(url, referer="https://www.zol.com.cn/")
    listings, banned, _series = zol.parse_listing(html, hw)
    print("\n== %s == 条目数 %d%s" % (hw, len(listings),
                                     "（封禁！）" if banned else ""))
    if err:
        print("   fetch err:", err)
        time.sleep(3)
        continue
    miss = []
    for item in items_cat:
        sku = "%s|%s|%s" % (item["brand"], item["model"], item["spec"])
        hit = None
        for name, u in listings:
            if zol.match_catalog(name, hw) == item:
                hit = name
                break
        if hit:
            continue
        miss.append((item, sku))
    total_miss += len(miss)
    for item, sku in miss:
        mnorm = norm_of(item["model"])
        close = [n for n, u in listings if mnorm and mnorm in norm_of(n)][:3]
        print("   MISS %-10s %-14s %s  (同名近似条目: %s)"
              % (item["brand"], item["model"], item["spec"],
                 (" / ".join(close[:2]) if close else "无")))
    time.sleep(3)

print("\n总未命中：%d / 45" % total_miss)
