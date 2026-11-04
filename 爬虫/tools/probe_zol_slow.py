# -*- coding: utf-8 -*-
"""临时探针 10：慢速重测被防刷的 ZOL 类目（完整浏览器头，间隔 15s）。

结论写入 tools/zol_slug_probe.txt，供后续代码核对。
"""
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Referer": "https://www.zol.com.cn/",
    "sec-ch-ua": '"Chromium";v="126", "Not)A;Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-site",
    "Upgrade-Insecure-Requests": "1",
}

TARGETS = [
    ("vga 显卡", "https://detail.zol.com.cn/vga/"),
    ("solid_state_drive 固态", "https://detail.zol.com.cn/solid_state_drive/"),
    ("mice 鼠标", "https://detail.zol.com.cn/mice/"),
    ("mobile_hard_disk 移动硬盘", "https://detail.zol.com.cn/mobile_hard_disk/"),
    ("mobiledisk 移动硬盘2", "https://detail.zol.com.cn/mobiledisk/"),
    ("lcd 显示器复测", "https://detail.zol.com.cn/lcd/"),
]

out_lines = []


def probe(name, url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read()
            enc = resp.headers.get_content_charset() or "gbk"
            text = raw.decode(enc, errors="replace")
            line = "[%s] %s -> HTTP %d, %d chars, final=%s" % (
                name, url, resp.status, len(raw), resp.geturl())
            if "checking" in resp.geturl() or "防刷" in text[:2000]:
                line += "  ❌防刷验证"
            else:
                products = len(set(__import__("re").findall(
                    r'detail\.zol\.com\.cn/[a-z0-9_]+/index\d+\.shtml', text)))
                line += "  ✅ 商品链接数≈%d" % products
            print(line, flush=True)
            out_lines.append(line)
    except Exception as e:
        line = "[%s] %s -> 异常 %r" % (name, url, e)
        print(line, flush=True)
        out_lines.append(line)


if __name__ == "__main__":
    for n, u in TARGETS:
        probe(n, u)
        time.sleep(15)
    with open("tools/zol_slug_probe.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines))
    print("done -> tools/zol_slug_probe.txt")
