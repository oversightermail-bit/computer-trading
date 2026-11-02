# -*- coding: utf-8 -*-
"""模拟行情数据源（封禁/离线时的降级策略，文档 §四(二) 监控与自动切换）。

真实平台返回验证码/风险页、或网络不可达时，Spider 上报"封禁信号"，
调度层自动把该平台切换为模拟行情：用固定种子的随机游走生成
"商品 × 平台 × 日期"的确定性价格（与后端 tools/gen_sample_data.py 同思路），
保证 采集→清洗→入库→折线 全链路在演示环境始终可跑通。

确定性保证：随机游走锚定固定纪元（2025-01-01），任意目标日期先取"该日
之前全量游走"的末值，因此同一天多次运行 / 回填与日更，同一
(sku, 平台, 日期) 价格完全一致，不会产生自相矛盾的历史数据。
"""
import hashlib
import random
from datetime import date, datetime, time, timedelta
from typing import List, Optional

from . import config
from .items import RawItem
from .loader import catalog

# 随机游走锚点：所有日期相对该纪元取步数，保证序列全局一致
_EPOCH = date(2025, 1, 1)


def _seed(*parts: str) -> int:
    return int(hashlib.md5("|".join(parts).encode("utf-8")).hexdigest(), 16) % (2 ** 32)


def _step_index(target: date) -> int:
    return (target - _EPOCH).days


def _walk_head(sku: str, platform: str, upto: date, base: float):
    """从纪元游走到 upto（含）的价格序列：固定种子，逐日 ±波动并夹在区间内。"""
    factor = config.PLATFORM_FACTOR.get(platform, 1.0)
    rng = random.Random(_seed(sku, platform, "walk"))
    price = base * factor * (1 + rng.uniform(-0.02, 0.02))
    floor = base * factor * config.MOCK["floor_ratio"]
    cap = base * factor * config.MOCK["cap_ratio"]
    vals = []
    for _ in range(_step_index(upto) + 1):
        drift = rng.uniform(-config.MOCK["volatility"], config.MOCK["volatility"])
        price = max(floor, min(cap, price * (1 + drift)))
        vals.append(round(price, 2))
    return vals  # vals[k] = 纪元后第 k 天的价格


def price_on(sku: str, platform: str, target: date, base: float) -> float:
    """某商品某平台某日的模拟价格（确定性）。"""
    return _walk_head(sku, platform, target, base)[-1]


def series(sku: str, platform: str, end: date, days: int, base: float) -> List[float]:
    """连续 days 天（含 end 当天）的模拟价格序列，下标 0 = 最旧。"""
    start_idx = _step_index(end) - days + 1
    head = _walk_head(sku, platform, end, base)
    return head[start_idx:]


def promo(sku: str, platform: str, target: date, price: float) -> float:
    """按天决定的小概率促销价（确定性，同日多跑结果一致）。"""
    rng = random.Random(_seed(sku, platform, target.isoformat(), "promo"))
    if rng.random() < config.MOCK["promo_prob"]:
        return round(price * config.MOCK["promo_discount"], 2)
    return price


def items_for(platform: str, target: Optional[date] = None) -> List[RawItem]:
    """生成某平台全部目录商品的当日模拟行情原始条目（含小概率促销）。"""
    target = target or date.today()
    out: List[RawItem] = []
    for item in catalog():
        sku = "%s|%s|%s" % (item["brand"], item["model"], item["spec"])
        raw = price_on(sku, platform, target, item["base"])
        price = promo(sku, platform, target, raw)
        out.append(RawItem(
            platform=platform,
            hardware_type=item["type"],
            brand=item["brand"],
            model=item["model"],
            spec=item["spec"],
            price=price,
            price_text="%.2f" % price,
            shop="模拟行情·自营/旗舰店",
            url="(mock)",
            source="mock",
            crawled_at=datetime.combine(target, time.min),
        ))
    return out


def history_for(platform: str, start: date, end: date) -> List[RawItem]:
    """回填历史：start..end 每天、每个商品、每个平台一条（幂等，可重复执行）。"""
    out: List[RawItem] = []
    day = start
    while day <= end:
        out.extend(items_for(platform, day))
        day += timedelta(days=1)
    return out
