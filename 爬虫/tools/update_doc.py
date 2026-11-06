# -*- coding: utf-8 -*-
"""更新《硬件比价网站_功能整理文档.docx》至版本 4.0（2026-11-06）：
反映本轮代码改动（爬虫定时抓取、AI 免费/付费分档、订阅按钮规则、到期豁免、
额度调整、支付模块、兼容修复）。"""
from docx import Document
from docx.shared import Pt
from copy import deepcopy

DOC = r"D:\AI电脑购买指导项目\硬件比价网站_功能整理文档.docx"

doc = Document(DOC)
paras = doc.paragraphs


def set_text(p, text):
    """替换段落文本，保留段落样式；run 级格式以第一个 run 为准。"""
    if not p.runs:
        p.add_run(text)
        return
    p.runs[0].text = text
    for r in p.runs[1:]:
        r._element.getparent().remove(r._element)


def bullet(text):
    doc.add_paragraph(text, style="List Bullet")


# ---------- 1. 标题与版本 ----------
set_text(paras[3], "版本 4.0（2026-11-06 更新）")
set_text(paras[13], "七、数据库设计（11 张表）")
set_text(paras[16], "十、近期变更记录（2026-11-06）")
set_text(paras[117], "七、数据库设计（11 张表）")

# ---------- 2. 概述（一） ----------
set_text(paras[19],
         "本网站是面向个人装机与硬件选购的比价与智能推荐平台：聚合中关村在线（ZOL）参考报价，"
         "提供 10 类硬件的 30 天价格走势折线图与“高性价比推荐”（性能分由公开基准自动映射、"
         "指数对数归一化），并内置 AI 装机顾问（预算配机、型号对比、配置单图片识别），配套订阅套餐、"
         "AI 问答额度体系与管理员管理中心（爬虫启动/定时抓取、AI 网关免费/付费分档配置、用户管理、"
         "后端服务管理），订阅支付按“模拟支付 + 可切换真实接口”预留（真实账户付款码弹窗，"
         "营业执照办理后接入支付宝/微信）。")

# ---------- 3. 系统架构与数据流 ----------
set_text(paras[33],
         "AI 链路：前端 POST /api/auth/ai/chat（JWT 鉴权 + 额度门禁）→ 后端注入近 3 日真实价格上下文 → "
         "运行时网关按账户分档路由（免费账户走免费档配置、付费账户走付费档配置；该档未配密钥回落本地 "
         "Mock 规则引擎）→ 扣减额度写流水；")
set_text(paras[34],
         "管理链路：根管理员 Controler 登录管理中心 → 启动爬虫（拉起 Python 采集）与开启/停止定时抓取"
         "（每日 08/12/18/22 点，服务器常驻）、分档配置 AI 网关（免费/付费各一套密钥/地址/模型，无默认值）、"
         "用户删改、后端服务状态与重启（调用项目根目录 start/restart-backend 脚本，Windows/Linux 通用）。")

# ---------- 4. 前端 3.3 订阅与额度 ----------
set_text(paras[49],
         "4 档套餐卡片：免费版 / 基础版 / 专业版 / 旗舰版，价格与权益实时来自 t_subscription_plan，"
         "改库即生效；额度口径（2026-11-06）：免费版 3 次/日 · 15 次/月，基础版 100 次/月、专业版 300 次/月、"
         "旗舰版 600 次/月（付费方案只限每月次数，每日不限）；")
set_text(paras[51],
         "订阅支付（2026-11-06）：真实账户点击订阅弹付款码窗（营业执照未办理：显示“功能开发中，目前暂不支持”）；"
         "demo 演示账号与根管理员走模拟支付直接开通；后端支付模块保留完整流程（下单→支付确认→回调激活），"
         "app.subscribe.payment.channel 可切换真实接口；")

# ---------- 5. 前端 3.5 管理中心 ----------
set_text(paras[58],
         "爬虫控制：一键启动爬虫（后端拉起 Python 子进程，只写真实价），展示最近一轮解析数、写入数、"
         "沿用上一真实价数、暂无数据数，运行期间每 10 秒自动刷新；另有“开启定时抓取（每日 08/12/18/22 点）”"
         "按钮（服务器常驻调度进程，可随时停止），与单轮启动互不影响；")
set_text(paras[59],
         "AI 对话端 API 接入（免费/付费分档）：免费账户与付费账户各一套密钥、接口地址、模型名（均无默认值），"
         "分别保存即时生效；某档密钥留空 = 仅该档回落本地演示模型；")

# ---------- 6. 后端 4.3 订阅与额度 ----------
set_text(paras[73],
         "到期回落：定时任务（默认每小时）把过期付费订阅回落免费级；demo 演示账号与根管理员 Controler "
         "到期豁免——其付费订阅到期时间恒为空（长期有效），到期检查永不命中，保持当前方案不动；")

