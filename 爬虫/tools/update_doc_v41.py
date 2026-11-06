# -*- coding: utf-8 -*-
"""功能整理文档同步最新代码：安全加固细节（限流/长度限制/hwapp 账号/环境变量开关）。"""
from docx import Document

DOC = r"D:\AI电脑购买指导项目\硬件比价网站_功能整理文档.docx"
doc = Document(DOC)


def set_text(p, text):
    if not p.runs:
        p.add_run(text)
        return
    p.runs[0].text = text
    for r in p.runs[1:]:
        r._element.getparent().remove(r._element)


hits = {"version": 0, "sec45": 0, "cfg": 0, "dbrow": 0}

# 1) 版本号
for p in doc.paragraphs:
    if p.text.strip().startswith("版本 4.0"):
        set_text(p, "版本 4.1（2026-11-06 更新）")
        hits["version"] += 1

# 2) 4.5 安全与账号体系：补限流/长度限制/最小权限账号
for p in doc.paragraphs:
    if "Spring Security + JWT 无状态认证" in p.text:
        set_text(p, "Spring Security + JWT 无状态认证；密码 BCrypt 加盐存储；/api/auth/admin/** 要求 ROLE_ADMIN，"
                    "后端服务管理接口二次校验仅根管理员 Controler；登录/注册接口限流（同 IP 30 秒 5 次，超限 42902）；"
                    "AI 问答输入长度限制（文本 2000 字 / 图片 2MB，超长在扣额度前拒绝）；"
                    "应用连接数据库使用最小权限账号 hwapp（仅增删改查，无 DDL），root 仅维护脚本使用；")
        hits["sec45"] += 1

# 3) 8.5 关键配置行：补安全环境变量
for p in doc.paragraphs:
    if p.text.startswith("关键配置："):
        set_text(p, "关键配置：app.quota.store=auto|redis|db；app.subscribe.payment.channel=mock|alipay|wechat"
                    "（模拟支付/真实接口切换，参数占位见 application-subscription.yml）；"
                    "app.crawler.work-dir/command/schedule-command（单轮/定时抓取命令）；")
        hits["cfg"] += 1
        # 在下一段前插入一行安全环境变量说明
        p.insert_paragraph_before(
            "安全环境变量（本地由 backend-env.bat 注入，均已 gitignore 不入库）：DB_USER/DB_PASSWORD（hwapp 账号）、"
            "JWT_SECRET（JWT 签名密钥）、ADMIN_INIT_PASSWORD（根管理员初始密码）；"
            "SWAGGER_ENABLED=false 关闭接口文档、CORS_ALLOWED_ORIGINS 收紧跨域白名单（部署时设置）。",
            style="List Bullet")

# 4) 技术栈表：数据库行说明补 hwapp
t0 = doc.tables[0]
for row in t0.rows:
    if row.cells[0].text.strip() == "数据库":
        cell = row.cells[2]
        p = cell.paragraphs[0]
        if p.runs:
            p.runs[0].text = "MySQL 8（hw_price 库，11 张表）｜ 价格时序由爬虫写入、后端只读聚合；source 列隔离真实/模拟数据；"
            p.runs[0].text += "应用连接使用最小权限账号 hwapp（仅增删改查）"
            for r in p.runs[1:]:
                r._element.getparent().remove(r._element)
        hits["dbrow"] += 1

doc.save(DOC)
print("hits:", hits)
