# -*- coding: utf-8 -*-
"""把找到的 zol_url 写回 hwspider/config.py 的 CATALOG（按 SKU 精确插入，不改其他内容）。

用法：先运行 find_zol_urls.py 生成 tools/zol_urls_found.json，再运行本脚本。
"""
import io
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

CFG = "hwspider/config.py"
FOUND = "tools/zol_urls_found.json"

found = json.load(open(FOUND, encoding="utf-8"))
lines = io.open(CFG, encoding="utf-8").read().splitlines(keepends=True)

n_insert = 0
n_skip = 0
for i, line in enumerate(lines):
    if '"base":' not in line or '"model":' not in line:
        continue
    m = re.search(r'"brand": "([^"]+)", "model": "([^"]+)", "spec": "([^"]+)"', line)
    if not m:
        continue
    sku = "%s|%s|%s" % (m.group(1), m.group(2), m.group(3))
    if sku not in found:
        continue
    if '"zol_url"' in line:  # 已写过
        n_skip += 1
        continue
    url = found[sku]
    line = line.replace('"base":', '"zol_url": "%s", "base":' % url, 1)
    lines[i] = line
    n_insert += 1
    print("写入 %s -> %s" % (sku, url))

io.open(CFG, "w", encoding="utf-8").write("".join(lines))
print("\n完成：新增 zol_url %d 条，已存在跳过 %d 条 -> %s" % (n_insert, n_skip, CFG))
