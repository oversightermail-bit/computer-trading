# -*- coding: utf-8 -*-
"""临时探针 3：验证京东轻量接口（带 Referer / 手机版）是否可行。"""
import sys
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding="utf-8")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

TARGETS = [
    ("p.3.cn 价格(带Referer)",
     "https://p.3.cn/prices/mgets?skuIds=J_100012043978",
     {"Referer": "https://item.jd.com/100012043978.html"}),
    ("item-soa 详情价接口",
     "https://item-soa.jd.com/getWareBusiness?skuId=100012043978&cat=670,671,672",
     {"Referer": "https://item.jd.com/100012043978.html"}),
    ("京东手机版搜索",
     "https://so.m.jd.com/ware/search.action?keyword=i5-12400F",
     {"Referer": "https://so.m.jd.com/"}),
    ("京东详情页",
     "https://item.jd.com/100012043978.html",
     {"Referer": "https://www.jd.com/"}),
]


def probe(name, url, extra):
    print("=" * 70)
    print("[%s] %s" % (name, url))
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    headers.update(extra)
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read()
            charset = resp.headers.get_content_charset() or "utf-8"
            text = body.decode(charset, errors="replace")
            print("HTTP %d  最终URL: %s  大小: %d bytes" % (resp.status, resp.geturl(), len(body)))
            head = text[:400].replace("\n", " ").replace("\r", " ")
            print("前400字符: %s" % head)
            for marker in ["京东验证", "risk", "captcha", "pdos", "j_", "\"p\":",
                           "skuId", "wareId", "iconfont", "gl-item", "price"]:
                idx = text[:30000].find(marker)
                if idx >= 0:
                    print("  含 %r @%d" % (marker, idx))
    except urllib.error.HTTPError as e:
        print("HTTPError: %s %s" % (e.code, e.reason))
    except Exception as e:
        print("请求异常: %r" % e)


if __name__ == "__main__":
    for n, u, h in TARGETS:
        probe(n, u, h)
