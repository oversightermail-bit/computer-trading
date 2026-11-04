# -*- coding: utf-8 -*-
"""临时探针 5：实测替代数据源（比价站 / 报价站 / 联盟接口）的可抓性。

全部用标准库，无副作用。目标：找到"不用登录 Cookie 也能稳定抓到真实价格"的源。
"""
import sys
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding="utf-8")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

KW = "i5-12400F"
TARGETS = [
    # 比价/导购站：聚合三大平台价格，反爬温和
    ("慢慢买搜索", "https://www.manmanbuy.com/search.aspx?key=%s" % KW),
    ("什么值得买搜索", "https://search.smzdm.com/?c=home&s=%s&v=b" % KW),
    ("惠惠网搜索", "http://www.huihui.cn/all?q=%s" % KW),
    # 专业硬件报价站：只做硬件，天然适合本项目目录
    ("中关村在线搜索", "https://detail.zol.com.cn/search/?keyword=%s" % KW),
    ("中关村CPU报价", "https://detail.zol.com.cn/cpu/"),
    ("太平洋CPU报价", "https://product.pconline.com.cn/cpu/intel/"),
    # 京东联盟开放平台（官方 API，未带 key 只验证连通性）
    ("京东联盟API探测", "https://api.jd.com/routerjson"),
]


def probe(name, url):
    print("=" * 72)
    print("[%s] %s" % (name, url))
    if url is None:
        print("跳过（URL 待定）")
        return
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
            head = text[:300].replace("\n", " ").replace("\r", " ")
            print("前300字符: %s" % head)
            for marker in ["12400F", "i5", "price", "价格", "元",
                           "item.jd.com", "search.zol", "product"]:
                idx = text[:40000].find(marker)
                if idx >= 0:
                    print("  含 %r @%d" % (marker, idx))
    except urllib.error.HTTPError as e:
        print("HTTPError: %s %s" % (e.code, e.reason))
    except Exception as e:
        print("请求异常: %r" % e)


if __name__ == "__main__":
    for n, u in TARGETS:
        probe(n, u)
