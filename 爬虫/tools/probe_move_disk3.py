# -*- coding: utf-8 -*-
"""临时探针 14：move_disk 全部条目里核对 6 个 ssd_usb/hdd_usb 目录型号的覆盖情况。"""
import re
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://detail.zol.com.cn/hard_drives/",
}

time.sleep(20)  # ZOL 防刷，拉大间隔
req = urllib.request.Request("https://detail.zol.com.cn/move_disk/", headers=HEADERS)
with urllib.request.urlopen(req, timeout=25) as resp:
    text = resp.read().decode(resp.headers.get_content_charset() or "gbk", errors="replace")

pairs = []
for m in re.finditer(r'<a[^>]+href="((?://detail\.zol\.com\.cn)?/move_disk/index\d+\.shtml)"[^>]*>(.*?)</a>', text, re.S):
    url = "https:" + m.group(1) if m.group(1).startswith("//") else "https://detail.zol.com.cn" + m.group(1)
    inner = m.group(2)
    name = re.sub(r"<[^>]+>", "", inner).strip()
    alt = re.search(r'alt="([^"]+)"', inner)
    if alt and (not name or name in ("去看看>>", "去看看")):
        name = alt.group(1)
    if name:
        pairs.append((name, url))

# 去重（同 URL 保留名字最长的）
best = {}
for n, u in pairs:
    if u not in best or len(n) > len(best[u][0]):
        best[u] = (n, u)
pairs = list(best.values())

for brand in ["闪迪", "致态", "希捷", "东芝", "西数", "西部数据", "三星"]:
    print("== %s ==" % brand)
    for n, u in pairs:
        if brand in n:
            print("   %-46s %s" % (n[:46], u))
print("\nE61/至尊极速相关:")
for n, u in pairs:
    if re.search(r"E61|至尊|极速", n, re.I):
        print("   %-46s %s" % (n[:46], u))
