# -*- coding: utf-8 -*-
"""数据清洗与价格标准化（文档 §四(三)）。

各平台字段口径不一（促销价/到手价/优惠券、¥ 符号、千分位、缺失值），
统一用 pandas 归一化为可比较字段：
  1. 去除货币符号与千分位，统一为浮点"元"；
  2. 缺失/非正值/异常抖动（偏离目录基准价 50% 以上）剔除；
  3. SKU = 品牌|型号|规格，作为唯一商品标识；
  4. 同一 SKU 同平台同一天多店铺报价取中位数，消除重复与极端促销抖动。
"""
import re
from typing import Dict, List

import pandas as pd

from .loader import catalog_by_sku

# 价格文本里的货币符号 / 全角逗号
_CLEAN_RE = r"[¥￥,，\s]"


def normalize_price(text: str) -> float:
    """'￥1,299.00' / '1299元' / '到手价 1299' → 1299.0；失败返回 NaN。"""
    if text is None:
        return float("nan")
    s = str(text)
    # 提取第一个数字串（容忍前后文案），避免正则替换把话术一起留下
    m = re.search(r"\d+(?:\.\d+)?", s.replace(",", "").replace("，", ""))
    if not m:
        return float("nan")
    try:
        return round(float(m.group(0)), 2)
    except ValueError:
        return float("nan")


def clean(raw_items: List) -> pd.DataFrame:
    """原始条目 → 清洗后的 DataFrame（含 sku 与最终价格列）。

    返回列：platform, hardware_type, brand, model, spec, sku, price, shop, url,
    source, crawled_at, date（采集日期）。
    """
    if not raw_items:
        return pd.DataFrame(columns=[
            "platform", "hardware_type", "brand", "model", "spec", "sku",
            "price", "shop", "url", "source", "crawled_at", "date"])

    df = pd.DataFrame([{
        "platform": it.platform,
        "hardware_type": it.hardware_type,
        "brand": it.brand,
        "model": it.model,
        "spec": it.spec,
        "price": it.price,
        "price_text": it.price_text,
        "shop": it.shop,
        "url": it.url,
        "source": it.source,
        "crawled_at": it.crawled_at,
    } for it in raw_items])

    # 未匹配目录的条目直接剔除（品牌/型号缺失）
    df = df[df["brand"].str.len().gt(0) & df["model"].str.len().gt(0)].copy()

    # 1) 价格标准化：优先直接价格，缺失时从原始文本解析（pandas 3 严格类型：先转 float）
    df["price"] = df["price"].astype(float)
    missing = df["price"].isna()
    if missing.any():
        parsed = df.loc[missing, "price_text"].map(normalize_price).astype(float)
        df.loc[missing, "price"] = parsed
    df["price"] = df["price"].astype(float)

    # 2) 缺失/非正值剔除
    df = df[df["price"].notna() & (df["price"] > 0)].copy()

    # 3) SKU 唯一标识 + 异常抖动剔除（偏离基准价过大视为脏数据）。
    #    区间放宽到 0.3~3.0：ZOL 参考报价对老型号可能仍标官方指导价，
    #    与目录基准价（市价口径）差距可达 2 倍以上，属正常而非脏数据。
    df["sku"] = df["brand"].str.strip() + "|" + df["model"].str.strip() + "|" + df["spec"].str.strip()
    base_map: Dict[str, float] = {sku: it["base"] for sku, it in catalog_by_sku().items()}
    df["base"] = df["sku"].map(base_map)
    df = df[df["base"].notna() & (df["price"] / df["base"]).between(0.3, 3.0)].copy()

    # 4) 同 SKU 同平台同一天多店铺报价 → 中位价（文档：中位数/最低价）
    df["date"] = pd.to_datetime(df["crawled_at"]).dt.date.astype(str)
    grouped = (df.groupby(["sku", "platform", "date"], as_index=False)
               .agg(price=("price", "median"),
                    hardware_type=("hardware_type", "first"),
                    brand=("brand", "first"), model=("model", "first"),
                    spec=("spec", "first"), shop=("shop", lambda s: "、".join(
                        dict.fromkeys(x for x in s if x))),
                    url=("url", "first"), source=("source", "first")))
    grouped["price"] = grouped["price"].round(2)
    return grouped[["platform", "hardware_type", "brand", "model", "spec",
                    "sku", "price", "shop", "url", "source", "date"]]


def overwrite_date(df: pd.DataFrame, target_date: str) -> pd.DataFrame:
    """回填场景：把清洗结果的采集日期统一改写为目标日期（历史补数用）。"""
    out = df.copy()
    out["date"] = target_date
    return out
