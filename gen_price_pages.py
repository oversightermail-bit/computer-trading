# -*- coding: utf-8 -*-
"""生成 10 个硬件价格波动页面：HTML + css/price.css + js/page.js（与后端 10 类硬件一一对应）"""
import os
import shutil

BASE = r"D:\AI电脑购买指导项目\前端"

PAGES = [
    # type, 文件夹, html 文件名, 分类标题, 规格标签
    ("cpu", "CPU", "cpu.html", "CPU（台式机）", "Intel / AMD · 多核多线程"),
    ("gpu", "GPU", "gpu.html", "GPU（台式机）", "独立显卡 · 各显存版本"),
    ("mem_desktop", "台式机内存", "neichun pc.html", "内存条（台式机）", "DDR4 / DDR5 · 台式机"),
    ("mem_laptop", "笔记本内存", "neichun bookpc.html", "内存条（笔记本）", "DDR4 / DDR5 · SO-DIMM"),
    ("ssd", "固态硬盘", "gutai.html", "固态硬盘（M.2 NVMe）", "PCIe 4.0 / 5.0 · 内置"),
    ("ssd_usb", "移动便携固态硬盘", "yidong gutaiyingpan.html", "移动便携固态硬盘（USB）", "USB 3.2 · 口袋级 SSD"),
    ("hdd_usb", "移动便携机械硬盘", "yidong jixieyingpan.html", "移动便携机械硬盘（USB）", "USB · 大容量冷备份"),
    ("monitor", "显示屏", "xianshiping.html", "台式机显示屏", "1080P ~ 4K · 高刷"),
    ("keyboard", "键盘", "jianpan.html", "键盘", "有线/无线 × 薄膜/机械/磁轴"),
    ("mouse", "鼠标", "shubiao.html", "鼠标", "有线 / 无线 / 蓝牙"),
]

ICONS = {
    "cpu": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><rect x="7" y="7" width="10" height="10" rx="1.5"/><path d="M5 10H2M5 14H2M22 10h-3M22 14h-3M10 5V2M14 5V2M10 22v-3M14 22v-3"/></svg>',
    "gpu": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="6" width="19" height="12" rx="2"/><circle cx="9.5" cy="12" r="3"/><circle cx="9.5" cy="12" r="1"/><path d="M14 9.5h4M14 14.5h4M16 7.5v2"/></svg>',
    "mem_desktop": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><rect x="3" y="8" width="18" height="8" rx="1.5"/><path d="M6 11.5h2M10 11.5h4M16 11.5h2M6.5 8v-2M9.5 8v-2M14.5 8v-2M17.5 8v-2M6.5 16v2M9.5 16v2M14.5 16v2M17.5 16v2"/></svg>',
    "mem_laptop": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><rect x="4" y="8" width="16" height="6" rx="1.5"/><path d="M5.5 11h2M9 11h3M14 11h2M6 8v-1.5M18 8v-1.5M6 14v1.5M18 14v1.5"/></svg>',
    "ssd": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><rect x="3" y="7" width="18" height="10" rx="2"/><circle cx="8" cy="12" r="2.2"/><path d="M13 10.5h6M13 13.5h6"/></svg>',
    "ssd_usb": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="8" y="3.5" width="8" height="14" rx="2"/><path d="M12 3.5v3M13.5 10h2M13.5 13h2"/><rect x="10" y="17.5" width="4" height="4" rx="1"/></svg>',
    "hdd_usb": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3.5" width="18" height="13" rx="2"/><circle cx="15.5" cy="10" r="1.6"/><path d="M5 10h5"/><rect x="9.5" y="16.5" width="5" height="4.5" rx="1"/></svg>',
    "monitor": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="4" width="19" height="13" rx="2"/><path d="M8.5 21h7M12 17v4"/></svg>',
    "keyboard": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><rect x="2" y="6.5" width="20" height="11" rx="2"/><path d="M5 10h.01M8 10h.01M11 10h.01M14 10h.01M17 10h.01M5.5 13.5h.01M8.5 13.5h.01M11.5 13.5h.01M14.5 13.5h.01M17.5 13.5h.01M20 13.5h.01M7 16h10"/></svg>',
    "mouse": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="8" y="2.5" width="8" height="15.5" rx="4"/><path d="M12 2.5v5M8 21.5h8"/><path d="M12 18v3.5"/></svg>',
}

