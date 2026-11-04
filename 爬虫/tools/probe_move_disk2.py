# -*- coding: utf-8 -*-
"""临时探针 13（纯标准库）：move_disk 类目页是否含 ssd_usb/hdd_usb 的 6 个型号。"""
import re
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://detail.zol.com.cn/hard_drives/",
}

req = urllib.request.Request("https://detail.zol.com.cn/move_disk/", headers=HEADERS)
with urllib.request.urlopen(req, timeout=25) as resp:
    raw = resp.read()
    text = raw.decode(resp.headers.get_content_charset() or "gbk", errors="replace")
print("[move_disk] %d chars, final=%s" % (len(raw), resp.geturl()))

# 条目：<a href=".../move_disk/indexXXX.shtml">名称</a>，名称可能在 img alt
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
print("解析条目：%d" % len(pairs))

WANT = ["E61", "T7", "移动固态", "Elements", "睿品", "新小黑", "三星", "闪迪", "致态", "西数", "西部数据", "希捷", "东芝"]
hits = [p for p in pairs if any(w.lower() in p[0].lower() for w in WANT)]
print("\n相关条目（前25）：")
for n, u in hits[:25]:
    print("  %-40s %s" % (n, u))
print("\n全部条目样例（前15）：")
for n, u in pairs[:15]:
    print("  %-40s %s" % (n, u))
