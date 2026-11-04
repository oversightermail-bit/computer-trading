# -*- coding: utf-8 -*-
"""临时探针：用标准库直连三个平台搜索页，观察真实响应（不改动任何正式代码）。

用法：python tools/probe_real.py
"""
import sys
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding="utf-8")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

TARGETS = [
    ("京东搜索", "https://search.jd.com/Search?keyword=i5-12400F&enc=utf-8&page=1"),
    ("京东价格接口", "https://p.3.cn/prices/mgets?skuIds=J_100012043978"),
    ("淘宝搜索", "https://s.taobao.com/search?q=i5-12400F&page=1"),
    ("天猫搜索", "https://list.tmall.com/search_product.htm?q=i5-12400F&s=0"),
]


def probe(name, url):
    print("=" * 70)
    print("[%s] %s" % (name, url))
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read()
            charset = resp.headers.get_content_charset() or "utf-8"
            text = body.decode(charset, errors="replace")
            print("HTTP %d  最终URL: %s  大小: %d bytes"
                  % (resp.status, resp.geturl(), len(body)))
            head = text[:600].replace("\n", " ").replace("\r", " ")
            print("前600字符: %s" % head)
            markers = ["captcha", "验证码", "安全验证", "风险控制", "登录",
                       "passport", "login", "g_page_config", "gl-item",
                       "product-iWrap", "auctions"]
            hits = [m for m in markers if m.lower() in text[:20000].lower()]
            print("特征命中: %s" % (hits or "无"))
    except urllib.error.HTTPError as e:
        print("HTTPError: %s %s" % (e.code, e.reason))
    except Exception as e:
        print("请求异常: %r" % e)


if __name__ == "__main__":
    for n, u in TARGETS:
        probe(n, u)
