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
p(doc, "版本 3.0（2026-11-05 更新）", size=12, color=GRAY,
  align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)
p(doc, "前端 HTML/CSS/JS + ECharts ｜ 后端 Java Spring Boot ｜ 采集 Python 爬虫",
  size=11, color=GRAY, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)
p(doc, "数据源：中关村在线（ZOL）参考报价（三重质量校验，仅真实采集价）", size=11, color=GRAY,
  align=WD_ALIGN_PARAGRAPH.CENTER, space_after=40)

p(doc, "目录", size=14, bold=True, color=DARK, space_after=8)
toc_items = [
    "一、项目概述与数据源变更",
    "二、系统架构与数据流",
    "三、前端功能（14 个页面）",
    "四、后端功能（Spring Boot）",
    "五、数据采集子系统（Python 爬虫）",
    "六、高性价比推荐",
    "七、数据库设计（10 张表）",
    "八、运行与部署",
    "九、已知限制与后续规划",
    "十、近期变更记录（2026-11-05）",
]
for item in toc_items:
    p(doc, item, size=11, color=DARK, space_after=4,
      style="List Number" if False else None)
doc.add_page_break()

# ===================== 一、概述 =====================
h1(doc, "一、项目概述与数据源变更")
p(doc, "本网站是面向个人装机与硬件选购的比价与智能推荐平台：聚合中关村在线（ZOL）"
       "参考报价，提供 10 类硬件的 30 天价格走势折线图与“高性价比推荐”（性能分由"
       "公开基准自动映射、指数对数归一化），并内置 AI 装机顾问（预算配机、型号对比、"
       "配置单图片识别），配套订阅套餐、AI 问答额度体系与管理员管理中心"
       "（爬虫启动、AI 网关配置、用户管理、后端服务管理）。")
h2(doc, "1.1 技术栈")
table(doc,
      ["模块", "技术选型", "说明"],
      [
          ["前端", "原生 HTML/CSS/JS + ECharts 5.5.1", "无框架；暗色科技风；默认真实模式，演示账号自动切 Mock 模式"],
          ["后端", "Spring Boot 3.5 + Spring Security(JWT) + MyBatis-Plus + Redis(可降级)", "REST 接口 + Swagger 文档；额度计数器 Redis/数据库双实现；内置管理员/演示账号启动幂等创建"],
          ["数据采集", "Python 3.9+：requests + lxml + pandas + PyMySQL", "默认只写真实采集价；三重质量校验（标题回校验 / ±30% 合理性 / 禁模拟冒充）"],
          ["数据库", "MySQL 8（hw_price 库，10 张表）", "价格时序由爬虫写入、后端只读聚合；source 列隔离真实/模拟数据"],
          ["AI 能力", "统一网关运行时路由：管理员配置密钥+地址+模型（无默认值）/ 本地 Mock 规则引擎", "回答强制“简短大白话”，注入实时价格上下文"],
      ],
      widths=[2.4, 7.0, 7.0])
h2(doc, "1.2 数据源变更说明（2026-11）")
p(doc, "原设计从京东 / 天猫 / 淘宝三平台采集价格，2026 年实测三大平台反爬全面收紧"
       "（京东风控验证页、淘宝/天猫搜索页改为 React 空壳、价格接口需登录 Cookie），"
       "真实抓取已不可行。现已切换为抓取中关村在线（ZOL）参考报价：无需登录、无验证码、"
       "结构稳定，覆盖全部 10 个硬件类目；旧三平台采集器代码保留备用，恢复多平台"
       "真实价的升级路线（京东联盟开放平台 API、Playwright 浏览器渲染）记录于"
       "爬虫子模块的《真实抓取改进建议.md》。")
h2(doc, "1.3 价格可信度保障（2026-11-05 起）")
p(doc, "ZOL“参考报价”存在错配与滞后指导价问题，为此入库前执行三重质量校验：")
bullet(doc, "型号页标题回校验：详情页 <title> 必须匹配回目录 SKU，防止把别的型号的"
            "价格记到目标型号头上（错配直接丢弃）；")
bullet(doc, "合理性校验：与目录基准价偏差超出 ±30% 视为错配/脏数据丢弃，当日不写入，"
            "后端聚合自动“沿用上一真实价”；")
