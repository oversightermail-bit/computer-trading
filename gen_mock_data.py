# -*- coding: utf-8 -*-
"""生成 前端/assets/js/data.js（Mock 演示数据）。

数据来源改为内存导入 后端/tools/gen_sample_data.py（与 init_data.sql 完全同口径：
58 型号 × 1 数据源 × 30 天 + 基准性能分），不读取/改写 后端 目录下的文件，
避免演示数据生成受文件权限影响。
"""
import json
import os
import random
import sys

BASE = r"D:\AI电脑购买指导项目"
OUT = os.path.join(BASE, "前端", "assets", "js", "data.js")

sys.path.insert(0, os.path.join(BASE, "后端", "tools"))
import gen_sample_data as g  # noqa: E402

# ---- t_hardware ----
hardware = {}
for i, h in enumerate(g.HARDWARE):
    hardware[h[0]] = {"name": h[1], "func": h[2], "scene": h[3], "pitfall": h[4]}

# ---- t_product（性能分/依据/日期来自 perf_benchmarks.json，与后端 t_product 同口径） ----
products = {}
for i, p in enumerate(g.PRODUCTS):
    score, basis, updated = g.bench_for(p[1], p[2], p[3])
    products[str(i + 1)] = {
        "type": p[0], "brand": p[1], "model": p[2], "spec": p[3],
        "perf": score, "perfBasis": basis, "perfUpdated": updated,
    }

# ---- t_price_history（30 天模拟演示序列，键 = daysAgo，与 init_data.sql 同种子同口径） ----
prices = {}  # pid -> platform -> daysAgo -> price
for i, p in enumerate(g.PRODUCTS):
    pid = i + 1
    base = p[4]
    for pi, platform in enumerate(g.PLATFORMS):
        start = base * g.PLATFORM_FACTOR[platform] * (1 + (random.Random(pid + pi).uniform(-0.02, 0.02)))
        series = g.price_series(pid * 31 + pi * 7, start)
        prices.setdefault(str(pid), {}).setdefault(platform, {}) \
            .update({n: round(v, 2) for n, v in enumerate(series)})  # n=0 -> 29 天前

# 校验：58 型号 × 1 数据源 × 30 天
total = sum(len(d) for pf in prices.values() for d in pf.values())
assert len(products) == 58, f"products={len(products)}"
assert len(prices) == 58, f"price products={len(prices)}"
assert total == 1740, f"price rows={total}"

# ---- t_subscription_plan ----
plans = [{
    "id": pl[0], "planName": pl[1], "priceMonth": float(pl[2]),
    "quotaDay": pl[3], "quotaMonth": pl[4], "multimodal": pl[5] == 1,
    "description": pl[7],
} for pl in g.PLANS]
assert len(plans) == 4, f"plans={len(plans)}"

# ---- 输出 JS ----
js = []
js.append("/* ============================================================")
js.append(" * 前端 Mock 数据（自动生成，勿手改）")
js.append(" * 数据与 后端/sql/init_data.sql 完全同源：58 型号 × 1 数据源 × 30 天")
js.append(" * 价格数组顺序为 最早(29天前) -> 最新(今天)，与后端 series 接口一致")
js.append(" * 仅演示账号进入 Mock 模式时展示；真实模式由后端聚合 source='real' 数据")
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
