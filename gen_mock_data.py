# -*- coding: utf-8 -*-
"""解析 后端/sql/init_data.sql，生成 前端/assets/js/data.js（Mock 数据，与后端演示数据同源）。"""
import json
import os
import re

BASE = r"D:\AI电脑购买指导项目"
SQL = os.path.join(BASE, "后端", "sql", "init_data.sql")
OUT = os.path.join(BASE, "前端", "assets", "js", "data.js")

text = open(SQL, encoding="utf-8").read()

# ---- t_hardware ----
hw_pat = re.compile(r"\((\d+),\s*'([a-z_]+)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*(\d+)\)")
hardware = {}
for m in hw_pat.finditer(text):
    if m.group(2) in ("cpu", "gpu", "mem_desktop", "mem_laptop", "ssd", "ssd_usb",
                      "hdd_usb", "monitor", "keyboard", "mouse"):
        hardware[m.group(2)] = {
            "name": m.group(3), "func": m.group(4), "scene": m.group(5), "pitfall": m.group(6),
        }

# ---- t_product ----
prod_pat = re.compile(r"\((\d+),\s*'(cpu|gpu|mem_desktop|mem_laptop|ssd|ssd_usb|hdd_usb|monitor|keyboard|mouse)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*(\d+)\)")
products = {}
for m in prod_pat.finditer(text):
    products[m.group(1)] = {
        "type": m.group(2), "brand": m.group(3), "model": m.group(4), "spec": m.group(5),
        "perf": int(m.group(6)),
    }

# ---- t_price_history ----
price_pat = re.compile(r"\((\d+),\s*'([^']+)',\s*([0-9.]+),\s*CURDATE\(\)\s*-\s*INTERVAL\s*(\d+)\s*DAY\)")
prices = {}  # pid -> platform -> daysAgo -> price
for m in price_pat.finditer(text):
    pid, pf, price, d = m.group(1), m.group(2), m.group(3), int(m.group(4))
    prices.setdefault(pid, {}).setdefault(pf, {})[d] = round(float(price), 2)

# 校验：45 型号 × 1 数据源 × 30 天
total = sum(len(d) for pf in prices.values() for d in pf.values())
assert len(products) == 45, f"products={len(products)}"
assert len(prices) == 45, f"price products={len(prices)}"
assert total == 1350, f"price rows={total}"

# ---- t_subscription_plan ----
plan_pat = re.compile(r"\((\d+),\s*'([^']*)',\s*([0-9.]+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*'([^']*)',\s*(\d+)\)")
plans = []
for m in plan_pat.finditer(text):
    plans.append({
        "id": int(m.group(1)), "planName": m.group(2),
        "priceMonth": float(m.group(3)), "quotaDay": int(m.group(4)),
        "quotaMonth": int(m.group(5)), "multimodal": int(m.group(6)) == 1,
        "description": m.group(8),
    })

assert len(plans) == 4, f"plans={len(plans)}"

# ---- 输出 JS ----
js = []
js.append("/* ============================================================")
js.append(" * 前端 Mock 数据（自动生成，勿手改）")
js.append(" * 数据与 后端/sql/init_data.sql 完全同源：45 型号 × 1 数据源 × 30 天")
js.append(" * 价格数组顺序为 最早(29天前) -> 最新(今天)，与后端 series 接口一致")
js.append(" * ============================================================ */")
js.append("window.HW_DATA = " + json.dumps({
    "hardware": hardware,
    "products": products,
    "prices": prices,
    "plans": plans,
    "platforms": ["中关村在线"],
    "days": 30,
}, ensure_ascii=False, indent=2) + ";")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(js))
print("OK ->", OUT)
print("hardware:", list(hardware))
print("products:", len(products), "| price rows:", total, "| plans:", len(plans))