bullet(doc, "真实/模拟隔离：默认模式只写真实采集价（source='real'），失败/封禁不再降级"
            "生成模拟价；采不到显示“暂无数据”。模拟价仅在显式 --mode mock 时写入"
            "（source='mock'），后端只聚合 source='real'，模拟价绝不会冒充真实价。")

# ===================== 二、架构 =====================
h1(doc, "二、系统架构与数据流")
p(doc, "系统为三层结构：前端页面（浏览器）→ 后端 REST 服务（Java）→ MySQL；"
       "Python 爬虫独立运行，直接写库，后端只负责读取聚合。")
bullet(doc, "采集链路：ZOL 类目页（定位 58 个目录型号的详情页链接）→ 型号详情页"
           "“参考报价”提取 → 三重质量校验（标题回校验、±30% 合理性校验、真实/模拟隔离）"
           "→ pandas 清洗 → 幂等写入 t_product / t_price_history（source='real'）；")
bullet(doc, "展示链路：前端调用 GET /api/public/price/series → 后端按“型号 × 日期”"
           "聚合 30 天真实采集价与基准性能分 → 前端渲染折线图 + 高性价比推荐表"
           "（采不到显示“暂无数据”）；")
bullet(doc, "AI 链路：前端 POST /api/auth/ai/chat（JWT 鉴权 + 额度门禁）→ 后端"
           "注入近 3 日真实价格上下文 → 运行时网关路由（配置了密钥走云端大模型，"
           "否则本地 Mock 规则引擎）→ 扣减额度写流水；")
bullet(doc, "管理链路：根管理员 Controler 登录管理中心 → 启动爬虫（拉起 Python 采集）、"
           "配置 AI 网关（密钥/地址/模型，无默认值）、用户删改、后端服务状态与重启"
           "（调用项目根目录 start/restart-backend 脚本，Windows/Linux 通用）。")

# ===================== 三、前端 =====================
h1(doc, "三、前端功能（14 个页面）")
table(doc,
      ["页面", "文件", "功能说明"],
      [
          ["首页", "首页/shouye.html", "搜索框（型号/类目模糊搜索）、10 类硬件入口、数据来源说明、AI 装机顾问入口与引导横幅"],
          ["价格波动页 ×10", "CPU/GPU/台式机内存/笔记本内存/固态硬盘/移动便携固态硬盘/移动便携机械硬盘/显示屏/键盘/鼠标", "每个类目一个页面：功能作用/适用场景/易踩坑点文案卡片 + 30 天价格折线图 + 高性价比推荐表（暂无数据显示“暂无数据”）"],
          ["登录 / 注册", "登录界面/denlu.html", "游客可浏览价格；注册默认免费级；演示账号不在页面展示，手动登录后自动切 Mock 模式"],
          ["我的账户与订阅", "账户/gerenxingxi.html", "当前订阅与有效期、日/月额度进度条、4 档套餐订阅（比赛模式即订即激活）、额度消耗明细分页"],
          ["管理中心", "管理/guanli.html", "仅管理员：爬虫启动与统计、AI 网关配置（无默认地址）、用户删改；后端服务管理仅根管理员 Controler 可见"],
      ],
      widths=[2.6, 5.0, 8.8])

h2(doc, "3.1 价格波动页（10 个，同模板生成）")
bullet(doc, "文案卡片：功能作用、适用场景、容易踩坑点三块知识卡片（文案存于 "
           "t_hardware 表，随接口下发）；")
bullet(doc, "折线图：近 30 天价格走势，每个收录型号一条折线；点击图例可显示/隐藏"
           "任意型号，滚轮或拖动缩放查看细节；缺口按真实情况断开，不编造数据；")
bullet(doc, "高性价比推荐表：按“性价比指数”（性能分 ÷ ln(参考价) × 100）降序展示"
           "该类目全部型号，前 2 名标注绿色“高性价比之选”徽章、3-5 名标注“值得关注”；"
           "性能分悬停可见依据（基准数值与公式）；无真实价的型号显示“暂无数据”并沉底；")
bullet(doc, "数据更新说明：页面标注真实采集口径与质量校验规则，不再承诺固定抓取时刻。")

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

h2(doc, "3.4 双模式运行（2026-11-05 起）")
bullet(doc, "真实模式（默认）：全部用户（含游客）走 Java 后端 REST 接口，只展示 "
           "source='real' 的真实采集价；API_BASE 默认 http://127.0.0.1:8080/api；")
