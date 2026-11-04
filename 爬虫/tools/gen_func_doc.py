# -*- coding: utf-8 -*-
"""生成《硬件比价网站_功能整理文档.docx》：整理当前系统的全部功能。

运行：用 DSH 自带 Python（含 python-docx 1.2.0）执行本脚本。
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

OUT = r"D:\AI电脑购买指导项目\硬件比价网站_功能整理文档.docx"

EAST = "微软雅黑"
ASCII = "Calibri"
MONO = "Consolas"
DARK = RGBColor(0x1F, 0x2D, 0x3D)
ACCENT = RGBColor(0x0E, 0x7A, 0x5F)
GRAY = RGBColor(0x6B, 0x76, 0x80)
HEADER_BG = "1F2D3D"
ALT_BG = "F4F7F9"


def set_run(run, size=None, bold=None, color=None, east=EAST, ascii_=ASCII,
            italic=None):
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), ascii_)
    rfonts.set(qn("w:hAnsi"), ascii_)
    rfonts.set(qn("w:eastAsia"), east)
    run.font.name = ascii_
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic
    if color is not None:
        run.font.color.rgb = color


def p(doc, text="", size=10.5, bold=False, color=DARK, style=None,
      align=None, space_after=6, east=EAST):
    para = doc.add_paragraph(style=style)
    if text:
        run = para.add_run(text)
        set_run(run, size=size, bold=bold, color=color, east=east)
    if align is not None:
        para.alignment = align
    para.paragraph_format.space_after = Pt(space_after)
    return para


def h1(doc, text):
    para = doc.add_heading("", level=1)
    run = para.add_run(text)
    set_run(run, size=16, bold=True, color=DARK)
    para.paragraph_format.space_before = Pt(14)
    para.paragraph_format.space_after = Pt(6)
    return para


def h2(doc, text):
    para = doc.add_heading("", level=2)
    run = para.add_run(text)
    set_run(run, size=13, bold=True, color=ACCENT)
    para.paragraph_format.space_before = Pt(10)
    para.paragraph_format.space_after = Pt(4)
    return para


def bullet(doc, text, size=10.5):
    para = doc.add_paragraph(style="List Bullet")
    run = para.add_run(text)
    set_run(run, size=size, color=DARK)
    para.paragraph_format.space_after = Pt(2)
    return para


def code(doc, text, size=9.5):
    para = doc.add_paragraph()
    run = para.add_run(text)
    set_run(run, size=size, color=RGBColor(0x24, 0x35, 0x4A), east=MONO, ascii_=MONO)
    para.paragraph_format.space_after = Pt(2)
    para.paragraph_format.left_indent = Cm(0.6)
    return para


def shade(cell, hexcolor):
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), hexcolor)
    tcpr.append(shd)


def table(doc, headers, rows, widths=None, font_size=9.5, header_size=9.5):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, htext in enumerate(headers):
        cell = t.rows[0].cells[j]
        cell.text = ""
        run = cell.paragraphs[0].add_run(htext)
        set_run(run, size=header_size, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))
        shade(cell, HEADER_BG)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = t.rows[i + 1].cells[j]
            cell.text = ""
            run = cell.paragraphs[0].add_run(str(val))
            set_run(run, size=font_size, color=DARK)
            if i % 2 == 1:
                shade(cell, ALT_BG)
    if widths:
        for j, w in enumerate(widths):
            for row in t.rows:
                row.cells[j].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


doc = Document()

# A4
for sec in doc.sections:
    sec.page_width = Cm(21.0)
    sec.page_height = Cm(29.7)
    sec.top_margin = Cm(2.2)
    sec.bottom_margin = Cm(2.2)
    sec.left_margin = Cm(2.4)
    sec.right_margin = Cm(2.4)

# Normal 默认字体
normal = doc.styles["Normal"]
normal.font.name = ASCII
normal.font.size = Pt(10.5)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), EAST)

# ===================== 封面 =====================
p(doc, "", space_after=120)
p(doc, "硬核比价 · 硬件价格比价与智能推荐网站", size=26, bold=True, color=DARK,
  align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)
p(doc, "功能整理文档", size=20, bold=True, color=ACCENT,
  align=WD_ALIGN_PARAGRAPH.CENTER, space_after=30)
p(doc, "版本 2.0（2026-11-04 更新）", size=12, color=GRAY,
  align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)
p(doc, "前端 HTML/CSS/JS + ECharts ｜ 后端 Java Spring Boot ｜ 采集 Python 爬虫",
  size=11, color=GRAY, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)
p(doc, "数据源：中关村在线（ZOL）参考报价", size=11, color=GRAY,
  align=WD_ALIGN_PARAGRAPH.CENTER, space_after=40)

p(doc, "目录", size=14, bold=True, color=DARK, space_after=8)
toc_items = [
    "一、项目概述与数据源变更",
    "二、系统架构与数据流",
    "三、前端功能（13 个页面）",
    "四、后端功能（Spring Boot）",
    "五、数据采集子系统（Python 爬虫）",
    "六、高性价比推荐",
    "七、数据库设计（9 张表）",
    "八、运行与部署",
    "九、已知限制与后续规划",
    "十、近期变更记录（2026-11-04）",
]
for item in toc_items:
    p(doc, item, size=11, color=DARK, space_after=4,
      style="List Number" if False else None)
doc.add_page_break()

# ===================== 一、概述 =====================
h1(doc, "一、项目概述与数据源变更")
p(doc, "本网站是面向个人装机与硬件选购的比价与智能推荐平台：聚合中关村在线（ZOL）"
       "参考报价，提供 10 类硬件的 30 天价格走势折线图与“高性价比推荐”，并内置 AI "
       "装机顾问（预算配机、型号对比、配置单图片识别），配套订阅套餐与 AI 问答额度体系。")
h2(doc, "1.1 技术栈")
table(doc,
      ["模块", "技术选型", "说明"],
      [
          ["前端", "原生 HTML/CSS/JS + ECharts 5.5.1", "无框架；暗色科技风；双击即可离线演示（Mock 模式）"],
          ["后端", "Spring Boot 3.5 + Spring Security(JWT) + MyBatis-Plus + Redis(可降级)", "REST 接口 + Swagger 文档；额度计数器 Redis/数据库双实现"],
          ["数据采集", "Python 3.9+：requests + lxml + pandas + PyMySQL", "每日 4 次定时抓取 ZOL 参考报价写入 MySQL"],
          ["数据库", "MySQL 8（hw_price 库，9 张表）", "价格时序由爬虫写入、后端只读聚合"],
          ["AI 能力", "统一网关：本地 Mock 规则引擎 / OpenAI 兼容接口", "回答强制“简短大白话”，注入实时价格上下文"],
      ],
      widths=[2.4, 7.0, 7.0])
h2(doc, "1.2 数据源变更说明（2026-11）")
p(doc, "原设计从京东 / 天猫 / 淘宝三平台采集价格，2026 年实测三大平台反爬全面收紧"
       "（京东风控验证页、淘宝/天猫搜索页改为 React 空壳、价格接口需登录 Cookie），"
       "真实抓取已不可行。现已切换为抓取中关村在线（ZOL）参考报价：无需登录、无验证码、"
       "结构稳定，覆盖全部 10 个硬件类目；旧三平台采集器代码保留备用，恢复多平台"
       "真实价的升级路线（京东联盟开放平台 API、Playwright 浏览器渲染）记录于"
       "爬虫子模块的《真实抓取改进建议.md》。")

# ===================== 二、架构 =====================
h1(doc, "二、系统架构与数据流")
p(doc, "系统为三层结构：前端页面（浏览器）→ 后端 REST 服务（Java）→ MySQL；"
       "Python 爬虫独立运行，直接写库，后端只负责读取聚合。")
bullet(doc, "采集链路：ZOL 类目页（定位 45 个目录型号的详情页链接）→ 型号详情页"
           "“参考报价”提取 → pandas 清洗（价格标准化、异常剔除）→ 幂等写入 "
           "t_product / t_price_history；")
bullet(doc, "展示链路：前端调用 GET /api/public/price/series → 后端按“型号 × 日期”"
           "聚合 30 天价格与性能分 → 前端渲染折线图 + 高性价比推荐表；")
bullet(doc, "AI 链路：前端 POST /api/auth/ai/chat（JWT 鉴权 + 额度门禁）→ 后端"
           "注入近 3 日价格上下文 → Mock 规则引擎或 OpenAI 兼容模型应答 → 扣减额度写流水。")

# ===================== 三、前端 =====================
h1(doc, "三、前端功能（13 个页面）")
table(doc,
      ["页面", "文件", "功能说明"],
      [
          ["首页", "首页/shouye.html", "搜索框（型号/类目模糊搜索）、10 类硬件入口、数据来源说明、AI 装机顾问入口与引导横幅"],
          ["价格波动页 ×10", "CPU/GPU/台式机内存/笔记本内存/固态硬盘/移动便携固态硬盘/移动便携机械硬盘/显示屏/键盘/鼠标", "每个类目一个页面：功能作用/适用场景/易踩坑点文案卡片 + 30 天价格折线图 + 高性价比推荐表"],
          ["登录 / 注册", "登录界面/denlu.html", "游客可浏览价格；注册默认免费级；登录后解锁 AI 问答与订阅"],
          ["我的账户与订阅", "账户/gerenxingxi.html", "当前订阅与有效期、日/月额度进度条、4 档套餐订阅（比赛模式即订即激活）、额度消耗明细分页"],
      ],
      widths=[2.6, 5.0, 8.8])

h2(doc, "3.1 价格波动页（10 个，同模板生成）")
bullet(doc, "文案卡片：功能作用、适用场景、容易踩坑点三块知识卡片（文案存于 "
           "t_hardware 表，随接口下发）；")
bullet(doc, "折线图：近 30 天价格走势，每个收录型号一条折线；点击图例可显示/隐藏"
           "任意型号，滚轮或拖动缩放查看细节；")
bullet(doc, "高性价比推荐表：按“性价比指数”降序展示该类目全部型号，前 2 名标注"
           "绿色“高性价比之选”徽章、3-5 名标注“值得关注”（详见第六节）；")
bullet(doc, "数据更新说明：页面标注“爬虫每日 08:00 / 12:00 / 18:00 / 22:00 自动抓取”。")

h2(doc, "3.2 AI 助手（全站悬浮）")
bullet(doc, "全站右下角悬浮按钮“AI 助手”，游客点击引导登录，登录后打开问答抽屉；")
bullet(doc, "能力：预算+用途自动配机、两个型号对比、上传配置单/硬件图片把关"
           "（图片问答计 2 次额度）；")
bullet(doc, "快捷提问：抽屉内预置 3 个示例问题一键发送；")
bullet(doc, "额度联动：抽屉头部实时显示当日/当月剩余额度；额度用尽（code 42901）"
           "自动弹订阅升级窗；")
bullet(doc, "交互：Enter 发送、Shift+Enter 换行、右上角 ✕ 或 Esc 或点击遮罩关闭。")

h2(doc, "3.3 订阅与额度（账户页）")
bullet(doc, "4 档套餐卡片：免费版 / 基础版 / 专业版 / 旗舰版，价格与权益实时来自"
           "t_subscription_plan，改库即生效；")
bullet(doc, "额度进度：今日 / 本月已用与剩余可视化；消耗明细支持分页查询；")
bullet(doc, "比赛演示模式：订阅下单跳过支付直接激活（后端 app.subscribe.skip-payment）。")

h2(doc, "3.4 双模式运行")
bullet(doc, "Mock 模式（默认）：双击 首页/shouye.html 即可完整演示——数据与后端演示"
           "数据完全同源（10 类硬件、45 型号、30 天价格、4 档套餐），登录/订阅/额度/"
           "AI 全部本地模拟；演示账号 demo / demo123；")
bullet(doc, "真实模式：assets/js/config.js 把 API_MODE 改为 'real'，即切换到 Java "
           "后端 REST 接口，业务代码零改动。")

# ===================== 四、后端 =====================
h1(doc, "四、后端功能（Spring Boot）")
h2(doc, "4.1 接口清单（统一响应 {code, message, data}）")
table(doc,
      ["接口", "方法", "权限", "说明"],
      [
          ["/api/public/register", "POST", "游客", "注册（默认免费级）"],
          ["/api/public/login", "POST", "游客", "登录，返回 JWT + 套餐 + 剩余额度"],
          ["/api/public/hardware", "GET", "游客", "首页硬件分类列表（含近 3 日最低价）"],
          ["/api/public/search?keyword=", "GET", "游客", "搜索商品/型号/硬件类目"],
          ["/api/public/price/series?type=", "GET", "游客", "价格时序（折线数据 + 高性价比推荐）"],
          ["/api/public/price/content?type=", "GET", "游客", "硬件文案（功能/场景/避坑）"],
          ["/api/public/subscribe/plans", "GET", "游客", "4 个订阅套餐与权益"],
          ["/api/auth/ai/chat", "POST", "登录", "AI 问答（文本 1 次 / 图片 2 次额度）"],
          ["/api/auth/subscribe/order", "POST", "登录", "订阅下单（比赛模式直接激活）"],
          ["/api/auth/subscribe/me", "GET", "登录", "我的订阅（套餐/有效期/等级快照）"],
          ["/api/auth/quota", "GET", "登录", "当前套餐与剩余额度（日/月）"],
          ["/api/auth/quota/logs", "GET", "登录", "额度消耗明细（分页）"],
      ],
      widths=[5.6, 1.6, 1.6, 7.6])
p(doc, "错误契约：code=0 成功；42901 = AI 额度用尽（HTTP 429，前端弹升级窗）；"
       "40301 = 免费版图片问答被拒；401 = 未登录自动跳登录页。", size=9.5, color=GRAY)

h2(doc, "4.2 价格聚合与高性价比推荐")
p(doc, "后端从 t_price_history 按“型号 × 日期”聚合 30 天参考价；每个型号附性能分"
       "（t_product.perf_score）并计算性价比指数（公式见第六节）。热点数据走 Redis "
       "缓存（TTL 数分钟），Redis 不可用时自动直查数据库。")

h2(doc, "4.3 订阅与额度体系")
bullet(doc, "双重门禁：/api/auth/ai/** 先过 JWT 认证，再由 QuotaInterceptor 按等级"
           "原子扣减（文本 1 次、含图 2 次；免费级图片问答直接 403）；")
bullet(doc, "先扣减、后调用、失败返还：调用模型前置扣减，超时/失败自动返还并记负流水；")
bullet(doc, "计数器双实现：默认优先 Redis（Lua 原子扣减，key 按日/月 TTL 自动过期），"
           "Redis 连不上自动降级为数据库计数器（条件 UPDATE 同样原子，跨日/月自动清零），"
           "没有 Redis 的比赛环境可完整演示；")
bullet(doc, "流水对账：每次消耗/返还异步写 t_ai_quota_log，可查明细、可重建计数器；")
bullet(doc, "到期回落：定时任务（默认每小时）把过期付费订阅回落免费级。")

h2(doc, "4.4 AI 问答")
bullet(doc, "系统提示词强制“简短的大白话”，注入网站近 3 日各硬件最低价 TOP3 上下文；")
bullet(doc, "两种实现：mock（默认零配置，本地规则引擎：预算解析、场景识别、型号对比，"
           "全部使用数据库真实价格）/ openai（OpenAI 兼容协议，支持 DeepSeek/通义等，"
           "图片自动转多模态消息）。")

h2(doc, "4.5 安全")
p(doc, "Spring Security + JWT 无状态认证；密码 BCrypt 加盐存储；CORS 与全局异常"
       "处理；请求体缓存过滤器支持拦截器重复读取。")

# ===================== 五、爬虫 =====================
h1(doc, "五、数据采集子系统（Python 爬虫）")
h2(doc, "5.1 采集流程")
p(doc, "每轮采集（约 4-6 分钟，全程限速防封）：")
code(doc, "1) 遍历 10 个硬件类目的 ZOL 分类列表页（单页全量、不分页）；")
code(doc, "2) 解析页内商品条目（名称 + 型号页链接），用归一化匹配对应到目录 45 个 SKU")
code(doc, "   （兼容 \"i5 12400F\" / \"i5-12400F\"、\"R5 5600\" / \"Ryzen 5 5600\" 等写法差异）；")
code(doc, "3) 型号未直接列出时，跟随系列筛选链接（如 \"RTX 4080 SUPER\" → /vga/s11033/）")
code(doc, "   进系列页二次定位；类目页偶发返回精简版时自动重取合并；")
code(doc, "4) 逐型号抓详情页，提取\"参考报价\"（GBK 编码页面）；")
code(doc, "5) pandas 清洗（价格标准化、异常剔除、中位价聚合）→ 幂等写入 MySQL")
code(doc, "   （同日重跑刷新价格，绝不产生重复行）。")
h2(doc, "5.2 反爬与健壮性机制")
bullet(doc, "限速：请求间隔 3 秒、单并发（ZOL 有防刷限流）；失败按指数退避重试；")
bullet(doc, "浏览器指纹头（sec-ch-ua 等）——ZOL 对无指纹请求返回精简页面，带完整头"
           "才稳定返回全量商品列表；")
bullet(doc, "封禁识别：页面跳 service.zol.com.cn/checking 防刷验证时上报封禁信号，"
           "自动切换模拟行情兜底并告警；")
bullet(doc, "匹配防误配：长型号优先（RTX 4060 不会误配 RTX 4060 Ti）、容量/内存代际"
           "冲突拒绝（三星 T7（2TB）不会配给 1TB 目录条目）、品牌别名表（西数=西部数据 等）；")
bullet(doc, "模式：auto（真实抓取，失败自动降级模拟行情）/ real（只走真实）/ "
           "mock（纯模拟）；每日 08:00/12:00/18:00/22:00 定时调度；")
bullet(doc, "监控告警：每轮成功率统计落盘，封禁/成功率低/连续失败自动写告警文件"
           "（可配 webhook）。")
h2(doc, "5.3 实测采集效果（2026-11-04）")
p(doc, "全量真实采集一轮：46 请求 / 0 失败 / 0 封禁，25 个型号当日真实参考价入库；"
       "45 个型号当日全部有数据（其余为同口径演示价，次日采集继续尝试）。"
       "个别型号 ZOL 未收录（i5-13490F 中国特供、闪迪 E61 等），属数据源正常缺口，"
       "可在目录里为该条目手动指定 zol_url 补齐。")

# ===================== 六、高性价比推荐 =====================
h1(doc, "六、高性价比推荐")
p(doc, "数据源切换后，“推荐购买平台”升级为“高性价比推荐”。每个收录型号维护一个"
       "性能分（1-100，同类目内相对性能，人工维护），结合当日参考价计算性价比指数：")
p(doc, "性价比指数 = 性能分 ÷ 参考价 × 1000", size=13, bold=True, color=ACCENT,
  align=WD_ALIGN_PARAGRAPH.CENTER)
p(doc, "指数越大越划算（同价位性能越高、同性能价格越低）。价格页推荐表按指数降序"
       "展示，前 2 名标注“高性价比之选”。示例（CPU 类目，2026-11-04 数据）：",
  space_after=8)
table(doc,
      ["型号", "今日参考价", "性能分", "性价比指数", "推荐"],
      [
          ["Intel i5-13490F（10核16线程）", "¥1110.75", "62", "55.8", "高性价比之选"],
          ["Intel i7-13700KF（16核24线程）", "¥1813.44", "82", "45.2", "高性价比之选"],
          ["Intel i5-12400F（6核12线程）", "¥1219.00", "55", "45.1", "值得关注"],
          ["AMD R5 5600（6核12线程）", "¥1359.00", "52", "38.3", "—"],
          ["AMD R7 7800X3D（8核16线程）", "¥3099.00", "90", "29.0", "—"],
      ],
      widths=[5.6, 2.6, 1.8, 2.6, 3.8])
p(doc, "性能分维护位置：后端 tools/gen_sample_data.py 的 PRODUCTS 第 6 列"
       "（重新生成 init_data.sql 即同步到演示数据；线上库用迁移脚本更新）。"
       "前端 Mock 演示层的性能分随 data.js 自动生成，无需二次维护。", size=9.5, color=GRAY)

# ===================== 七、数据库 =====================
h1(doc, "七、数据库设计（9 张表）")
table(doc,
      ["表", "用途"],
      [
          ["t_user", "用户（BCrypt 密码哈希、角色）"],
          ["t_hardware", "10 个硬件类目与文案（功能/场景/避坑）"],
          ["t_product", "45 个型号主数据（含 perf_score 性能分，用于高性价比推荐）"],
          ["t_price_history", "价格时序：商品 × 数据源 × 日期（爬虫写、后端只读）"],
          ["t_trade", "二手交易（预留，本期不开发）"],
          ["t_ai_session", "AI 问答会话记录"],
          ["t_subscription_plan", "4 档订阅套餐配置（改库即时生效）"],
          ["t_user_subscription", "用户订阅（等级快照 + 数据库额度计数器）"],
          ["t_ai_quota_log", "AI 额度消耗/返还流水（对账）"],
      ],
      widths=[4.6, 11.8])

# ===================== 八、运行 =====================
h1(doc, "八、运行与部署")
h2(doc, "8.1 前端")
code(doc, "# Mock 演示：直接双击 前端/首页/shouye.html（无需服务器、无需联网）")
code(doc, "# 或本地静态服务器：cd 前端 && python -m http.server 8080")
code(doc, "# 接真实后端：assets/js/config.js 中 API_MODE 改为 'real'")
h2(doc, "8.2 后端")
code(doc, "# 1. 建库建表  mysql -u root -p < sql/schema.sql")
code(doc, "# 2. 演示数据  mysql -u root -p hw_price < sql/init_data.sql")
code(doc, "# 3. application.yml 修改数据库密码")
code(doc, "# 4. 启动（IDEA 直接运行 HwPriceApplication 或 mvn spring-boot:run）")
code(doc, "# Swagger: http://localhost:8080/swagger-ui/index.html")
h2(doc, "8.3 爬虫")
code(doc, "cd 爬虫 && pip install -r requirements.txt")
code(doc, "python run.py once --mode real    # 单轮真实采集")
code(doc, "python run.py backfill --days 30  # 回填近 30 天时序")
code(doc, "python run.py schedule            # 每日 4 次定时调度")
code(doc, "python run.py report              # 查看采集统计与报告")
h2(doc, "8.4 演示账号与配置速查")
bullet(doc, "演示账号：demo / demo123（免费版 3 次/日）；")
bullet(doc, "关键配置：app.ai.provider=mock|openai；app.quota.store=auto|redis|db；"
           "app.subscribe.skip-payment=true（比赛模式跳过支付）；")
bullet(doc, "重新生成演示数据：python tools/gen_sample_data.py（后端）与 "
           "python gen_mock_data.py（前端 Mock 层，两者同源）。")

# ===================== 九、限制 =====================
h1(doc, "九、已知限制与后续规划")
table(doc,
      ["项目", "说明 / 规划"],
      [
          ["价格口径", "ZOL“参考报价”对部分老型号仍是官方指导价（如 R5 5600 显示 1359，市价约 600），页面已明确标注“参考报价”；要市价级精度可接京东联盟开放平台 API"],
          ["型号覆盖", "约 20 个目录型号 ZOL 未收录（中国特供/下架/命名不同），当日由同口径演示价填充；可人工指定 zol_url 补齐"],
          ["数据源数量", "当前为单一数据源（中关村在线）；多平台真实价路线：京东联盟 API（京东）+ Playwright 渲染（淘宝/天猫），代码方案已备于《真实抓取改进建议.md》"],
          ["二手交易（F5）", "按排期本期不开发，仅预留 t_trade 表"],
          ["支付", "订阅为比赛模式跳过支付，接支付需改 app.subscribe.skip-payment=false"],
      ],
      widths=[3.6, 12.8])

# ===================== 十、变更记录 =====================
h1(doc, "十、近期变更记录（2026-11-04）")
bullet(doc, "数据源切换：京东/天猫/淘宝 → 中关村在线（ZOL）参考报价；新增 "
           "hwspider/spiders/zol.py 采集器，配置、监控、文案全链路口径统一；")
bullet(doc, "推荐升级：“推荐购买平台”表改为“高性价比推荐”：t_product 新增 perf_score "
           "性能分，后端返回性价比指数，前端按指数排序并标注“高性价比之选”；")
bullet(doc, "数据库迁移：线上库 t_price_history 演示数据统一为“中关村在线”口径；"
           "t_product 增加性能分列并写入 45 个型号；")
bullet(doc, "界面文案清理：首页副标题/走势图例/数据来源标识/AI 建议语等全部去除"
           "“京东/天猫/淘宝”字样；")
bullet(doc, "Bug 修复：AI 助手抽屉右上角 ✕ 关闭按钮补上事件绑定（并支持 Esc 关闭）；")
bullet(doc, "演示数据同源重建：init_data.sql（后端）与 data.js（前端 Mock）均由同一"
           "数据生成，45 型号 × 30 天 × 单数据源。")

doc.save(OUT)
print("OK ->", OUT)
