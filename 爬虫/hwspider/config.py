# -*- coding: utf-8 -*-
"""
爬虫子模块统一配置中心（运营可配，改完重启调度即生效）

依据《硬件比价网站_代码实现功能描述文档》第四章：
  - 采集目标：京东 / 天猫 / 淘宝 三大平台，覆盖 10 个硬件类目；
  - 反爬策略：UA 轮换、代理池、请求限速、失败重试、封禁信号检测；
  - 清洗口径：价格标准化 + 按 SKU（品牌|型号|规格）聚合取中位价；
  - 调度：每日多次定时抓取，保证价格时序连续；
  - 监控：成功率统计、封禁告警、自动切换策略（被封禁 → 模拟行情降级）。

与后端契约（见 后端/sql/schema.sql 与 README）：
  - t_product：商品/型号主数据，爬虫按 (hardware_type, brand, model, spec) 幂等 upsert；
  - t_price_history：价格时序，爬虫写入、后端只读聚合，一行 = 商品 × 平台 × 日期；
  - 平台名称与 init_data.sql 一致：京东 / 天猫 / 淘宝；
  - hardware_type 编码与 t_hardware.type 一致。
"""
from pathlib import Path

# ---------------- 项目路径 ----------------
BASE_DIR = Path(__file__).resolve().parent.parent     # 爬虫/
LOG_DIR = BASE_DIR / "logs"
REPORT_DIR = LOG_DIR                                   # 推荐报告/统计/告警统一放 logs/

# ---------------- 数据库（与后端 application.yml 保持一致） ----------------
DATABASE = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "hw_price",
    "charset": "utf8mb4",
}

# ---------------- 采集平台（顺序即抓取顺序） ----------------
PLATFORMS = ["京东", "天猫", "淘宝"]

# 各平台相对基准价系数（与后端演示数据口径一致，用于模拟行情与校验）
PLATFORM_FACTOR = {"京东": 1.00, "天猫": 0.985, "淘宝": 0.97}

# ---------------- 反爬参数 ----------------
ANTI_CRAWL = {
    "download_delay": 2.0,          # 请求限速（秒）
    "concurrent_requests": 4,       # 并发数
    "retry_times": 3,               # 失败重试次数
    "timeout": 10,                  # 单请求超时（秒）
    "page_size": 1,                 # 每个关键词最多翻页数（演示环境别抓太狠）
    # UA 池轮换（可用真实浏览器 UA 扩充）
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    ],
    # 代理池（留空 = 直连；格式 ["http://user:pass@ip:port", ...]）
    "proxies": [],
    # 封禁/风险页特征词：命中即判定为封禁信号（触发告警与自动切换）
    "ban_markers": [
        "验证码", "captcha", "安全验证", "风险控制", "异常访问",
        "登录后", "请登录", "login.taobao.com", "passport.jd.com",
    ],
    # 每平台请求上限（超出视为异常，保护目标站点也保护自己）
    "max_requests_per_platform": 60,
}

# ---------------- 调度（每日多次，保证时序连续） ----------------
SCHEDULE = {
    "times": ["08:00", "12:00", "18:00", "22:00"],  # 每日 4 次
    "timezone": "Asia/Shanghai",
    "backfill_days": 30,                             # 首次回填最近 30 天
}

# ---------------- 推荐购买平台算法 ----------------
RECOMMEND = {
    # 最低价与次低价差额 ≤ 该值（元）时"并列推荐"，避免微小差价误导用户
    "tie_threshold": 5.0,
}

# ---------------- 监控与告警 ----------------
MONITOR = {
    "alert_success_rate": 0.5,   # 真实抓取成功率低于该值即告警
    "alert_consecutive_fail": 3, # 连续失败次数告警线
    "webhook_url": "",           # 可选：企业微信/钉钉 webhook，留空仅写告警文件
    "keep_stats_runs": 30,       # 统计文件保留最近 N 轮
}

# ---------------- 模拟行情（降级策略） ----------------
# 真实平台被封禁 / 离线 / 解析失效时，自动切换为该数据源，
# 用固定种子的随机游走生成"品牌×型号×规格×平台×日期"的确定性价格，
# 保证 采集→清洗→入库→折线 全链路在演示环境始终可跑通。
MOCK = {
    "volatility": 0.02,         # 单日波动 ±2%
    "floor_ratio": 0.92,        # 相对基准价下限
    "cap_ratio": 1.08,          # 相对基准价上限
    "promo_prob": 0.08,         # 当日促销概率
    "promo_discount": 0.95,     # 促销折扣
}

