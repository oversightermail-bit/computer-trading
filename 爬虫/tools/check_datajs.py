# -*- coding: utf-8 -*-
"""校验 data.js 新格式。"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8")
t = io.open("前端/assets/js/data.js", encoding="utf-8").read()
i = t.find('"platforms"')
print("platforms 列表:", t[i:i + 40].replace("\n", " ").strip())
print("perf 出现次数:", t.count('"perf"'))
print("中关村在线 出现次数:", t.count("中关村在线"))
print("京东/天猫/淘宝 残留:", any(w in t for w in ("京东", "天猫", "淘宝")))
# 第一个商品对象样例
j = t.find('"1": {')
print("商品1样例:", t[j:j + 130].replace("\n", " ").strip())
