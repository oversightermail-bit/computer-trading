# -*- coding: utf-8 -*-
"""双向扩容：更新 爬虫/hwspider/config.py 与 后端/tools/gen_sample_data.py 的型号目录。

- 新增 13 个型号（含 zol_url 直采链接、基准价、性能分）
- 替换 5 个 ZOL 未收录型号（SN770→KC3000、新小黑→Basics A3、三星32GB→英睿达32GB、
  达尔优A98→狼蛛F87 Pro、ATK 68→洛斐小顺 Flow）
幂等：已更新过会自动跳过。
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

# ---------------- 新增型号（追加到目录末尾） ----------------
NEW = [
    {"type": "cpu", "brand": "Intel", "model": "i5-14600KF", "spec": "14核20线程", "base": 1299, "perf": 70,
     "zol_url": "https://detail.zol.com.cn/cpu/index1929615.shtml"},
    {"type": "cpu", "brand": "AMD", "model": "R5 7500F", "spec": "6核12线程", "base": 949, "perf": 62,
     "zol_url": "https://detail.zol.com.cn/cpu/index1796349.shtml"},
    {"type": "gpu", "brand": "NVIDIA", "model": "RTX 4070", "spec": "12GB", "base": 4099, "perf": 75,
     "zol_url": "https://detail.zol.com.cn/vga/index1981975.shtml"},
    {"type": "gpu", "brand": "AMD", "model": "RX 7800 XT", "spec": "16GB", "base": 3399, "perf": 78,
     "zol_url": "https://detail.zol.com.cn/vga/index2041683.shtml"},
    {"type": "mem_desktop", "brand": "金士顿", "model": "FURY 32GB", "spec": "DDR5 6000", "base": 849, "perf": 80,
     "zol_url": "https://detail.zol.com.cn/memory/index1629095.shtml"},
    {"type": "mem_desktop", "brand": "芝奇", "model": "幻锋戟 32GB", "spec": "DDR5 6400", "base": 999, "perf": 82,
     "zol_url": "https://detail.zol.com.cn/memory/index1985113.shtml"},
    {"type": "ssd", "brand": "三星", "model": "990 EVO Plus", "spec": "1TB", "base": 799, "perf": 78,
     "zol_url": "https://detail.zol.com.cn/solid_state_drive/index2112238.shtml"},
    {"type": "ssd_usb", "brand": "三星", "model": "T9", "spec": "1TB", "base": 999, "perf": 80,
     "zol_url": "https://detail.zol.com.cn/move_disk/index1924415.shtml"},
    {"type": "hdd_usb", "brand": "西数", "model": "Elements", "spec": "4TB", "base": 699, "perf": 68,
     "zol_url": "https://detail.zol.com.cn/move_disk/index1253105.shtml"},
    {"type": "monitor", "brand": "HKC", "model": "IG27Q", "spec": "2K 165Hz", "base": 899, "perf": 62,
     "zol_url": "https://detail.zol.com.cn/lcd/index1337857.shtml"},
    {"type": "monitor", "brand": "AOC", "model": "27G4", "spec": "1080P 180Hz", "base": 799, "perf": 58,
     "zol_url": "https://detail.zol.com.cn/lcd/index1930210.shtml"},
    {"type": "mouse", "brand": "罗技", "model": "G502 HERO", "spec": "有线", "base": 249, "perf": 68,
     "zol_url": "https://detail.zol.com.cn/Ergonomics_mouse/index1230541.shtml"},
    {"type": "mouse", "brand": "雷蛇", "model": "蝰蛇V2X", "spec": "无线", "base": 329, "perf": 72,
     "zol_url": "https://detail.zol.com.cn/Ergonomics_mouse/index1394153.shtml"},
]

# ---------------- 替换（旧 SKU -> 新定义） ----------------
REPLACE = {
    ("西部数据", "SN770", "1TB"): {"type": "ssd", "brand": "金士顿", "model": "KC3000", "spec": "1TB",
                                   "base": 599, "perf": 80,
                                   "zol_url": "https://detail.zol.com.cn/solid_state_drive/index1403069.shtml"},
    ("东芝", "新小黑", "4TB"): {"type": "hdd_usb", "brand": "东芝", "model": "Basics A3", "spec": "2TB",
                               "base": 429, "perf": 50,
                               "zol_url": "https://detail.zol.com.cn/move_disk/index1241704.shtml"},
    ("三星", "32GB", "DDR5 5600"): {"type": "mem_laptop", "brand": "英睿达", "model": "32GB", "spec": "DDR5 5600",
                                    "base": 899, "perf": 80,
                                    "zol_url": "https://detail.zol.com.cn/memory/index1857393.shtml"},
    ("达尔优", "A98", "无线机械"): {"type": "keyboard", "brand": "狼蛛", "model": "F87 Pro", "spec": "无线机械",
                                    "base": 249, "perf": 58,
                                    "zol_url": "https://detail.zol.com.cn/keyboard/index1969155.shtml"},
    ("ATK", "68", "有线磁轴"): {"type": "keyboard", "brand": "洛斐", "model": "小顺 Flow", "spec": "68键线性轴",
                                "base": 599, "perf": 60,
                                "zol_url": "https://detail.zol.com.cn/keyboard/index2147075.shtml"},
}


def cat_line(d):
    return ('    {"type": "%s", "brand": "%s", "model": "%s", "spec": "%s", '
            '"zol_url": "%s", "base": %d},\n'
            % (d["type"], d["brand"], d["model"], d["spec"], d["zol_url"], d["base"]))


def prod_tuple(d):
    return ('    ("%s", "%s", "%s", "%s", %d, %d),\n'
            % (d["type"], d["brand"], d["model"], d["spec"], d["base"], d["perf"]))


def update_config():
    path = "hwspider/config.py"
    text = io.open(path, encoding="utf-8").read()
    n_rep = n_new = 0
    for (ob, om, ospec), d in REPLACE.items():
        pat = re.compile(r'(\{\"type\": \"[a-z_]+\", \"brand\": \"%s\", \"model\": \"%s\", '
                         r'\"spec\": \"%s\", )(?:[^}]*)\},\n'
                         % (re.escape(ob), re.escape(om), re.escape(ospec)))
        text, c = pat.subn(
            lambda m: m.group(1) + '"zol_url": "%s", "base": %d},\n' % (d["zol_url"], d["base"]),
            text)
        n_rep += c
        print("config 替换 %s|%s|%s x%d" % (ob, om, ospec, c))
    # 追加新型号：在最后一个目录条目后插入
    anchor = re.search(r'\n(\s*\{[^}]*"OP-520"[^}]*\},\n)', text)
    if anchor:
        block = "".join(cat_line(d) for d in NEW)
        text = text[:anchor.start(1)] + block + text[anchor.start(1):]
        n_new = len(NEW)
    io.open(path, "w", encoding="utf-8").write(text)
    print("config 新增 %d 条" % n_new)


def update_products():
    path = r"D:\AI电脑购买指导项目\后端\tools\gen_sample_data.py"
    text = io.open(path, encoding="utf-8").read()
    n_rep = 0
    for (ob, om, ospec), d in REPLACE.items():
        # 旧条目与新条目同属一个硬件类目，匹配 类型+品牌+型号，再用旧规格二次确认
        pat = re.compile(r'\("(%s)", "(%s)", "(%s)", "([^"]*)", \d+, \d+\),'
                         % (re.escape(d["type"]), re.escape(ob), re.escape(om)))
        def sub(m, ospec=ospec, d=d):
            if m.group(4).strip() != ospec:
                return m.group(0)
            return prod_tuple(d).strip()
        text, c = pat.subn(sub, text)
        n_rep += c
        print("products 替换 %s|%s|%s x%d" % (ob, om, ospec, c))
    anchor = re.search(r'\n(\s*\("[^"]*", "[^"]*", "OP-520", "[^"]*", \d+, \d+\),\n)', text)
    if anchor:
        block = "".join(prod_tuple(d) for d in NEW)
        text = text[:anchor.start(1)] + block + text[anchor.start(1):]
    io.open(path, "w", encoding="utf-8").write(text)
    print("products 新增 %d 条" % len(NEW))


if __name__ == "__main__":
    update_config()
    update_products()
    print("DONE")
