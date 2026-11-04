# -*- coding: utf-8 -*-
"""临时探针 6：验证 ZOL / PConline 型号详情页是否含报价数据。"""
import sys
import re
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def get(url, encoding_hint=None):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read()
        enc = encoding_hint or resp.headers.get_content_charset() or "utf-8"
        return resp.status, resp.geturl(), raw.decode(enc, errors="replace"), raw


def main():
    # 1) ZOL CPU 分类页：抽出第一个产品链接
    st, url, text, _ = get("https://detail.zol.com.cn/cpu/", "gbk")
    print("[ZOL分类页] HTTP %d, %d chars" % (st, len(text)))
    links = re.findall(r'href="(//detail\.zol\.com\.cn/cpu/[^"]+/)"', text)
    print("产品链接样例: %s" % links[:5])
    if links:
        detail = "https:" + links[0]
        st2, u2, t2, _ = get(detail, "gbk")
        print("\n[ZOL型号页] %s -> HTTP %d, %d chars, 最终URL: %s" % (detail, st2, len(t2), u2))
        for m in ["参考价格", "参考价", "¥", "￥", "price", "报价", "经销商"]:
            idx = t2.find(m)
            print("  含 %r -> %s" % (m, ("位置 %d" % idx) if idx >= 0 else "无"))
        prices = re.findall(r"[\d]{3,6}(?:\.\d+)?元", t2[:60000])
        print("  价格样例: %s" % prices[:8])

    # 2) PConline CPU 分类页 → 产品链接
    st, url, text, _ = get("https://product.pconline.com.cn/cpu/intel/", "gb2312")
    print("\n[PConline分类页] HTTP %d, %d chars" % (st, len(text)))
    links = re.findall(r'href="(//product\.pconline\.com\.cn/cpu/[^"/]+/\d+\.html)"', text)
    print("产品链接样例: %s" % links[:5])
    if links:
        detail = "https:" + links[0]
        st2, u2, t2, _ = get(detail, "gb2312")
        print("[PConline型号页] %s -> HTTP %d, %d chars" % (detail, st2, len(t2)))
        for m in ["参考价格", "参考价", "¥", "￥", "报价", "经销商", "价格"]:
            idx = t2.find(m)
            print("  含 %r -> %s" % (m, ("位置 %d" % idx) if idx >= 0 else "无"))
        prices = re.findall(r"[\d]{3,6}(?:\.\d+)?元", t2[:60000])
        print("  价格样例: %s" % prices[:8])


if __name__ == "__main__":
    main()