bullet(doc, "Mock 演示模式：仅内置演示账号 demo / demo123（不在任何页面展示）登录后"
           "自动切换（顶栏显示“演示模式”徽章），退出登录自动切回真实模式；"
           "演示数据与 init_data.sql 同源（58 型号 × 30 天）；")
bullet(doc, "注册用户一律使用真实后端，绝不进入 Mock 模式；模式持久化于 localStorage，"
           "跨页面保持一致。")

h2(doc, "3.5 管理中心（仅管理员）")
bullet(doc, "权限：ROLE_ADMIN 可访问；其中“后端服务”卡片仅根管理员 Controler 可见"
           "（后端二次校验，其余管理员 403）；")
bullet(doc, "爬虫控制：一键启动爬虫（后端拉起 Python 子进程，只写真实价），展示最近"
           "一轮解析数、写入数、沿用上一真实价数、暂无数据数，运行期间每 10 秒自动刷新；")
bullet(doc, "AI 对话端 API 接入：密钥、接口地址、模型名均无默认值，填写保存后即时"
           "生效（密钥留空 = 清空并回落本地演示模型）；")
bullet(doc, "用户管理：列表（含套餐）/ 改角色（USER/ADMIN）/ 重置密码 / 删除"
           "（连同订阅、会话、额度流水）；根管理员 Controler 不可删除、不可改角色；")
bullet(doc, "后端服务：PID / 启动时间 / 运行时长 / Java 版本 / 操作系统状态展示，"
           "“重启后端服务”按钮执行项目根目录 restart-backend 脚本（Windows/Linux 自动选择）。")

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
          ["/api/public/price/series?type=", "GET", "游客", "价格时序（只聚合真实采集价 + 高性价比推荐）"],
          ["/api/public/price/content?type=", "GET", "游客", "硬件文案（功能/场景/避坑）"],
          ["/api/public/subscribe/plans", "GET", "游客", "4 个订阅套餐与权益"],
          ["/api/auth/ai/chat", "POST", "登录", "AI 问答（文本 1 次 / 图片 2 次额度）"],
          ["/api/auth/subscribe/order", "POST", "登录", "订阅下单（比赛模式直接激活）"],
          ["/api/auth/subscribe/me", "GET", "登录", "我的订阅（套餐/有效期/等级快照）"],
          ["/api/auth/quota", "GET", "登录", "当前套餐与剩余额度（日/月）"],
          ["/api/auth/quota/logs", "GET", "登录", "额度消耗明细（分页）"],
          ["/api/auth/admin/crawler/start", "POST", "ADMIN", "启动爬虫（后台子进程，只写真实价）"],
          ["/api/auth/admin/crawler/status", "GET", "ADMIN", "最近一轮抓取统计 + 运行状态"],
          ["/api/auth/admin/ai-config", "GET/POST", "ADMIN", "AI 网关配置（密钥打码；无默认地址）"],
          ["/api/auth/admin/users", "GET/PUT/DELETE", "ADMIN", "用户列表 / 改角色改密码 / 删除"],
          ["/api/auth/admin/backend/status", "GET", "根管理员", "后端服务状态（PID/运行时长/Java 版本）"],
          ["/api/auth/admin/backend/restart", "POST", "根管理员", "重启后端服务（执行 restart-backend 脚本）"],
      ],
      widths=[5.6, 1.6, 1.6, 7.6])
p(doc, "错误契约：code=0 成功；42901 = AI 额度用尽（HTTP 429，前端弹升级窗）；"
       "40301 = 无权限（含免费版图片问答、非根管理员访问后端服务管理）；"
       "401 = 未登录自动跳登录页。", size=9.5, color=GRAY)

h2(doc, "4.2 价格聚合与高性价比推荐")
p(doc, "后端只聚合 source='real' 的真实采集价（模拟演示数据隔离，绝不冒充真实价），"
       "按“型号 × 日期”聚合 30 天参考价；采不到的型号折线断开、推荐表显示“暂无数据”，"
       "最新价缺失时自动沿用上一真实采集价。每个型号附基准性能分"
       "（t_product.perf_score/perf_basis/perf_updated）并计算性价比指数（公式见第六节）。"
       "热点数据走 Redis 缓存（TTL 数分钟），Redis 不可用时自动直查数据库。")

