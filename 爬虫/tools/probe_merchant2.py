# -*- coding: utf-8 -*-
"""临时探针 16：ZOL 商家报价页（price.shtml）的价格提取方式。"""
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
    "Referer": "https://detail.zol.com.cn/cpu/index1403088.shtml",
}

time.sleep(12)
req = urllib.request.Request("https://detail.zol.com.cn/1404/1403088/price.shtml", headers=HEADERS)
with urllib.request.urlopen(req, timeout=25) as resp:
    text = resp.read().decode(resp.headers.get_content_charset() or "gbk", errors="replace")
print("chars:", len(text))
with open("tools/probe_price_shtml.html", "w", encoding="utf-8") as f:
    f.write(text)

for pat in [r"¥[0-9,]+", r"\d{3,6}\s*元", r"price[^<]{0,30}", r"最低[^<]{0,30}",
            r"<em[^>]*class=\"[^\"]*price[^\"]*\"[^>]*>([^<]+)<"]:
    ms = list(set(re.findall(pat, text)))[:10]
    print("%-40s -> %s" % (pat, ms if ms else "无"))

# 报价行上下文
i = text.find("元")
print("\n'元'上下文:", repr(text[i-120:i+80]) if i >= 0 else "无")
