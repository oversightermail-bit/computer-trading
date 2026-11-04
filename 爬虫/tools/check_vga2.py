# -*- coding: utf-8 -*-
"""离线核对已保存的 vga 页：4080/6750 是否真的不在列表。"""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

t = open("tools/probe_vga.html", encoding="utf-8").read()
for tok in ["4080", "6750", "RX 7", "RX 6", "Super"]:
    idxs = [m.start() for m in re.finditer(tok, t)]
    print("%-8s 出现 %d 次" % (tok, len(idxs)))
    if idxs and tok in ("4080", "6750"):
        i = idxs[0]
        print("   上下文:", repr(t[i-80:i+80]))
