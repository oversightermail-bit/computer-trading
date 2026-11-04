# -*- coding: utf-8 -*-
"""一次性脚本：把前端演示层与文案的平台口径统一为中关村在线（ZOL）。

替换范围：
  1. 前端/assets/js/data.js —— 价格键名与 platforms 列表
  2. 前端/assets/js/api.js —— mock 默认平台列表
  3. 前端/首页/shouye.html、前端/账户/gerenxingxi.html —— 文案
"""
import io

F = "前端"
paths = {
    "%s/assets/js/data.js" % F: [
        ('    "京东",\n    "天猫",\n    "淘宝"\n', '    "中关村在线"\n'),
        ('"京东":', '"中关村在线":'),
        ('"天猫":', '"中关村在线":'),
        ('"淘宝":', '"中关村在线":'),
    ],
    "%s/assets/js/api.js" % F: [
        ("['京东', '天猫', '淘宝']", "['中关村在线']"),
    ],
    "%s/首页/shouye.html" % F: [
        ("多平台比价 · 每日更新 · AI 推荐配置", "中关村在线参考价 · 每日更新 · AI 推荐配置"),
        ("自动抓取三大平台价格", "自动抓取中关村在线（ZOL）参考报价"),
        ("爬虫采集多平台价格", "爬虫采集中关村在线参考价"),
    ],
    "%s/账户/gerenxingxi.html" % F: [
        ("爬虫采集多平台价格", "爬虫采集中关村在线参考价"),
    ],
}

for path, rules in paths.items():
    with io.open(path, encoding="utf-8") as f:
        text = f.read()
    n_total = 0
    for old, new in rules:
        n = text.count(old)
        text = text.replace(old, new)
        n_total += n
        print("%-40s %-30s x%d" % (path, old[:30], n))
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("  -> %s 共 %d 处替换完成" % (path, n_total))
print("DONE")
