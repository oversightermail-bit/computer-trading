# -*- coding: utf-8 -*-
"""推荐购买平台算法（文档 §四(五)）。

对同一硬件型号，比较各平台当日有效价格：
  - 取最低价平台作为默认推荐；
  - 标注与次低价的差额；
  - 差额 ≤ 阈值（config.RECOMMEND.tie_threshold）时并列展示，
    避免仅因微小差价误导用户。
后端 /api/public/price/series 会从 t_price_history 独立计算同口径的推荐，
这里同时输出运营可读的报告文件（logs/recommend_YYYY-MM-DD.{json,txt}）。
"""
import json
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from . import config


def compute(rows: List[dict], target_date: Optional[str] = None) -> List[dict]:
    """rows: 已入库的当日价格行 [{product_id, platform, price, date, brand, model, spec, ...}]。

    返回推荐列表（每型号一条）：
    {hardware_type, brand, model, spec, platform, price,
     second_platform, second_price, diff, tied}
    """
    if not rows:
        return []
    df = pd.DataFrame(rows)
    if "date" in df.columns and target_date:
        df = df[df["date"].astype(str) == target_date]
    elif "date" in df.columns:
        latest = df["date"].astype(str).max()
        df = df[df["date"].astype(str) == latest]

    out: List[dict] = []
    groups: Dict[str, pd.DataFrame] = {k: g for k, g in df.groupby("sku")}
    for sku, g in groups.items():
        # 同平台多店铺取最低价（后端同口径：当日各平台最低价再排序）
        platform_min = g.groupby("platform", as_index=False)["price"].min()
        sorted_pl = platform_min.sort_values("price").reset_index(drop=True)
        if sorted_pl.empty:
            continue
        first = sorted_pl.iloc[0]
        rec = {
            "hardware_type": g["hardware_type"].iloc[0],
            "brand": g["brand"].iloc[0],
            "model": g["model"].iloc[0],
            "spec": g["spec"].iloc[0],
            "sku": sku,
            "platform": first["platform"],
            "price": round(float(first["price"]), 2),
            "second_platform": None,
            "second_price": None,
            "diff": 0.0,
            "tied": False,
        }
        if len(sorted_pl) > 1:
            second = sorted_pl.iloc[1]
            rec["second_platform"] = second["platform"]
            rec["second_price"] = round(float(second["price"]), 2)
            rec["diff"] = round(float(second["price"] - first["price"]), 2)
            rec["tied"] = rec["diff"] <= config.RECOMMEND["tie_threshold"]
        out.append(rec)
    return out


def write_report(recommendations: List[dict], target_date: Optional[str] = None,
                 platform_stats: Optional[dict] = None) -> Path:
    """写推荐报告（json 供程序用 + txt 供人看），返回 txt 路径。

    报告目录不可写（如受限沙箱）时返回 None，不影响采集主流程。
    """
    target_date = target_date or date.today().isoformat()
    json_path = config.REPORT_DIR / ("recommend_%s.json" % target_date)
    txt_path = config.REPORT_DIR / ("recommend_%s.txt" % target_date)

    lines = ["推荐购买平台（%s）" % target_date, "=" * 60]
    lines.append("%-6s %-28s %-6s %9s %-6s %9s %8s" %
                 ("类目", "型号", "平台", "价格(元)", "次选", "次低价", "差额"))
    lines.append("-" * 60)
    for r in recommendations:
        name = config.HARDWARE_NAMES.get(r["hardware_type"], r["hardware_type"])
        model = "%s %s %s" % (r["brand"], r["model"], r["spec"])
        if len(model) > 28:
            model = model[:26] + ".."
        second = (r["second_platform"] or "-")
        second_price = ("%.2f" % r["second_price"]) if r["second_price"] is not None else "-"
        tied = "（并列）" if r["tied"] else ""
        lines.append("%-6s %-28s %-6s %9.2f %-6s %9s %8s %s" %
                     (name, model, r["platform"], r["price"], second, second_price,
                      ("%.2f" % r["diff"]) if r["diff"] else "-", tied))
    try:
        config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps({
            "date": target_date,
            "recommendations": recommendations,
            "platform_stats": platform_stats or {},
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        txt_path.write_text("\n".join(lines), encoding="utf-8")
    except OSError as e:
        import logging
        logging.getLogger("hwspider.recommend").warning("推荐报告写出失败：%s", e)
        return None
    return txt_path
