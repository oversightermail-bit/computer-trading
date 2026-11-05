# -*- coding: utf-8 -*-
"""
生成 sql/init_data.sql：套餐、硬件类目、商品主数据、近 30 天中关村在线价格时序。
价格用固定种子的随机游走生成（可复现）；日期使用 CURDATE() 相对表达式，
保证任何时候导入，折线图都有"最近 30 天"的新鲜数据。

口径说明（2026-11-05 起）：init_data.sql 中的价格是**模拟演示数据**，
入库时 source='mock'，后端聚合只读 source='real'（真实采集），
模拟价绝不会冒充真实价；前端 Mock 演示模式（data.js）与其同源。
性能分（perf_score/perf_basis/perf_updated）来自项目根 perf_benchmarks.json
（PassMark / 3DMark / 官方规格自动映射 1-100，单一数据源）。

用法：python tools/gen_sample_data.py
"""
import json
import os
import random

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "sql", "init_data.sql")

# 性能分基准（与 爬虫/tools/migrate_quality.py 共用同一文件，避免口径漂移）
ROOT = os.path.dirname(BASE)
BENCH = json.load(open(os.path.join(ROOT, "perf_benchmarks.json"), encoding="utf-8"))
BENCH_BY_SKU = {it["sku"]: it for it in BENCH["items"]}

# 2026-11 起主数据源为中关村在线（ZOL）参考报价（真实爬虫写同一平台名）
PLATFORMS = ["中关村在线"]
PLATFORM_FACTOR = {"中关村在线": 0.99}
DAYS = 30  # 折线窗口

# 硬件类目：(type, name, func, scene, pitfall)
HARDWARE = [
    ("cpu", "CPU（台式机）",
     "电脑的大脑，决定日常操作、游戏与生产力的响应速度；核数越多多任务越强，频率越高单核越猛。",
     "办公上网选 4-6 核即可；打游戏优先单核强的新架构；剪辑渲染、多开虚拟机选 8 核以上。",
     "别只看核数，架构代际更关键；Intel 与 AMD 主板不通用；带 K/X 的型号要另买散热器。"),
    ("gpu", "GPU（台式机）",
     "独立显卡负责游戏画面渲染与视频编码，显存大小决定能开多高画质。",
     "网游与 1080P 电竞用中端卡；2K/4K 3A 大作与 AI 绘图、剪辑加速上高端卡。",
     "矿卡/二手卡水深，认准正规渠道；电源功率要留足；机箱长度要装得下。"),
    ("mem_desktop", "内存条（台式机）",
     "程序运行时的临时数据仓库，容量不足会卡顿，频率与时序影响游戏帧数。",
     "办公 16G 起步；游戏 16G 够用、32G 舒服；剪辑与生产力 32G 起。",
     "DDR4/DDR5 不通用，看主板支持；双通道记得插 2/4 槽；高频条要进 BIOS 开 XMP。"),
    ("mem_laptop", "内存条（笔记本）",
     "笔记本内存决定多开网页与程序的流畅度，比台式机更讲究功耗。",
     "办公 16G 起步；轻度剪辑与游戏 16-32G；升级前先查本机是否板载焊死。",
     "分清 DDR4/DDR5 与电压（标压/低压）；确认是 SO-DIMM 插槽还是板载；频率取主板支持值。"),
    ("ssd", "固态硬盘（M.2 NVMe）",
     "系统与软件的存储盘，读写速度直接影响开机、进游戏与拷贝大文件的速度。",
     "系统盘 500G-1T；游戏库 1-2T；做视频素材库建议 2T 起并另配机械盘备份。",
     "分清 PCIe 4.0 与 5.0（后者发热大需散热片）；QLC 颗粒写入寿命低于 TLC；认准正规颗粒。"),
    ("ssd_usb", "移动便携固态硬盘（USB）",
     "口袋大小的外接固态，比 U 盘快几十倍，适合随身带素材、备份与传大文件。",
     "摄影师/剪辑师外拍备份；学生与上班族传资料；需要 Type-C 直连手机平板选带 C 口的型号。",
     "接口速度决定上限（USB 3.2 10Gbps 以上才有意义）；别买扩容盘；重要数据多做一份备份。"),
    ("hdd_usb", "移动便携机械硬盘（USB）",
     "大容量冷备份的性价比之王，适合存不常动的照片、视频与资料。",
     '家庭照片与影音冷备份；预算有限又需要 2T 以上容量；配合 SSD 做"热+冷"双备份。',
     "机械盘怕摔怕震，用的时候别移动；转速 5400/7200 区别不大；垂直盘（CMR）比叠瓦盘（SMR）稳。"),
    ("monitor", "台式机显示屏",
     '电脑的"脸"，分辨率、刷新率与面板类型决定画面清晰度与流畅感。',
     "办公选 1080P/2K IPS 护眼；电竞选 144Hz 以上高刷；设计修图选广色域高色准屏。",
     "显卡要带得动高分辨率高刷；Type-C 供电一体屏注意功率；坏点/漏光收货就检查。"),
    ("keyboard", "键盘",
     "输入设备，轴体手感差异大：薄膜便宜安静，机械手感好寿命长，磁轴响应最快。",
     "办公码字选薄膜或轻压力机械轴；游戏选机械/磁轴；桌面无线整洁选 2.4G/蓝牙三模。",
     "有线/无线/蓝牙三种连接别搞混；机械轴有青红茶等手感差异；磁轴需支持软件才有完整功能。"),
    ("mouse", "鼠标",
     "指针与点击设备，传感器精度、握持手感和重量影响游戏与办公体验。",
     "办公选无线静音小重量；FPS 电竞选轻量高回报率；多设备切换选蓝牙+2.4G 双模。",
     "回报率不是越高越好（耗电）；对称/人体工学模具手感因人而异；无线鼠标注意接收器收纳。"),
]

