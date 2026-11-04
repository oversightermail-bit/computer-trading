# -*- coding: utf-8 -*-
"""临时探针 8：从 ZOL 首页导航解析 10 个硬件类目的分类页 URL，
并确认分类页的商品链接与翻页方式。"""
import sys
import re
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

WANT = ["CPU", "显卡", "内存", "固态硬盘", "移动硬盘", "移动固态硬盘",
        "显示器", "键盘", "鼠标", "硬盘"]


def get(url, enc="gbk"):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "zh-CN,zh;q=0.9"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read()
        return resp.status, resp.geturl(), raw.decode(enc, errors="replace")


def main():
    st, u, t = get("https://detail.zol.com.cn/")
    print("[ZOL首页] HTTP %d, %d chars" % (st, len(t)))
    # 导航链接：<a href="//detail.zol.com.cn/xxx/">名称</a>
    nav = re.findall(r'<a[^>]+href="(//detail\.zol\.com\.cn/[a-z0-9_]+/)"[^>]*>([^<]{1,20})</a>', t)
    seen = {}
    for href, name in nav:
        name = name.strip()
        if name and name not in seen:
            seen[name] = href
    print("\n导航里与硬件相关的类目链接：")
    for name, href in sorted(seen.items()):
        if any(w in name for w in WANT):
            print("  %-10s %s" % (name, href))

    # 逐个类目页验证：标题 + 商品链接样例 + 翻页链接
    for name, href in sorted(seen.items()):
        if not any(w in name for w in WANT):
            continue
        url = "https:" + href
        try:
            st2, u2, t2 = get(url)
        except Exception as e:
            print("\n[%s %s] 异常 %r" % (name, url, e))
            continue
        m = re.search(r"<title>(.*?)</title>", t2)
        products = sorted(set(re.findall(r'detail\.zol\.com\.cn/[a-z0-9_]+/(index\d+\.shtml)',
                                         t2)))
        pages = sorted(set(re.findall(r'href="([^"]*?%s[^"]*?)"[^>]*>\s*(\d+)\s*<' % re.escape(href),
                                      t2)))
        print("\n[%s] %s -> HTTP %d, %d chars" % (name, url, st2, len(t2)))
        print("  title: %s" % (m.group(1).strip() if m else "?"))
        print("  商品链接样例(%d): %s" % (len(products), products[:4]))
        print("  翻页链接样例(%d): %s" % (len(pages), pages[:5]))


if __name__ == "__main__":
    main()
