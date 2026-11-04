# -*- coding: utf-8 -*-
"""临时探针 11：检查 ZOL 小体积类目页（vga/mice）的真实结构：子类链接、JS 数据。"""
import sys
import re
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.zol.com.cn/",
}


def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read()
        enc = resp.headers.get_content_charset() or "gbk"
        return raw.decode(enc, errors="replace")


def inspect(name, url):
    print("=" * 72)
    print("[%s] %s" % (name, url))
    try:
        t = get(url)
    except Exception as e:
        print("异常 %r" % e)
        return
    with open("tools/probe_%s.html" % name, "w", encoding="utf-8") as f:
        f.write(t)
    print("已存 tools/probe_%s.html（%d chars）" % (name, len(t)))
    for pat, label in [
        (r'detail\.zol\.com\.cn/[a-z0-9_]+/index\d+\.shtml', "index商品链接"),
        (r'detail\.zol\.com\.cn/[a-z0-9_]+/s\d+/', "子类链接"),
        (r'<title>(.*?)</title>', "title"),
        (r'"(?:list|proList|productList|data)"', "JS列表变量"),
        (r'href="([^"]*all[^"]*)"', "全部链接"),
        (r'共\s*(\d+)\s*款', "款数"),
    ]:
        ms = list(set(re.findall(pat, t)))[:6]
        print("  %s: %s" % (label, ms if ms else "无"))


if __name__ == "__main__":
    inspect("vga", "https://detail.zol.com.cn/vga/")
    time.sleep(15)
    inspect("mice", "https://detail.zol.com.cn/mice/")
    time.sleep(15)
    inspect("hard_drives", "https://detail.zol.com.cn/hard_drives/")
