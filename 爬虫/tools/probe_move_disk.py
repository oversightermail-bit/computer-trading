# -*- coding: utf-8 -*-
"""临时探针 12：move_disk 类目页结构 + 目录型号匹配自检。"""
import sys
import re
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, ".")
from hwspider.spiders import zol  # noqa: E402

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.zol.com.cn/",
}


def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read()
        enc = resp.headers.get_content_charset() or "gbk"
        return raw.decode(enc, errors="replace")


def main():
    t = get("https://detail.zol.com.cn/move_disk/")
    print("[move_disk] %d chars" % len(t))
    print("子类/相关类目链接：")
    for href, name in sorted(set(re.findall(
            r'<a[^>]+href="(//detail\.zol\.com\.cn/[a-z0-9_]+/)"[^>]*>([^<]{0,20})</a>', t))):
        if any(w in name for w in ("移动", "固态", "硬盘", "SSD")):
            print("  %-20s %s" % (name, href))

    # 用 zol.parse_listing 解析条目
    listings, banned = zol.parse_listing(t, "hdd_usb")
    print("\n条目总数：%d，封禁：%s" % (len(listings), banned))

    # 目录匹配自检：hdd_usb / ssd_usb / gpu 三个难匹配的类目
    for hw in ("hdd_usb", "ssd_usb", "gpu", "cpu"):
        hits = []
        for name, url in listings if hw in ("hdd_usb", "ssd_usb") else []:
            m = zol.match_catalog(name, hw)
            if m:
                hits.append((name, m["model"], m["spec"]))
        if hw in ("hdd_usb", "ssd_usb"):
            print("\n[%s] 匹配到 %d 条：" % (hw, len(hits)))
            for n, mo, sp in hits[:12]:
                print("   %-40s -> %s %s" % (n, mo, sp))


if __name__ == "__main__":
    main()
