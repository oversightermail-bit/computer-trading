# -*- coding: utf-8 -*-
"""从已保存的 ZOL 页面找"移动硬盘/移动固态"类目链接与关键词。"""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

t = open("tools/probe_hard_drives.html", encoding="utf-8").read()

print("== 硬盘页里含 移动/固态/硬盘 的类目链接 ==")
for href, name in sorted(set(re.findall(
        r'<a[^>]+href="(//detail\.zol\.com\.cn/[a-z0-9_]+/)"[^>]*>([^<]{0,16})</a>', t))):
    if any(w in name for w in ("移动", "固态", "硬盘")):
        print("  %-16s %s" % (name, href))

print("\n== 硬盘页里所有 /detail.zol.com.cn/ 二级目录 slug ==")
print(sorted(set(re.findall(r"detail\.zol\.com\.cn/([a-z0-9_]+)/", t))))

print("\n== 硬盘页含'移动'的文本上下文 ==")
for m in list(re.finditer(r"移动[^<]{0,12}", t))[:10]:
    print("  ", m.group(0))