# 商品主数据：(hardware_type, brand, model, spec, base_price, _perf_deprecated)
# 性能分不再取第 6 元组值（旧人工分已废弃），统一取 perf_benchmarks.json 的
# 基准映射分（PassMark / 3DMark / 官方规格 → 1-100，记录依据与日期）。
# 性价比指数 = 性能分 ÷ ln(参考价) × 100（对数归一化，抑制"越便宜分越高"偏差）。
PRODUCTS = [
    ("cpu", "Intel", "i5-12400F", "6核12线程", 749, 55),
    ("cpu", "Intel", "i5-13490F", "10核16线程", 1099, 62),
    ("cpu", "Intel", "i7-13700KF", "16核24线程", 1899, 82),
    ("cpu", "AMD", "R5 5600", "6核12线程", 599, 52),
    ("cpu", "AMD", "R7 7800X3D", "8核16线程", 2599, 90),
    ("gpu", "NVIDIA", "RTX 4060", "8GB", 2299, 60),
    ("gpu", "NVIDIA", "RTX 4060 Ti", "8GB", 2999, 65),
    ("gpu", "NVIDIA", "RTX 4070 Super", "12GB", 4399, 80),
    ("gpu", "NVIDIA", "RTX 4080 Super", "16GB", 7599, 92),
    ("gpu", "AMD", "RX 6750 XT", "12GB", 1899, 62),
    ("gpu", "AMD", "RX 7900 XT", "20GB", 5299, 88),
    ("mem_desktop", "金士顿", "FURY 16GB", "DDR4 3200", 289, 50),
    ("mem_desktop", "金士顿", "FURY 16GB", "DDR5 6000", 429, 55),
    ("mem_desktop", "威刚", "XPG 32GB", "DDR5 6400", 899, 78),
    ("mem_desktop", "光威", "天策 16GB", "DDR4 3200", 199, 48),
    ("mem_laptop", "三星", "16GB", "DDR4 3200", 269, 52),
    ("mem_laptop", "英睿达", "16GB", "DDR5 4800", 349, 50),
    ("mem_laptop", "英睿达", "32GB", "DDR5 5600", 899, 80),
    ("ssd", "三星", "990 PRO", "1TB", 729, 85),
    ("ssd", "三星", "990 PRO", "2TB", 1299, 88),
    ("ssd", "致态", "TiPlus7100", "1TB", 549, 78),
    ("ssd", "铠侠", "RC20", "1TB", 429, 55),
    ("ssd", "金士顿", "KC3000", "1TB", 599, 80),
    ("ssd_usb", "闪迪", "E61", "1TB", 699, 70),
    ("ssd_usb", "三星", "T7", "1TB", 749, 72),
    ("ssd_usb", "致态", "移动固态", "1TB", 599, 68),
    ("hdd_usb", "西数", "Elements", "2TB", 499, 55),
    ("hdd_usb", "希捷", "睿品", "2TB", 529, 58),
    ("hdd_usb", "东芝", "Basics A3", "2TB", 429, 50),
    ("monitor", "AOC", "24G2", "1080P 144Hz", 799, 50),
    ("monitor", "小米", "G27Q", "2K 165Hz", 1099, 68),
    ("monitor", "LG", "27GP850", "2K 180Hz", 1899, 78),
    ("monitor", "三星", "S27A800", "4K 60Hz", 2399, 72),
    ("keyboard", "罗技", "G610", "有线机械", 449, 55),
    ("keyboard", "罗技", "G913", "无线机械", 1299, 75),
    ("keyboard", "狼蛛", "F87 Pro", "无线机械", 249, 58),
    ("keyboard", "雷蛇", "黑寡妇V4", "有线机械", 899, 72),
    ("keyboard", "双飞燕", "KB-8", "有线薄膜", 59, 25),
    ("keyboard", "洛斐", "小顺 Flow", "68键线性轴", 599, 60),
    ("mouse", "罗技", "G102", "有线", 99, 55),
    ("mouse", "罗技", "G304", "无线", 199, 60),
    ("mouse", "罗技", "GPW 2", "无线", 799, 85),
    ("mouse", "雷蛇", "蝰蛇V3", "有线", 299, 78),
    ("mouse", "罗技", "M185", "无线", 69, 30),
    ("cpu", "Intel", "i5-14600KF", "14核20线程", 1299, 70),
    ("cpu", "AMD", "R5 7500F", "6核12线程", 949, 62),
    ("gpu", "NVIDIA", "RTX 4070", "12GB", 4099, 75),
    ("gpu", "AMD", "RX 7800 XT", "16GB", 3399, 78),
    ("mem_desktop", "金士顿", "FURY 32GB", "DDR5 6000", 849, 80),
    ("mem_desktop", "芝奇", "幻锋戟 32GB", "DDR5 6400", 999, 82),
    ("ssd", "三星", "990 EVO Plus", "1TB", 799, 78),
    ("ssd_usb", "三星", "T9", "1TB", 999, 80),
    ("hdd_usb", "西数", "Elements", "4TB", 699, 68),
    ("monitor", "HKC", "IG27Q", "2K 165Hz", 899, 62),
    ("monitor", "AOC", "27G4", "1080P 180Hz", 799, 58),
    ("mouse", "罗技", "G502 HERO", "有线", 249, 68),
    ("mouse", "雷蛇", "蝰蛇V2X", "无线", 329, 72),
    ("mouse", "双飞燕", "OP-520", "有线", 39, 25),
]