INFO_ICONS = {
    "func": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.6 2.6 0 0 1 5 .6c0 1.8-2.5 1.9-2.5 3.4"/><circle cx="12" cy="16.8" r=".4" fill="currentColor"/></svg>',
    "scene": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 10.5L12 4l8 6.5"/><path d="M6.5 9.5V19a1.5 1.5 0 0 0 1.5 1.5h8a1.5 1.5 0 0 0 1.5-1.5V9.5"/><path d="M10 20.5v-5h4v5"/></svg>',
    "pitfall": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/></svg>',
}

HTML_TMPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} 价格走势 · 硬核比价</title>
  <link rel="icon" type="image/svg+xml" href="../assets/img/favicon.svg">
  <link rel="stylesheet" href="../assets/css/common.css">
  <link rel="stylesheet" href="css/price.css">
</head>
<body data-type="{ptype}">

<header class="site-header">
  <div class="container header-inner">
    <a class="brand" href="../首页/shouye.html">
      <img src="../assets/img/logo.svg" alt="logo">
      <span class="brand-name">硬核比价</span><span class="brand-sub">HWPRICE</span>
    </a>
    <nav class="nav">
      <a class="nav-link" href="../首页/shouye.html">首页</a>
      <a class="nav-link active" href="../首页/shouye.html#categories">硬件价格</a>
      <a class="nav-link" href="#" onclick="return HW_AIBtn(event)">AI 助手</a>
      <a class="nav-link" href="../账户/gerenxingxi.html#plans">订阅方案</a>
    </nav>
    <div class="header-right" id="headerRight"></div>
  </div>
</header>

<main id="hwMain">
  <!-- ===== 标题区 ===== -->
  <section class="hw-hero">
    <div class="container">
      <div class="crumb">
        <a href="../首页/shouye.html">首页</a><span>›</span>
        <a href="../首页/shouye.html#categories">硬件价格</a><span>›</span>
        <span style="color:var(--text-2)" id="crumbName">{title}</span>
      </div>
      <div class="hw-hero-inner">
        <div class="hw-icon">{icon}</div>
        <div>
          <h1 id="hwTitle">{title}</h1>
          <p class="tagline" id="hwTagline">加载中…</p>
          <div class="meta">
            <span class="tag">{spec}</span>
            <span class="tag teal">中关村在线（ZOL）参考报价</span>
            <span class="tag blue">近 30 天走势</span>
          </div>
        </div>
      </div>
    </div>
  </section>

  <div class="container">
    <!-- ===== 功能作用 / 适用场景 / 易踩坑点 ===== -->
    <div class="info-grid">
      <div class="card info-card">
        <div class="ico">{func_icon}</div>
        <h3>功能作用</h3>
        <p id="funcText">加载中…</p>
      </div>
      <div class="card info-card teal">
        <div class="ico">{scene_icon}</div>
        <h3>适用场景</h3>
        <p id="sceneText">加载中…</p>
      </div>
      <div class="card info-card rose">
        <div class="ico">{pitfall_icon}</div>
        <h3>容易踩坑点</h3>
        <p id="pitfallText">加载中…</p>
      </div>
    </div>

    <!-- ===== 价格波动折线图 ===== -->
    <div class="card chart-card">
      <div class="chart-toolbar">
        <span class="card-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="M7 14l4-4 3 3 5-6"/></svg>
          近 30 天价格波动
        </span>
        <span class="sub" id="updateTime"></span>
      </div>
      <p class="chart-hint" id="legendHint">数据加载中…</p>
      <div id="chartBox" class="skeleton" style="height:430px;margin-top:14px"></div>
      <div class="back-row">
        <a class="btn btn-primary btn-lg" href="../首页/shouye.html">← 返回首页</a>
      </div>
    </div>

    <!-- ===== 高性价比推荐 ===== -->
    <div class="card reco-card">
      <div class="chart-toolbar">
        <span class="card-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
          高性价比推荐
        </span>
        <span class="sub">性价比指数 = 性能分 ÷ 参考价 × 1000 · 数据来源：中关村在线（ZOL）参考报价</span>
      </div>
      <div class="table-wrap" style="margin-top:14px">
        <table class="data">
          <thead>
            <tr>
              <th>型号</th>
              <th>今日参考价</th>
              <th>性能分</th>
              <th>性价比指数</th>
              <th>推荐</th>
            </tr>
          </thead>
          <tbody id="recommendBody">
            <tr><td colspan="5" style="text-align:center;color:var(--text-3)">加载中…</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</main>

