# -*- coding: utf-8 -*-
"""临时探针 9：ZOL 类目页内部结构 + 缺的类目 slug + 翻页方式。"""
import sys
import re
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def get(url, enc="gbk"):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "zh-CN,zh;q=0.9"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read()
        return resp.status, resp.geturl(), raw.decode(enc, errors="replace")


def main():
    # 1) 被 meta refresh 的类目
    for name, url in [("固态硬盘", "https://detail.zol.com.cn/solid_state_drive/"),
                      ("鼠标", "https://detail.zol.com.cn/mice/")]:
        st, u, t = get(url)
        m = re.search(r'url=([^"\'>]+)', t)
        print("[%s] HTTP %d, %d chars, refresh-> %s" % (name, st, len(t), m.group(1) if m else "无"))
        if m:
            tgt = m.group(1)
            if not tgt.startswith("http"):
                tgt = "https://detail.zol.com.cn" + tgt
            st2, u2, t2 = get(tgt)
            mt = re.search(r"<title>(.*?)</title>", t2)
            print("  -> %s HTTP %d, title: %s" % (tgt, st2, (mt.group(1).strip() if mt else "?")))

    # 2) 猜测缺的类目 slug
    for name, url in [("显卡", "https://detail.zol.com.cn/vga/"),
                      ("显示器", "https://detail.zol.com.cn/lcd/"),
                      ("移动硬盘", "https://detail.zol.com.cn/mobile_hard_disk/"),
                      ("移动固态硬盘", "https://detail.zol.com.cn/mobile_ssd/"),
                      ("鼠标2", "https://detail.zol.com.cn/mouse/")]:
        try:
            st, u, t = get(url)
            m = re.search(r"<title>(.*?)</title>", t)
            refresh = re.search(r'url=([^"\'>]+)', t)
            print("[%s] %s -> HTTP %d, title: %s%s" %
                  (name, url, st, (m.group(1).strip() if m else "?"),
                   (", refresh-> " + refresh.group(1)) if refresh else ""))
        except Exception as e:
            print("[%s] %s -> 异常 %r" % (name, url, e))

    # 3) CPU 类目页：商品条目结构和翻页
    st, u, t = get("https://detail.zol.com.cn/cpu/")
    # 找商品条目块
    idx = t.find("index")
    print("\n[CPU页 index 上下文]")
    for m in re.finditer(r'<a[^>]+href="([^"]*index\d+\.shtml)"[^>]*>([^<]*)</a>', t):
        print("  %s -> %s" % (m.group(2).strip()[:40], m.group(1)))
    # 翻页：找 page / p1 / _2 等
    print("\n[CPU页翻页线索]")
    for pat in [r'href="([^"]*cpu[^"]*(?:p\d+|page|_s\d+|param)[^"]*)"[^>]*>([^<]*)<',
                r'pageCount[^,]*([\d]+)', r'总页数[：:]\s*(\d+)']:
        for m in re.finditer(pat, t):
            print("  ", m.groups())
            break


if __name__ == "__main__":
    main()
