# -*- coding: utf-8 -*-
"""临时探针 4：检查京东详情页 HTML 中是否含价格/标题/店铺信息。"""
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

url = "https://item.jd.com/100012043978.html"
req = urllib.request.Request(url, headers={
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://www.jd.com/",
})
with urllib.request.urlopen(req, timeout=15) as resp:
    text = resp.read().decode("utf-8", errors="replace")

out = "tools/probe_jd_item.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(text)
print("已保存 %s（%d bytes）" % (out, len(text)))

for marker in ["p.3.cn", "prices/mgets", "pduid", "pageConfig", "价 格",
               "￥", "&yen;", "itemInfo", "name:", "shopId", "shop_name",
               "desc(", "cat:", "venderId"]:
    idx = text.find(marker)
    print("%-14s -> %s" % (marker, ("位置 %d" % idx) if idx >= 0 else "不存在"))
