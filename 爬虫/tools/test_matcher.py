# -*- coding: utf-8 -*-
"""匹配器离线单测：把可疑标题直接喂给 match_catalog，定位 MISS 原因。"""
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

from hwspider.spiders import zol

CASES = [
    ("ssd_usb", "三星T7（1TB）"),
    ("ssd_usb", "三星T7（2TB）"),
    ("ssd", "三星 990 PRO NVMe M.2"),
    ("ssd", "三星 990 PRO 1TB"),
    ("ssd", "三星 990 PRO 2TB"),
    ("mem_desktop", "金士顿骇客神条FURY 16GB DDR4 3200（HX432C18FB/16-SP）"),
    ("mem_desktop", "金士顿骇客神条FURY 16GB DDR5 6000"),
    ("mem_desktop", "金士顿FURY 32GB DDR5 6000"),
    ("mem_laptop", "三星16GB DDR4 3200 笔记本内存"),
    ("mem_laptop", "三星32GB DDR5 5600 笔记本内存"),
    ("gpu", "七彩虹iGame GeForce RTX 4060 Ti Ultra W OC 8G"),
    ("gpu", "七彩虹iGame GeForce RTX 4060 Ultra W OC 8G"),
    ("keyboard", "雷蛇黑寡妇蜘蛛V4"),
    ("monitor", "小米G27Q 27英寸 2K"),
    ("mouse", "罗技GPW2 无线游戏鼠标"),
]

for hw, title in CASES:
    r = zol.match_catalog(title, hw)
    print("%-14s %-42s -> %s" % (hw, title,
                                 ("%s %s %s" % (r["brand"], r["model"], r["spec"])) if r else "None"))
