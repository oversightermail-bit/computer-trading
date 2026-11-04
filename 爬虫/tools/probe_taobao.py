# -*- coding: utf-8 -*-
"""临时探针 2：把淘宝搜索页完整保存，检查商品数据所在结构。"""
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

url = "https://s.taobao.com/search?q=i5-12400F&page=1"
req = urllib.request.Request(url, headers={
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
})
with urllib.request.urlopen(req, timeout=15) as resp:
    text = resp.read().decode("utf-8", errors="replace")

out = "tools/probe_taobao.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(text)
print("已保存 %s（%d bytes）" % (out, len(text)))

for marker in ["g_page_config", "__INIT_DATA__", "auctions", "itemsArray",
               "raw_title", "view_price", "iconfont", "mainPic", "nid",
               "data-spm", "price"]:
    idx = text.find(marker)
    print("%-18s -> %s" % (marker, ("位置 %d" % idx) if idx >= 0 else "不存在"))
