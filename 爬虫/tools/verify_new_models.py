# -*- coding: utf-8 -*-
"""验证新增/替换型号的 ZOL 页面：抓标题与报价，输出核对表。"""
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from hwspider.spiders import zol  # noqa: E402

# (类目, 品牌, 型号, 规格, 期望标题关键词, url)
CANDIDATES = [
    ("cpu", "Intel", "i5-14600KF", "14核20线程", "14600KF", "https://detail.zol.com.cn/cpu/index1929615.shtml"),
    ("cpu", "AMD", "R5 7500F", "6核12线程", "7500F", "https://detail.zol.com.cn/cpu/index1796349.shtml"),
    ("gpu", "NVIDIA", "RTX 4070", "12GB", "RTX 4070", "https://detail.zol.com.cn/vga/index1981975.shtml"),
    ("gpu", "AMD", "RX 7800 XT", "16GB", "RX 7800", "https://detail.zol.com.cn/vga/index2041683.shtml"),
    ("mem_desktop", "金士顿", "FURY 32GB", "DDR5 6000", "FURY Beast 32GB DDR5 6000", "https://detail.zol.com.cn/memory/index1629095.shtml"),
    ("mem_desktop", "芝奇", "幻锋戟 32GB", "DDR5 6400", "幻锋戟", "https://detail.zol.com.cn/memory/index1985113.shtml"),
    ("ssd", "三星", "990 EVO Plus", "1TB", "990 EVO", "https://detail.zol.com.cn/solid_state_drive/index2112238.shtml"),
    ("ssd_usb", "三星", "T9", "1TB", "T9", "https://detail.zol.com.cn/move_disk/index1924415.shtml"),
    ("hdd_usb", "西数", "Elements", "4TB", "Elements", "https://detail.zol.com.cn/move_disk/index1253105.shtml"),
    ("monitor", "HKC", "IG27Q", "2K 165Hz", "IG27Q", "https://detail.zol.com.cn/lcd/index1337857.shtml"),
    ("monitor", "AOC", "27G4", "1080P 180Hz", "27G4", "https://detail.zol.com.cn/lcd/index1930210.shtml"),
    ("mouse", "罗技", "G502 HERO", "有线", "G502", "https://detail.zol.com.cn/Ergonomics_mouse/index1230541.shtml"),
    ("mouse", "雷蛇", "蝰蛇V2X", "无线", "蝰蛇V2X", "https://detail.zol.com.cn/Ergonomics_mouse/index1394153.shtml"),
    ("ssd", "金士顿", "KC3000", "1TB", "KC3000", "https://detail.zol.com.cn/solid_state_drive/index1403069.shtml"),
    ("hdd_usb", "东芝", "Basics A3", "2TB", "Basics A3", "https://detail.zol.com.cn/move_disk/index1241704.shtml"),
    ("mem_laptop", "英睿达", "32GB", "DDR5 5600", "32GB DDR5 5600", "https://detail.zol.com.cn/memory/index1857393.shtml"),
    ("keyboard", "狼蛛", "F87 Pro", "无线机械", "F87", "https://detail.zol.com.cn/keyboard/index1969155.shtml"),
    ("keyboard", "洛斐", "小顺 Flow", "68键线性轴", "小顺", "https://detail.zol.com.cn/keyboard/index2147075.shtml"),
]

for hw, br, mo, sp, kw, url in CANDIDATES:
    time.sleep(3)
    try:
        html, final, err = zol.fetch(url, referer="https://detail.zol.com.cn/")
    except Exception as e:
        print("ERR  %-22s %r" % (br + " " + mo, e))
        continue
    if err:
        print("NET  %-22s %s" % (br + " " + mo, err))
        continue
    m = re.search(r"<title>(.*?)</title>", html)
    title = (m.group(1).strip() if m else "").replace("报价_参数_图片_论坛_", "…")
    price, _ = zol.parse_product(html, url)
    ok = all(k.lower() in title.lower() for k in kw.split())
    print("%s %-22s 标题: %s  价格: %s"
          % ("OK " if ok else "?? ", br + " " + mo, title[:64], price or "暂无"))