h2(doc, "4.3 订阅与额度体系")
bullet(doc, "双重门禁：/api/auth/ai/** 先过 JWT 认证，再由 QuotaInterceptor 按等级"
           "原子扣减（文本 1 次、含图 2 次；免费级图片问答直接 403）；")
bullet(doc, "先扣减、后调用、失败返还：调用模型前置扣减，超时/失败自动返还并记负流水；")
bullet(doc, "计数器双实现：默认优先 Redis（Lua 原子扣减，key 按日/月 TTL 自动过期），"
           "Redis 连不上自动降级为数据库计数器（条件 UPDATE 同样原子，跨日/月自动清零），"
           "没有 Redis 的比赛环境可完整演示；")
bullet(doc, "流水对账：每次消耗/返还异步写 t_ai_quota_log，可查明细、可重建计数器；")
bullet(doc, "到期回落：定时任务（默认每小时）把过期付费订阅回落免费级。")

h2(doc, "4.4 AI 问答（运行时路由）")
bullet(doc, "系统提示词强制“简短的大白话”，注入网站近 3 日各硬件最低价 TOP3 上下文；")
bullet(doc, "网关路由：管理员在管理中心配置密钥+接口地址+模型名（均无默认值，"
           "任意 OpenAI 兼容网关如 DeepSeek/通义/Kimi）→ 走云端大模型；未配置密钥 "
           "自动回落本地 Mock 规则引擎（预算解析、场景识别、型号对比，全部使用"
           "数据库真实价格），切换即时生效、无需重启；")
bullet(doc, "保存校验：填密钥必须同时填接口地址与模型名，否则 400 拒绝；云端调用失败"
           "自动返还额度（code 50201）。")

h2(doc, "4.5 安全与账号体系")
bullet(doc, "Spring Security + JWT 无状态认证；密码 BCrypt 加盐存储；/api/auth/admin/** "
           "要求 ROLE_ADMIN，后端服务管理接口二次校验仅根管理员 Controler；")
bullet(doc, "内置账号启动幂等创建：根管理员 Controler（comtoapi，角色 ADMIN）、"
           "演示账号 demo（demo123，角色 USER），密码与角色不符时自动修复；")
bullet(doc, "应用配置表 t_app_config 存 AI 密钥等敏感配置（管理员维护，接口回显打码）。")

h2(doc, "4.6 后端服务管理（仅根管理员）")
bullet(doc, "状态：进程 PID、启动时间、运行时长、Java 版本、操作系统、jar 路径；")
bullet(doc, "重启：以分离子进程执行项目根目录 restart-backend.bat/.sh（Windows/Linux "
           "自动选择），脚本先等 3 秒（让管理接口响应发完）再结束旧进程并启动新实例，"
           "服务器环境同样可用。")

# ===================== 五、爬虫 =====================
h1(doc, "五、数据采集子系统（Python 爬虫）")
h2(doc, "5.1 采集流程")
p(doc, "每轮采集（约 4-6 分钟，全程限速防封）：")
code(doc, "1) 遍历 10 个硬件类目的 ZOL 分类列表页（单页全量、不分页）；")
code(doc, "2) 解析页内商品条目（名称 + 型号页链接），用归一化匹配对应到目录 58 个 SKU")
code(doc, "   （兼容 \"i5 12400F\" / \"i5-12400F\"、\"R5 5600\" / \"Ryzen 5 5600\" 等写法差异）；")
code(doc, "3) 型号未直接列出时，跟随系列筛选链接（如 \"RTX 4080 SUPER\" → /vga/s11033/）")
code(doc, "   进系列页二次定位；类目页偶发返回精简版时自动重取合并；")
code(doc, "4) 逐型号抓详情页，提取\"参考报价\"（GBK 编码页面）；")
code(doc, "5) 质量校验一：型号页标题回校验——页面 <title> 必须匹配回目标 SKU，")
code(doc, "   错配直接丢弃（统计 mismatch，防把别的型号价格记到目标型号）；")
code(doc, "6) 质量校验二：合理性校验——与目录基准价偏差超出 ±30% 视为错配/脏数据")
code(doc, "   丢弃，当日不写入 → 后端聚合自然\"沿用上一真实价\"；")
code(doc, "7) pandas 清洗（价格标准化、中位价聚合）→ 幂等写入 MySQL（source='real'），")
code(doc, "   同日重跑刷新价格，绝不产生重复行。")
h2(doc, "5.2 反爬与健壮性机制")
bullet(doc, "限速：请求间隔 3 秒、单并发（ZOL 有防刷限流）；失败按指数退避重试；")
bullet(doc, "浏览器指纹头（sec-ch-ua 等）——ZOL 对无指纹请求返回精简页面，带完整头"
           "才稳定返回全量商品列表；")
