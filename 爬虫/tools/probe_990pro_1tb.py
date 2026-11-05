# -*- coding: utf-8 -*-
"""探测 990 PRO 1TB 的 ZOL 页面（2TB=1425886，试相邻 ID 并校验标题）。"""
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from hwspider.spiders import zol  # noqa: E402

for pid in (1425885, 1425887, 1425884):
    url = "https://detail.zol.com.cn/solid_state_drive/index%d.shtml" % pid
    time.sleep(3)
    html, final, err = zol.fetch(url, referer="https://detail.zol.com.cn/solid_state_drive/")
    if err:
        print("%d 抓取失败 %s" % (pid, err))
        continue
    m = re.search(r"<title>(.*?)</title>", html)
    title = m.group(1).strip() if m else ""
    price, _ = zol.parse_product(html, url)
    print("%d %s  价格: %s" % (pid, title[:70], price or "暂无"))
