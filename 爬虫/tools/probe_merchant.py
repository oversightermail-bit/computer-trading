# -*- coding: utf-8 -*-
"""临时探针 15：ZOL 商家报价接口（_j_local_price）结构 + CPU 列表对目录型号的覆盖。"""
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
    "Referer": "https://detail.zol.com.cn/",
}


def get(url, referer="https://detail.zol.com.cn/"):
    h = dict(HEADERS)
    h["Referer"] = referer
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=25) as resp:
        raw = resp.read()
        enc = resp.headers.get_content_charset() or "gbk"
        return raw.decode(enc, errors="replace")


# 1) CPU 列表页覆盖检查
t = get("https://detail.zol.com.cn/cpu/")
print("== CPU 列表对目录型号的覆盖 ==")
for m in ["13490F", "13700KF", "13700K", "12400F", "13400F", "14600KF"]:
    idx = t.find(m)
    print("  %-10s -> %s" % (m, ("位置 %d" % idx) if idx >= 0 else "不在列表"))

time.sleep(8)

# 2) R5 5600 型号页：商家报价接口
t2 = get("https://detail.zol.com.cn/cpu/index1403088.shtml")
m = re.search(r'id="_j_local_price"\s+data-url="([^"]+)"', t2)
print("\n== R5 5600 商家报价接口 ==")
print("  data-url:", m.group(1) if m else "未找到")
if m:
    u = m.group(1)
    if u.startswith("//"):
        u = "https:" + u
    elif u.startswith("/"):
        u = "https://detail.zol.com.cn" + u
    print("  请求:", u)
    time.sleep(8)
    try:
        body = get(u, referer="https://detail.zol.com.cn/cpu/index1403088.shtml")
        print("  响应前 600 字符:", body[:600].replace("\n", " "))
    except Exception as e:
        print("  异常:", repr(e)[:200])

    # 参考报价对比
    m2 = re.search(r'<b class="price-type">([^<]+)</b>', t2)
    print("\n  参考报价:", m2.group(1) if m2 else "?")