# ---------------- 商品目录（SKU 主数据 + 采集关键词 + 模拟基准价） ----------------
# 与后端 sql/init_data.sql 的 45 个型号保持一致：爬虫按 (品牌,型号,规格)
# 匹配复用 t_product 已有记录（id 1-45），不会产生重复商品。
# 扩展硬件类目：在 CATALOG 追加条目即可，Spider 自动按 hardware_type 生成关键词。
CATALOG = [
    # ---- CPU（台式机） ----
    {"type": "cpu", "brand": "Intel", "model": "i5-12400F", "spec": "6核12线程", "base": 749},
    {"type": "cpu", "brand": "Intel", "model": "i5-13490F", "spec": "10核16线程", "base": 1099},
    {"type": "cpu", "brand": "Intel", "model": "i7-13700KF", "spec": "16核24线程", "base": 1899},
    {"type": "cpu", "brand": "AMD", "model": "R5 5600", "spec": "6核12线程", "base": 599},
    {"type": "cpu", "brand": "AMD", "model": "R7 7800X3D", "spec": "8核16线程", "base": 2599},
    # ---- GPU（台式机） ----
    {"type": "gpu", "brand": "NVIDIA", "model": "RTX 4060", "spec": "8GB", "base": 2299},
    {"type": "gpu", "brand": "NVIDIA", "model": "RTX 4060 Ti", "spec": "8GB", "base": 2999},
    {"type": "gpu", "brand": "NVIDIA", "model": "RTX 4070 Super", "spec": "12GB", "base": 4399},
    {"type": "gpu", "brand": "NVIDIA", "model": "RTX 4080 Super", "spec": "16GB", "base": 7599},
    {"type": "gpu", "brand": "AMD", "model": "RX 6750 XT", "spec": "12GB", "base": 1899},
    {"type": "gpu", "brand": "AMD", "model": "RX 7900 XT", "spec": "20GB", "base": 5299},
    # ---- 内存条（台式机 DDR4/DDR5） ----
    {"type": "mem_desktop", "brand": "金士顿", "model": "FURY 16GB", "spec": "DDR4 3200", "base": 289},
    {"type": "mem_desktop", "brand": "金士顿", "model": "FURY 16GB", "spec": "DDR5 6000", "base": 429},
    {"type": "mem_desktop", "brand": "威刚", "model": "XPG 32GB", "spec": "DDR5 6400", "base": 899},
    {"type": "mem_desktop", "brand": "光威", "model": "天策 16GB", "spec": "DDR4 3200", "base": 199},
    # ---- 内存条（笔记本） ----
    {"type": "mem_laptop", "brand": "三星", "model": "16GB", "spec": "DDR4 3200", "base": 269},
    {"type": "mem_laptop", "brand": "英睿达", "model": "16GB", "spec": "DDR5 4800", "base": 349},
    {"type": "mem_laptop", "brand": "三星", "model": "32GB", "spec": "DDR5 5600", "base": 799},
    # ---- 固态硬盘（M.2 NVMe PCIe 4.0/5.0） ----
    {"type": "ssd", "brand": "三星", "model": "990 PRO", "spec": "1TB", "base": 729},
    {"type": "ssd", "brand": "三星", "model": "990 PRO", "spec": "2TB", "base": 1299},
    {"type": "ssd", "brand": "致态", "model": "TiPlus7100", "spec": "1TB", "base": 549},
    {"type": "ssd", "brand": "铠侠", "model": "RC20", "spec": "1TB", "base": 429},
    {"type": "ssd", "brand": "西部数据", "model": "SN770", "spec": "1TB", "base": 529},
    # ---- 移动便携固态硬盘（USB） ----
    {"type": "ssd_usb", "brand": "闪迪", "model": "E61", "spec": "1TB", "base": 699},
    {"type": "ssd_usb", "brand": "三星", "model": "T7", "spec": "1TB", "base": 749},
    {"type": "ssd_usb", "brand": "致态", "model": "移动固态", "spec": "1TB", "base": 599},
    # ---- 移动便携机械硬盘（USB） ----
    {"type": "hdd_usb", "brand": "西数", "model": "Elements", "spec": "2TB", "base": 499},
    {"type": "hdd_usb", "brand": "希捷", "model": "睿品", "spec": "2TB", "base": 529},
    {"type": "hdd_usb", "brand": "东芝", "model": "新小黑", "spec": "4TB", "base": 899},
    # ---- 台式机显示屏 ----
    {"type": "monitor", "brand": "AOC", "model": "24G2", "spec": "1080P 144Hz", "base": 799},
    {"type": "monitor", "brand": "小米", "model": "G27Q", "spec": "2K 165Hz", "base": 1099},
    {"type": "monitor", "brand": "LG", "model": "27GP850", "spec": "2K 180Hz", "base": 1899},
    {"type": "monitor", "brand": "三星", "model": "S27A800", "spec": "4K 60Hz", "base": 2399},
    # ---- 键盘（有线/无线 × 薄膜/机械/磁轴） ----
    {"type": "keyboard", "brand": "罗技", "model": "G610", "spec": "有线机械", "base": 449},
    {"type": "keyboard", "brand": "罗技", "model": "G913", "spec": "无线机械", "base": 1299},
    {"type": "keyboard", "brand": "达尔优", "model": "A98", "spec": "无线机械", "base": 399},
    {"type": "keyboard", "brand": "雷蛇", "model": "黑寡妇V4", "spec": "有线机械", "base": 899},
    {"type": "keyboard", "brand": "双飞燕", "model": "KB-8", "spec": "有线薄膜", "base": 59},
    {"type": "keyboard", "brand": "ATK", "model": "68", "spec": "有线磁轴", "base": 599},
    # ---- 鼠标（有线/无线/蓝牙） ----
    {"type": "mouse", "brand": "罗技", "model": "G102", "spec": "有线", "base": 99},
    {"type": "mouse", "brand": "罗技", "model": "G304", "spec": "无线", "base": 199},
    {"type": "mouse", "brand": "罗技", "model": "GPW 2", "spec": "无线", "base": 799},
    {"type": "mouse", "brand": "雷蛇", "model": "蝰蛇V3", "spec": "有线", "base": 299},
    {"type": "mouse", "brand": "罗技", "model": "M185", "spec": "无线", "base": 69},
    {"type": "mouse", "brand": "双飞燕", "model": "OP-520", "spec": "有线", "base": 39},
]

# 硬件类目中文名（仅用于日志/报告展示）
HARDWARE_NAMES = {
    "cpu": "CPU（台式机）",
    "gpu": "GPU（台式机）",
    "mem_desktop": "内存条（台式机）",
    "mem_laptop": "内存条（笔记本）",
    "ssd": "固态硬盘（M.2 NVMe）",
    "ssd_usb": "移动便携固态硬盘（USB）",
    "hdd_usb": "移动便携机械硬盘（USB）",
    "monitor": "台式机显示屏",
    "keyboard": "键盘",
    "mouse": "鼠标",
}
