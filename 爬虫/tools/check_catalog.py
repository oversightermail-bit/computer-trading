# -*- coding: utf-8 -*-
"""检查当前 config.CATALOG 是否残留旧 SKU、以及新旧型号的完整性。"""
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from hwspider import config

old = [("ATK", "68"), ("达尔优", "A98"), ("东芝", "新小黑"),
       ("西部数据", "SN770"), ("三星", "32GB")]
new = [("Intel", "i5-14600KF"), ("AMD", "R5 7500F"), ("NVIDIA", "RTX 4070"),
       ("AMD", "RX 7800 XT"), ("金士顿", "FURY 32GB"), ("芝奇", "幻锋戟 32GB"),
       ("三星", "990 EVO Plus"), ("三星", "T9"), ("西数", "Elements"),
       ("HKC", "IG27Q"), ("AOC", "27G4"), ("罗技", "G502 HERO"),
       ("雷蛇", "蝰蛇V2X"), ("金士顿", "KC3000"), ("东芝", "Basics A3"),
       ("英睿达", "32GB"), ("狼蛛", "F87 Pro"), ("洛斐", "小顺 Flow")]

print("CATALOG 总数:", len(config.CATALOG))
print("旧 SKU 残留:", [(i["brand"], i["model"], i["spec"]) for i in config.CATALOG
                     if (i["brand"], i["model"]) in old])
print("新 SKU 存在:")
for b, m in new:
    hits = [(i["spec"], bool(i.get("zol_url"))) for i in config.CATALOG
            if i["brand"] == b and i["model"] == m]
    print("  %-14s %-14s %s" % (b, m, hits))