<footer class="site-footer">
  <div class="container">
    <div class="footer-inner">
      <div class="footer-col" style="max-width:300px">
        <a class="brand" href="../首页/shouye.html"><img src="../assets/img/logo.svg" alt="logo" style="width:28px;height:28px"><span class="brand-name">硬核比价</span></a>
        <p style="color:var(--text-3);font-size:13px;margin-top:12px">硬件价格比价与智能推荐网站：爬虫采集中关村在线（ZOL）参考报价，折线图看走势，AI 帮装机。</p>
      </div>
      <div class="footer-col">
        <h4>硬件价格</h4>
        <a href="../CPU/cpu.html">CPU（台式机）</a>
        <a href="../GPU/gpu.html">GPU（台式机）</a>
        <a href="../固态硬盘/gutai.html">固态硬盘</a>
        <a href="../显示屏/xianshiping.html">台式机显示屏</a>
      </div>
      <div class="footer-col">
        <h4>外设与存储</h4>
        <a href="../键盘/jianpan.html">键盘</a>
        <a href="../鼠标/shubiao.html">鼠标</a>
        <a href="../移动便携固态硬盘/yidong%20gutaiyingpan.html">移动固态硬盘</a>
        <a href="../移动便携机械硬盘/yidong%20jixieyingpan.html">移动机械硬盘</a>
      </div>
      <div class="footer-col">
        <h4>账户</h4>
        <a href="../登录界面/denlu.html">登录 / 注册</a>
        <a href="../账户/gerenxingxi.html">我的账户与订阅</a>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© 2026 硬核比价 · 硬件价格比价与智能推荐网站</span>
      <span>前端 HTML/CSS/JS + ECharts ｜ 后端 Java Spring Boot ｜ 采集 Python 爬虫</span>
    </div>
  </div>
</footer>

<script src="../assets/js/config.js"></script>
<script src="../assets/js/data.js"></script>
<script src="../assets/js/ui.js"></script>
<script src="../assets/js/api.js"></script>
<script src="../assets/js/auth.js"></script>
<script src="../assets/js/quota.js"></script>
<script src="../assets/js/ai.js"></script>
<script src="../assets/js/vendor/echarts.min.js"></script>
<script src="../assets/js/chart.js"></script>
<script src="js/page.js"></script>
<script src="../assets/js/price-page.js"></script>
</body>
</html>
"""

PAGE_JS = """/* 本页硬件类型（价格波动页通用逻辑会读取它） */
window.PRICE_TYPE = '{ptype}';
"""

price_css = open(os.path.join(BASE, "assets", "css", "price.css"), encoding="utf-8").read()

for ptype, folder, fname, title, spec in PAGES:
    page_dir = os.path.join(BASE, folder)
    os.makedirs(os.path.join(page_dir, "css"), exist_ok=True)
    os.makedirs(os.path.join(page_dir, "js"), exist_ok=True)
    html = HTML_TMPL.format(
        ptype=ptype, title=title, spec=spec,
        icon=ICONS[ptype],
        func_icon=INFO_ICONS["func"], scene_icon=INFO_ICONS["scene"], pitfall_icon=INFO_ICONS["pitfall"],
    )
    with open(os.path.join(page_dir, fname), "w", encoding="utf-8") as f:
        f.write(html)
    with open(os.path.join(page_dir, "css", "price.css"), "w", encoding="utf-8") as f:
        f.write(price_css)
    with open(os.path.join(page_dir, "js", "page.js"), "w", encoding="utf-8") as f:
        f.write(PAGE_JS.format(ptype=ptype))
    print("OK", folder, "->", fname, "| css/price.css | js/page.js")
print("DONE", len(PAGES), "pages")
