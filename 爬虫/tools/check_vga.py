# -*- coding: utf-8 -*-
"""分析已保存的 vga 类目页：商品链接数量与结构。"""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

t = open("tools/probe_vga.html", encoding="utf-8").read()
print("vga页 chars:", len(t))
hrefs = re.findall(r'href="([^"]*index\d+\.shtml)"', t)
print("index链接总数:", len(hrefs), "唯一:", len(set(hrefs)))
named = re.findall(r'<a[^>]+href="([^"]*index\d+\.shtml)"[^>]*>([^<]{2,60})</a>', t)
print("带文字锚点:", len(named))
for u, n in named[:20]:
    print("   ", n[:50], u)
print("RTX 4060 出现次数:", t.count("RTX 4060"))
i = t.find("RTX 4060")
print("RTX 4060 上下文:", repr(t[i-150:i+250]) if i >= 0 else "无")