# ---------- 7. 后端 4.4 AI 问答 ----------
set_text(paras[76],
         "网关路由（免费/付费分档）：管理员在管理中心分别配置免费档（ai.free.*）与付费档（ai.paid.*）"
         "的密钥+接口地址+模型名（均无默认值，任意 OpenAI 兼容网关如 DeepSeek/通义/Kimi）→ 该档用户走云端大模型；"
         "某档未配置密钥仅该档自动回落本地 Mock 规则引擎（预算解析、场景识别、型号对比，全部使用数据库真实价格），"
         "切换即时生效、无需重启；路由按套餐判定（非免费套餐=付费档），不受到期时间影响；")

# ---------- 8. 后端 4.5 应用配置表 ----------
set_text(paras[81],
         "应用配置表 t_app_config 存 AI 网关免费/付费两档密钥等敏感配置（管理员维护，接口回显打码）。")

# ---------- 9. 爬虫 5.2 调度 ----------
set_text(paras[105],
         "模式：real（默认，只写真实价）/ auto（同 real，保留兼容）/ mock（仅比赛演示与回填显式使用，"
         "入库 source='mock'，后端只聚合 source='real'，两条口径彻底隔离）；定时调度每日 08:00/12:00/18:00/22:00 "
         "（python run.py schedule 或管理中心一键开启，服务器常驻）；")

# ---------- 10. 运行与部署 8.3 / 8.5 ----------
set_text(paras[137],
         "# 也可在管理中心点“启动爬虫”单轮采集，或点“开启定时抓取（每日 08/12/18/22 点）”长期运行")
set_text(paras[143],
         "AI 网关：管理中心分档配置（免费账户 / 付费账户各一套密钥+接口地址+模型名，均无默认值），保存即时生效；"
         "某档未配置密钥仅该档使用本地演示模型；")
set_text(paras[144],
         "关键配置：app.quota.store=auto|redis|db；app.subscribe.payment.channel=mock|alipay|wechat"
         "（模拟支付/真实接口切换，参数占位见 application-subscription.yml）；app.crawler.work-dir/command/"
         "schedule-command（单轮/定时抓取命令）；")

# ---------- 11. 近期变更记录追加（2026-11-06） ----------
bullet("爬虫控制升级（2026-11-06）：管理中心新增“开启定时抓取（每日 08/12/18/22 点）”，服务器常驻调度进程"
       "（python run.py schedule --mode real），可一键开启/停止，与单轮“启动爬虫”互不影响；"
       "新增配置项 app.crawler.schedule-command 与接口 /api/auth/admin/crawler/schedule/start、/stop；")
bullet("AI 网关免费/付费分档（2026-11-06）：管理中心 AI 接入改为免费账户与付费账户两套独立配置"
       "（ai.free.* / ai.paid.*），分别保存即时生效；某档未配密钥仅该档回落本地演示模型；"
       "旧版单档配置启动时一次性自动迁移到付费档；AI 路由按套餐判定（非免费套餐=付费档），不受到期时间影响；")
bullet("订阅方案按钮规则（2026-11-06）：真实账户免费方案一栏不显示任何“立即升级”按钮（仅显示“默认免费方案 · "
       "到期未续费自动切回”）；demo 演示账号与根管理员 Controler 可随便切换方案（免费方案显示“切换回免费版”）；")
bullet("到期豁免（2026-11-06）：demo 与 Controler 的付费订阅到期时间恒为空（长期有效），到期检查永不命中，"
       "保持当前方案不动；启动时一次性修复存量生效订阅；")
bullet("订阅额度调整（2026-11-06）：免费版 3 次/日 · 15 次/月（原 60/月）；基础版 100 次/月、专业版 300 次/月、"
       "旗舰版 600 次/月，付费方案只限每月次数——quota_day=0 表示每日不限（数据库条件 UPDATE 与 Redis Lua 脚本"
       "均跳过每日校验），前端只展示月额度；")
bullet("订阅支付模块（2026-11-06）：真实账户点击订阅弹付款码窗（营业执照未办理，显示“功能开发中，目前暂不支持”），"
       "demo 演示账号走模拟支付直接开通；后端保留完整支付流程——支付单表 t_pay_order、下单 /api/auth/subscribe/order、"
       "模拟支付确认 /api/auth/subscribe/pay/mock/confirm、支付异步回调 /api/public/subscribe/pay/notify（游客通道），"
       "PaymentChannel 抽象支持 mock / alipay / wechat 三通道，app.subscribe.payment.channel 切换真实接口"
       "（营业执照办理后实现通道类 TODO 即启用）；模拟支付确认与回调仅 demo/根管理员可用（真实账户 403）；")
bullet("兼容修复（2026-11-06）：后端 Long id 全局序列化为字符串（防 JS 精度丢失），前端套餐卡片统一 Number() 归一比较"
       "（修复免费方案误显示“¥0/月 立即升级”与“¥0/月”价格标签）；顶栏 logo 图固定 30×30 且品牌名不换行"
       "（修复默认 300×150 渲染挤压标题竖排、首行被挡）；“比赛演示模式”提示仅 demo 演示账号可见；")