PLANS = [
    (1, "免费版", "0.00", 3, 60, 0, "全部价格与折线浏览；仅文本问答；无图片解析", 1),
    (2, "基础版", "9.90", 20, 400, 1, "文本问答 + 配置单图片解析（图片计 2 次）；配置单保存", 2),
    (3, "专业版", "29.90", 80, 1500, 1, "全部 AI 能力 + 多硬件对比 + 历史会话回溯 + 优先响应", 3),
    (4, "旗舰版", "69.90", 200, 4000, 1, "长上下文 + 优先并发 + 配置清单导出（CSV）", 4),
]


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "\\'")


def bench_for(brand: str, model: str, spec: str) -> tuple:
    """从 perf_benchmarks.json 取 (score, perf_basis, perf_updated)。"""
    sku = "%s|%s|%s" % (brand, model, spec)
    item = BENCH_BY_SKU.get(sku)
    if item is None:
        return (0, "基准缺失", "2026-01-01")
    return item["score"], item["basis"], item["updated"]


def price_series(seed: int, base: float) -> list:
    """随机游走 30 天价格序列，波动 ±2%/天，整体 ±8% 内"""
    rng = random.Random(seed)
    price = base
    out = []
    for _ in range(DAYS):
        drift = rng.uniform(-0.02, 0.02)
        price = max(base * 0.92, min(base * 1.08, price * (1 + drift)))
        out.append(round(price, 2))
    return out


