# -*- coding: utf-8 -*-
"""原始采集条目 RawItem：各平台 Spider 统一产出的数据模型。

清洗前的"原始口径"字段（price_text 可能带 ¥/促销话术），
统一交给 cleaner 做标准化，再进入入库管道。
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class RawItem:
    platform: str                    # 数据源：中关村在线（ZOL）等
    hardware_type: str               # 硬件类型编码，如 gpu
    brand: str = ""
    model: str = ""
    spec: str = ""
    price: Optional[float] = None    # 已能直接解析出的价格（元），否则 None
    price_text: str = ""             # 原始价格文本（¥、促销价等），清洗用
    shop: str = ""                   # 店铺名
    url: str = ""                    # 商品链接
    source: str = "real"             # real=真实抓取 / mock=模拟行情降级
    crawled_at: datetime = field(default_factory=datetime.now)

    @property
    def sku(self) -> str:
        """唯一商品标识：品牌|型号|规格（与文档 §四(三) 一致）"""
        return "%s|%s|%s" % (self.brand.strip(), self.model.strip(), self.spec.strip())

    @property
    def matched(self) -> bool:
        """是否与商品目录匹配成功（未匹配的条目不参与入库）"""
        return bool(self.brand and self.model and self.hardware_type)
