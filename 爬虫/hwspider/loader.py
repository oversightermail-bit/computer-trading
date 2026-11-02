# -*- coding: utf-8 -*-
"""配置与商品目录加载、SKU 匹配工具。

目录（config.CATALOG）即"可配置化扩展"的落点：新增/修改硬件类目与型号
只需改 config.py，Spider 与入库管道自动生效，无需改代码。
"""
import re
from typing import Dict, List, Optional

from . import config

_CATALOG: Optional[List[dict]] = None
_BY_TYPE: Optional[Dict[str, List[dict]]] = None
_BY_SKU: Optional[Dict[str, dict]] = None


def catalog() -> List[dict]:
    """商品目录（缓存加载）"""
    global _CATALOG
    if _CATALOG is None:
        _CATALOG = list(config.CATALOG)
    return _CATALOG


def catalog_by_type() -> Dict[str, List[dict]]:
    """按硬件类型分组的目录"""
    global _BY_TYPE
    if _BY_TYPE is None:
        _BY_TYPE = {}
        for item in catalog():
            _BY_TYPE.setdefault(item["type"], []).append(item)
    return _BY_TYPE


def catalog_by_sku() -> Dict[str, dict]:
    """SKU（品牌|型号|规格）→ 目录条目"""
    global _BY_SKU
    if _BY_SKU is None:
        _BY_SKU = {sku_of(item): item for item in catalog()}
    return _BY_SKU


def sku_of(item: dict) -> str:
    return "%s|%s|%s" % (item["brand"].strip(), item["model"].strip(), item["spec"].strip())


def keywords_for(hardware_type: str) -> List[str]:
    """某硬件类型下的采集关键词（品牌 + 型号），供 Spider 构造搜索请求"""
    return ["%s %s" % (i["brand"].strip(), i["model"].strip())
            for i in catalog_by_type().get(hardware_type, [])]


def all_keywords() -> Dict[str, List[str]]:
    """全部硬件类型 → 关键词列表"""
    return {t: keywords_for(t) for t in catalog_by_type()}


def match_catalog(title: str, hardware_type: Optional[str] = None) -> Optional[dict]:
    """把抓到的商品标题匹配回目录条目。

    规则：标题同时包含品牌与型号即命中；同一型号多规格（如 990 PRO 1TB/2TB）
    按标题中的规格词再细分，分不清时取该型号第一个规格作为默认。
    """
    title = title or ""
    pool = catalog_by_type().get(hardware_type, []) if hardware_type else catalog()
    hits = [i for i in pool
            if i["brand"] in title and i["model"].split(" ")[0] in title]
    if not hits:
        return None
    if len(hits) == 1:
        return hits[0]
    # 多规格同型号：用规格词（如 1TB/2TB/16GB/32GB）细分
    for i in hits:
        spec_word = re.split(r"[ /]", i["spec"])[0]
        if spec_word and spec_word in title:
            return i
    return hits[0]