bullet(doc, "封禁识别：页面跳 service.zol.com.cn/checking 防刷验证时上报封禁信号并告警；"
           "**不再自动降级模拟行情**——采不到就\"暂无数据\"，模拟价绝不冒充真实价；")
bullet(doc, "匹配防误配：长型号优先（RTX 4060 不会误配 RTX 4060 Ti）、容量/内存代际"
           "冲突拒绝（三星 T7（2TB）不会配给 1TB 目录条目）、品牌别名表（西数=西部数据 等）"
           "、型号页标题回校验兜底；")
bullet(doc, "模式：real（默认，只写真实价）/ auto（同 real，保留兼容）/ mock（仅比赛"
           "演示与回填显式使用，入库 source='mock'，后端只聚合 source='real'，两条口径"
           "彻底隔离）；可配每日 08:00/12:00/18:00/22:00 定时调度；")
bullet(doc, "监控告警：每轮成功率/错配数/沿用数/暂无数据数统计落盘，封禁/成功率低/"
           "连续失败自动写告警文件（可配 webhook）。")
h2(doc, "5.3 实测采集效果（2026-11-05，修复后首轮）")
p(doc, "目录 58 个型号全量真实采集一轮：83 请求 / 57 解析 / 0 失败 / 0 封禁；"
       "质量校验拦下 31 条问题数据（标题回校验错配 1 条、偏离基准价 ±30% 的虚高/"
       "错配价 30 条，如 i7-13700KF 标 3700、RTX 4060 Ti 标 6800 等全部丢弃）；"
       "最终 27 个型号当日真实参考价入库（source='real'），其余 31 个型号如实显示"
       "\"暂无数据\"（首轮真实采集无历史价可沿用，后续轮次将自动沿用上一真实价）。")

# ===================== 六、高性价比推荐 =====================
h1(doc, "六、高性价比推荐")
p(doc, "每个收录型号的性能分（1-100）由可验证基准自动映射，不再人工拍脑袋："
       "CPU 用 PassMark CPU Mark（÷400 截断）、GPU 用 3DMark Time Spy Graphics（÷300 截断）、"
       "内存按官方频率/容量、固态按官方顺序读写、移动硬盘按容量、显示器按分辨率+刷新率、"
       "键鼠按官方轴体/传感器/回报率规格，全部公式与原始数值记录在性能分依据"
       "（perf_basis）与更新日期（perf_updated）中，单一数据源为项目根目录 "
       "perf_benchmarks.json。")
p(doc, "结合最新真实采集价计算性价比指数（对数归一化，抑制“越便宜分越高”的偏差，"
       "避免廉价低性能产品霸榜）：")
p(doc, "性价比指数 = 性能分 ÷ ln(参考价) × 100", size=13, bold=True, color=ACCENT,
  align=WD_ALIGN_PARAGRAPH.CENTER)
p(doc, "指数越大越划算（同价位性能越高、同性能价格越低）。价格页推荐表按指数降序"
       "展示，前 2 名标注“高性价比之选”；无真实价的型号显示“暂无数据”并沉底。"
       "示例（鼠标类目，2026-11-05 真实采集数据）：",
  space_after=8)
table(doc,
      ["型号", "参考价", "性能分", "性价比指数", "推荐"],
      [
          ["罗技 GPW 2（无线）", "¥739.00", "95", "1438.2", "高性价比之选"],
          ["罗技 G102（有线）", "¥99.00", "60", "1305.7", "高性价比之选"],
          ["雷蛇 蝰蛇V2X（无线）", "¥300.00", "65", "1139.6", "值得关注"],
          ["罗技 M185（无线）", "¥59.00", "25", "613.1", "—"],
      ],
      widths=[5.6, 2.6, 1.8, 2.6, 3.8])
p(doc, "对比旧公式（性能分 ÷ 价格 × 1000）下，¥39 的办公鼠标会以 641 分霸榜"
       "“高性价比之选”；改用对数归一化后，榜单由综合性能/价格表现决定，"
       "更符合“高性价比”预期。", size=9.5, color=GRAY)
