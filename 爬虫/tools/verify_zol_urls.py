# -*- coding: utf-8 -*-
"""验证 web 搜索找到的候选 ZOL 型号页：抓标题 → match_catalog 校验 → 存映射。

候选为 (sku, url)；校验通过的写入 tools/zol_urls_found.json。
"""
import json
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

from hwspider.spiders import zol  # noqa: E402

CANDIDATES = [
    ("Intel|i5-13490F|10核16线程", "https://detail.zol.com.cn/cpu/index1457696.shtml"),
    ("Intel|i7-13700KF|16核24线程", "https://detail.zol.com.cn/cpu/index1429329.shtml"),
    ("光威|天策 16GB|DDR4 3200", "https://detail.zol.com.cn/memory/index1382782.shtml"),
    ("威刚|XPG 32GB|DDR5 6400", "https://detail.zol.com.cn/memory/index1984560.shtml"),
    ("金士顿|FURY 16GB|DDR5 6000", "https://detail.zol.com.cn/memory/index1416465.shtml"),
    ("三星|16GB|DDR4 3200", "https://detail.zol.com.cn/memory/index1373420.shtml"),
    ("西部数据|SN770|1TB", "https://detail.zol.com.cn/solid_state_drive/index1397885.shtml"),
    ("三星|990 PRO|2TB", "https://detail.zol.com.cn/solid_state_drive/index1425886.shtml"),
    ("铠侠|RC20|1TB", "https://detail.zol.com.cn/solid_state_drive/index1380785.shtml"),
    ("闪迪|E61|1TB", "https://detail.zol.com.cn/move_disk/index1794797.shtml"),
    ("小米|G27Q|2K 165Hz", "https://detail.zol.com.cn/lcd/index1856216.shtml"),
    ("LG|27GP850|2K 180Hz", "https://detail.zol.com.cn/lcd/index1367477.shtml"),
    ("三星|S27A800|4K 60Hz", "https://detail.zol.com.cn/lcd/index1378086.shtml"),
    ("双飞燕|KB-8|有线薄膜", "https://detail.zol.com.cn/keyboard/index313149.shtml"),
    ("罗技|M185|无线", "https://detail.zol.com.cn/Ergonomics_mouse/index287835.shtml"),
    ("双飞燕|OP-520|有线", "https://detail.zol.com.cn/mice/index275884.shtml"),
]

# 目录 SKU → 硬件类型（用于 match_catalog）
TYPE_OF = {}
for it in __import__("hwspider.config", fromlist=["CATALOG"]).CATALOG:
    TYPE_OF["%s|%s|%s" % (it["brand"], it["model"], it["spec"])] = it["type"]

found = {}
for sku, url in CANDIDATES:
    hw = TYPE_OF.get(sku)
    if not hw:
        print("SKIP 未知 SKU: %s" % sku)
        continue
    time.sleep(3)  # ZOL 限速
    try:
        html, final, err = zol.fetch(url, referer="https://detail.zol.com.cn/")
    except Exception as e:
        print("FAIL 抓取异常 %s %r" % (sku, e))
        continue
    if err:
        print("FAIL 网络 %s %s" % (sku, err))
        continue
    m = re.search(r"<title>(.*?)</title>", html)
    title = m.group(1).strip() if m else ""
    hit = zol.match_catalog(title, hw)
    price_text, _ = zol.parse_product(html, url)
    if hit is not None and "%s|%s|%s" % (hit["brand"], hit["model"], hit["spec"]) == sku:
        found[sku] = url
        print("OK   %-32s -> %s  标题: %s  价格: %s"
              % (sku, url, title[:42], price_text or "暂无"))
    else:
        print("MISS %-32s 标题不匹配: %s (%s)" % (sku, title[:52], url))

with open("tools/zol_urls_found.json", "w", encoding="utf-8") as f:
    json.dump(found, f, ensure_ascii=False, indent=2)
print("\n校验通过 %d 个 -> tools/zol_urls_found.json" % len(found))