# ---------- 12. 表格更新 ----------
def find_row(table, first_cell_text):
    for row in table.rows:
        if row.cells[0].text.strip() == first_cell_text:
            return row
    return None


def set_cell(row, idx, text):
    cell = row.cells[idx]
    p = cell.paragraphs[0]
    if not p.runs:
        p.add_run(text)
    else:
        p.runs[0].text = text
        for r in p.runs[1:]:
            r._element.getparent().remove(r._element)


def insert_row_after(table, ref_row, texts):
    new_row = table.add_row()
    for i, t in enumerate(texts):
        new_row.cells[i].text = t
    ref_row._tr.addnext(new_row._tr)
    return new_row


# 表格 0：技术栈表
t0 = doc.tables[0]
db_row = find_row(t0, "数据库")
if db_row is not None:
    set_cell(db_row, 2, "MySQL 8（hw_price 库，11 张表）｜ 价格时序由爬虫写入、后端只读聚合；source 列隔离真实/模拟数据")
ai_row = find_row(t0, "AI 能力")
if ai_row is not None:
    set_cell(ai_row, 2, "统一网关运行时路由：免费/付费两档各自配置密钥+地址+模型（无默认值）/ 本地 Mock 规则引擎｜ 回答强制“简短大白话”，注入实时价格上下文")

# 表格 1：页面表
t1 = doc.tables[1]
acct_row = find_row(t1, "我的账户与订阅")
if acct_row is not None:
    set_cell(acct_row, 2, "当前订阅与有效期、日/月额度进度条（付费方案每日不限）、4 档套餐订阅"
                           "（真实账户弹付款码·开发中；demo/根管理员模拟支付即订即激活）、额度消耗明细分页")
mgmt_row = find_row(t1, "管理中心")
if mgmt_row is not None:
    set_cell(mgmt_row, 2, "仅管理员：爬虫启动与定时抓取（每日 08/12/18/22 点）、AI 网关免费/付费分档配置"
                           "（无默认地址）、用户删改；后端服务管理仅根管理员 Controler 可见")

# 表格 2：接口表 —— 更新下单行 + 新增 4 行
t2 = doc.tables[2]
order_row = find_row(t2, "/api/auth/subscribe/order")
if order_row is not None:
    set_cell(order_row, 3, "订阅支付下单（mock 渠道返回模拟收款码；真实渠道预留）")
    insert_row_after(t2, order_row,
                     ["/api/auth/subscribe/pay/mock/confirm", "POST", "登录", "模拟支付确认（仅 demo/根管理员，激活套餐）"])
    notify_row = find_row(t2, "/api/auth/subscribe/pay/mock/confirm")
    insert_row_after(t2, notify_row,
                     ["/api/public/subscribe/pay/notify", "POST", "游客", "支付异步回调（真实接口预留，验签后激活订阅）"])
crawler_status_row = find_row(t2, "/api/auth/admin/crawler/status")
if crawler_status_row is not None:
    insert_row_after(t2, crawler_status_row,
                     ["/api/auth/admin/crawler/schedule/start", "POST", "ADMIN", "开启定时抓取（每日 08/12/18/22 点，服务器常驻）"])
    sched_start_row = find_row(t2, "/api/auth/admin/crawler/schedule/start")
    insert_row_after(t2, sched_start_row,
                     ["/api/auth/admin/crawler/schedule/stop", "POST", "ADMIN", "停止定时抓取"])

# 表格 4：数据库表 —— 更新 t_app_config + 新增 t_pay_order
t4 = doc.tables[4]
cfg_row = find_row(t4, "t_app_config")
if cfg_row is not None:
    set_cell(cfg_row, 1, "应用配置（AI 网关免费/付费两档密钥/地址/模型等，管理员维护）")
pay_row = t4.add_row()
set_cell(pay_row, 0, "t_pay_order")
set_cell(pay_row, 1, "订阅支付单（订单号/金额/通道 mock·alipay·wechat/状态，支付模块：模拟支付 + 真实接口预留）")

# 表格 6：已知限制 —— 支付行
t6 = doc.tables[6]
pay6_row = find_row(t6, "支付")
if pay6_row is not None:
    set_cell(pay6_row, 1, "支付模块已按“模拟支付 + 可切换真实接口”搭建（t_pay_order 支付单 + 下单/模拟确认/回调接口，"
                          "PaymentChannel 三通道抽象）；真实支付待营业执照办理后把 app.subscribe.payment.channel 改为 "
                          "alipay/wechat 并实现通道类 TODO 即启用；当前真实账户订阅弹“功能开发中”付款码窗，"
                          "demo 演示账号走模拟支付")

doc.save(DOC)
print("SAVED OK")
