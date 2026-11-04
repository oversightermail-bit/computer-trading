# -*- coding: utf-8 -*-
"""临时探针 7：定位 ZOL/PConline 型号页与报价的真实 URL 结构。"""
import sys
import re
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def get(url, enc="utf-8"):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "zh-CN,zh;q=0.9"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read()
        return resp.status, resp.geturl(), raw.decode(enc, errors="replace")


def main():
    # ZOL 分类页：找型号链接（形如 /cpu/sXXXX/ 或 indexXXXX.shtml）
    st, u, t = get("https://detail.zol.com.cn/cpu/", "gbk")
    print("[ZOL分类页] HTTP %d, %d chars" % (st, len(t)))
    pats = re.findall(r'href="(//detail\.zol\.com\.cn/[^"]+)"', t)
    samples = sorted(set(p for p in pats if re.search(r"(s\d+|index\d+)", p)))
    print("型号页链接样例(%d种):" % len(samples))
    for s in samples[:8]:
        print("  %s" % s)

    # PConline 详情页 302 → 看 Location 去哪（用 http.client 拿头）
    import http.client
    conn = http.client.HTTPSConnection("product.pconline.com.cn", timeout=15)
    conn.request("GET", "/cpu/intel/2512899.html", headers={"User-Agent": UA})
    r = conn.getresponse()
    print("\n[PConline型号页] HTTP %d, Location: %s" % (r.status, r.getheader("Location")))
    if r.status == 302:
        loc = r.getheader("Location")
        if not loc.startswith("http"):
            loc = "https://product.pconline.com.cn" + loc
        st2, u2, t2 = get(loc, "gb2312")
        print("跟随重定向 -> HTTP %d, %d chars, URL: %s" % (st2, len(t2), u2))
        for m in ["参考价格", "参考价", "¥", "￥", "价格", "元"]:
            idx = t2.find(m)
            print("  含 %r -> %s" % (m, ("位置 %d" % idx) if idx >= 0 else "无"))
        prices = re.findall(r"[\d]{3,6}(?:\.\d+)?元", t2[:80000])
        print("  价格样例: %s" % prices[:10])


if __name__ == "__main__":
    main()