p(doc, "性能分维护位置：perf_benchmarks.json（单一数据源）→ 后端 tools/gen_sample_data.py "
       "重新生成 init_data.sql、爬虫 tools/migrate_quality.py 迁移线上库；"
       "前端 Mock 演示层的性能分随 data.js 自动生成，三处同源、无需二次维护。",
  size=9.5, color=GRAY)

# ===================== 七、数据库 =====================
h1(doc, "七、数据库设计（10 张表）")
table(doc,
      ["表", "用途"],
      [
          ["t_user", "用户（BCrypt 密码哈希、角色 USER/ADMIN；内置根管理员与演示账号）"],
          ["t_hardware", "10 个硬件类目与文案（功能/场景/避坑）"],
          ["t_product", "58 个型号主数据（perf_score 基准性能分 + perf_basis 依据 + perf_updated 日期）"],
          ["t_price_history", "价格时序：商品 × 数据源 × 日期 + source 列（real=真实采集 mock=模拟演示，后端只聚合 real）"],
          ["t_trade", "二手交易（预留，本期不开发）"],
          ["t_ai_session", "AI 问答会话记录"],
          ["t_subscription_plan", "4 档订阅套餐配置（改库即时生效）"],
          ["t_user_subscription", "用户订阅（等级快照 + 数据库额度计数器）"],
          ["t_ai_quota_log", "AI 额度消耗/返还流水（对账）"],
          ["t_app_config", "应用配置（AI 网关密钥/地址/模型等，管理员维护）"],
      ],
      widths=[4.6, 11.8])

# ===================== 八、运行 =====================
h1(doc, "八、运行与部署")
h2(doc, "8.1 前端")
code(doc, "# 真实模式（默认）：双击任意页面即连本地后端 http://127.0.0.1:8080/api")
code(doc, "# Mock 演示：仅 demo / demo123 登录后自动切换（退出自动切回真实模式）")
code(doc, "# 本地静态服务器：cd 前端 && python -m http.server 8080")
h2(doc, "8.2 后端")
code(doc, "# 1. 建库建表  mysql -u root -p < sql/schema.sql")
code(doc, "# 2. 质量迁移  python 爬虫/tools/migrate_quality.py（建列/基准性能分/清模拟价）")
code(doc, "# 3. application.yml 修改数据库密码")
code(doc, "# 4. 启动：双击项目根目录 start-backend.bat（Linux 服务器：./start-backend.sh）")
code(doc, "#    内置账号启动幂等创建：Controler / comtoapi（管理员）、demo / demo123（演示）")
code(doc, "# Swagger: http://localhost:8080/swagger-ui/index.html")
h2(doc, "8.3 爬虫")
code(doc, "cd 爬虫 && pip install -r requirements.txt")
code(doc, "python run.py once --mode real    # 单轮真实采集（默认；采不到显示暂无数据）")
code(doc, "python run.py backfill --days 30  # 回填模拟时序（仅演示，source='mock'）")
code(doc, "python run.py schedule            # 每日 4 次定时调度")
code(doc, "python run.py report              # 查看采集统计与报告")
code(doc, "# 也可在管理中心点\"启动爬虫\"（后端自动拉起本轮真实采集）")
h2(doc, "8.4 启动 / 重启脚本（Windows 与 Linux 服务器通用）")
table(doc,
      ["脚本", "用途"],
      [
          ["start-backend.bat / start-backend.sh", "启动后端：自动定位 jar、自动找 Java（IDEA JBR → JAVA_HOME → PATH）、端口占用检测、日志落盘（Linux 另写 app.pid）"],
          ["restart-backend.bat / restart-backend.sh", "重启后端：先等 3 秒再结束旧进程并启动新实例；管理中心\"重启后端服务\"按钮（仅根管理员）调用"],
      ],
      widths=[5.8, 10.6])
h2(doc, "8.5 账号与配置速查")
bullet(doc, "根管理员：Controler / comtoapi（管理中心全部功能；后端服务管理仅此账号可用）；")
bullet(doc, "演示账号：demo / demo123（不在页面展示，登录后自动进 Mock 演示模式）；")
bullet(doc, "AI 网关：管理中心输入密钥+接口地址+模型名（无默认值），保存即时生效；"
           "未配置密钥自动用本地演示模型；")