def main() -> None:
    lines = []
    w = lines.append
    w("-- =========================================================")
    w("-- 初始化演示数据（由 tools/gen_sample_data.py 生成，可重复执行）")
    w("-- 执行方式：mysql -u root -p hw_price < sql/init_data.sql")
    w("-- 价格日期用 CURDATE() 相对表达式，任何时候导入都是\"最近 30 天\"")
    w("-- =========================================================")
    w("USE hw_price;")
    w("")

    # 套餐
    w("-- 订阅套餐（与 subscription_schema.sql 一致，INSERT IGNORE 可重复执行）")
    plan_rows = ",\n".join(
        "(%d, '%s', %s, %d, %d, %d, 1, '%s', %d)" % p for p in PLANS
    )
    w("INSERT IGNORE INTO t_subscription_plan")
    w("(id, plan_name, price_month, quota_day, quota_month, multimodal, status, description, sort_order) VALUES")
    w(plan_rows + ";")
    w("")

    # 硬件类目
    w("-- 硬件类目与文案（固定 id 1-%d）" % len(HARDWARE))
    w("INSERT INTO t_hardware (id, type, name, func_desc, scene, pitfall, sort_order) VALUES")
    hw_rows = ",\n".join(
        "(%d, '%s', '%s', '%s', '%s', '%s', %d)" % (i + 1, esc(h[0]), esc(h[1]), esc(h[2]), esc(h[3]), esc(h[4]), i + 1)
        for i, h in enumerate(HARDWARE)
    )
    w(hw_rows + ";")
    w("")

    # 商品主数据
    w("-- 商品/型号主数据（固定 id 1-%d，perf_score/perf_basis/perf_updated 来自 perf_benchmarks.json）" % len(PRODUCTS))
    w("INSERT INTO t_product (id, hardware_type, brand, model, spec, perf_score, perf_basis, perf_updated) VALUES")
    prod_rows = ",\n".join(
        "(%d, '%s', '%s', '%s', '%s', %d, '%s', '%s')" % (
            i + 1, esc(p[0]), esc(p[1]), esc(p[2]), esc(p[3]),
            bench_for(p[1], p[2], p[3])[0], esc(bench_for(p[1], p[2], p[3])[1]),
            bench_for(p[1], p[2], p[3])[2])
        for i, p in enumerate(PRODUCTS)
    )
    w(prod_rows + ";")
    w("")

    # 价格时序：每商品 × 1 平台 × 30 天（source='mock' 模拟演示数据）
    w("-- 价格时序：每个商品 1 平台 × 30 天（模拟演示数据 source='mock'，后端聚合只读 source='real'）")
    w("-- 日期 = CURDATE() - INTERVAL n DAY")
    w("INSERT INTO t_price_history (product_id, platform, price, date, source) VALUES")
    rows = []
    for i, p in enumerate(PRODUCTS):
        product_id = i + 1
        base = p[4]
        for pi, platform in enumerate(PLATFORMS):
            start = base * PLATFORM_FACTOR[platform] * (1 + (random.Random(product_id + pi).uniform(-0.02, 0.02)))
            series = price_series(product_id * 31 + pi * 7, start)
            for n, price in enumerate(series):  # n=0 -> 29 天前；n=29 -> 今天
                ago = DAYS - 1 - n
                rows.append("(%d, '%s', %.2f, CURDATE() - INTERVAL %d DAY, 'mock')" % (product_id, platform, price, ago))
    # 每 1500 行一个 INSERT 语句，避免包过大
    CHUNK = 1500
    for c in range(0, len(rows), CHUNK):
        chunk = rows[c:c + CHUNK]
        w(",\n".join(chunk) + (";" if c + CHUNK >= len(rows) else ","))
        w("")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("OK -> %s (%d products, %d price rows)" % (OUT, len(PRODUCTS), len(rows)))


if __name__ == "__main__":
    main()
