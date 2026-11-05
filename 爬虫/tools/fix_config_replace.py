# -*- coding: utf-8 -*-
"""修复 config.CATALOG 中 5 个替换型号的身份（上次只换了链接没换品牌/型号）。"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

FIX = {
    ("ATK", "68"): ('    {"type": "keyboard", "brand": "洛斐", "model": "小顺 Flow", "spec": "68键线性轴", '
                     '"zol_url": "https://detail.zol.com.cn/keyboard/index2147075.shtml", "base": 599},\n'),
    ("达尔优", "A98"): ('    {"type": "keyboard", "brand": "狼蛛", "model": "F87 Pro", "spec": "无线机械", '
                        '"zol_url": "https://detail.zol.com.cn/keyboard/index1969155.shtml", "base": 249},\n'),
    ("东芝", "新小黑"): ('    {"type": "hdd_usb", "brand": "东芝", "model": "Basics A3", "spec": "2TB", '
                        '"zol_url": "https://detail.zol.com.cn/move_disk/index1241704.shtml", "base": 429},\n'),
    ("西部数据", "SN770"): ('    {"type": "ssd", "brand": "金士顿", "model": "KC3000", "spec": "1TB", '
                            '"zol_url": "https://detail.zol.com.cn/solid_state_drive/index1403069.shtml", "base": 599},\n'),
    ("三星", "32GB"): ('    {"type": "mem_laptop", "brand": "英睿达", "model": "32GB", "spec": "DDR5 5600", '
                       '"zol_url": "https://detail.zol.com.cn/memory/index1857393.shtml", "base": 899},\n'),
}

path = "hwspider/config.py"
lines = io.open(path, encoding="utf-8").read().splitlines(keepends=True)
n = 0
for i, line in enumerate(lines):
    if '"brand":' not in line:
        continue
    for (b, m), newline in FIX.items():
        if '"brand": "%s"' % b in line and '"model": "%s"' % m in line:
            lines[i] = newline
            n += 1
            print("修复 %s %s -> %s" % (b, m, newline.strip()[:60]))
            break
io.open(path, "w", encoding="utf-8").write("".join(lines))
print("共修复 %d 行" % n)