bullet(doc, "关键配置：app.quota.store=auto|redis|db；app.subscribe.skip-payment=true"
           "（比赛模式跳过支付）；app.crawler.work-dir/command（爬虫启动命令）；")
bullet(doc, "演示数据同源重建：python tools/gen_sample_data.py（后端 init_data.sql）与 "
           "python gen_mock_data.py（前端 data.js），性能分统一来自 perf_benchmarks.json。")

# ===================== 九、限制 =====================
h1(doc, "九、已知限制与后续规划")
table(doc,
      ["项目", "说明 / 规划"],
      [
          ["价格口径", "ZOL“参考报价”对部分老型号仍是官方指导价，已被 ±30% 合理性校验自动拦截（显示“暂无数据”而非展示虚高价）；要市价级精度可接京东联盟开放平台 API"],
          ["型号覆盖", "目录 58 个型号全部有稳定 ZOL 数据源：34 个用 zol_url 直采详情页（绕过类目页轮换），其余由类目页匹配 + 标题回校验兜底；ZOL 未收录的型号已替换为同类替代品（SN770→金士顿KC3000、新小黑→东芝Basics A3、达尔优A98→狼蛛F87 Pro、ATK 68→洛斐小顺 Flow、三星32GB→英睿达32GB）"],
          ["数据源数量", "当前为单一数据源（中关村在线）；多平台真实价路线：京东联盟 API（京东）+ Playwright 渲染（淘宝/天猫），代码方案已备于《真实抓取改进建议.md》"],
          ["二手交易（F5）", "按排期本期不开发，仅预留 t_trade 表"],
          ["支付", "订阅为比赛模式跳过支付，接支付需改 app.subscribe.skip-payment=false"],
          ["定时采集", "爬虫定时调度需进程常驻（python run.py schedule）或挂系统计划任务；管理中心可随时手动启动一轮"],
      ],
      widths=[3.6, 12.8])

# ===================== 十、变更记录 =====================
h1(doc, "十、近期变更记录（2026-11-05）")
bullet(doc, "价格可信度（2026-11-05）：入库前三重质量校验——型号页标题回校验防错配、"
           "与基准价偏差超 ±30% 丢弃并沿用上一真实价、默认只写真实采集价"
           "（t_price_history 新增 source 列隔离模拟数据，后端只聚合 source='real'，"
           "采不到显示“暂无数据”）；清空线上模拟价重新真实采集；")
bullet(doc, "性价比公式（2026-11-05）：性能分 ÷ 参考价 × 1000 改为 性能分 ÷ ln(参考价) × 100"
           "（对数归一化），抑制“越便宜分越高”偏差，廉价低性能产品不再霸榜；")
bullet(doc, "性能分基准化（2026-11-05）：人工维护改为可验证基准自动映射 1-100"
           "（PassMark CPU Mark / 3DMark Time Spy / 官方规格），新增 perf_basis"
           "（依据公式与原始数值）与 perf_updated（更新日期），单一数据源 perf_benchmarks.json；")
bullet(doc, "管理员体系（2026-11-05）：新增根管理员 Controler（comtoapi）与管理中心页面"
           "——启动爬虫按钮（含统计面板）、AI 对话端 API 接入（密钥/地址/模型均无默认值，"
           "保存即时生效）、用户删改（改角色/重置密码/删除，根管理员受保护）；")
bullet(doc, "后端服务管理（2026-11-05）：新增 start/restart-backend 脚本"
           "（Windows .bat + Linux .sh，服务器通用），管理中心“后端服务”卡片"
           "（仅根管理员可见）展示状态并支持一键重启；")
bullet(doc, "Mock 模式切换（2026-11-05）：默认真实模式；演示账号 demo 不在页面展示，"
           "登录后自动切 Mock、退出自动切回；注册用户始终走真实后端；")
bullet(doc, "数据库（2026-11-05）：新增 t_app_config（AI 网关配置），共 10 张表；"
           "演示数据同源重建（init_data.sql 与 data.js，性能分随基准文件自动生成）；")
bullet(doc, "AI 网关运行时路由（2026-11-05）：配置密钥即走云端 OpenAI 兼容大模型，"
           "未配置自动回落本地 Mock 规则引擎，切换无需重启。")

doc.save(OUT)
print("OK ->", OUT)
