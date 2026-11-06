# -*- coding: utf-8 -*-
"""安全加固后同步《功能整理文档》：根管理员密码改为环境变量注入 + 新增安全加固变更记录。"""
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


count = 0
for p in doc.paragraphs:
    t = p.text
    if "内置账号启动幂等创建" in t and "comtoapi" in t:
        set_text(p, "#    内置账号启动幂等创建：Controler（密码见本地 backend-env.bat 的 ADMIN_INIT_PASSWORD，不入库）、demo / demo123（演示）")
        count += 1
    elif "根管理员：Controler" in t and "comtoapi" in t:
        set_text(p, "根管理员：Controler（密码见本地 backend-env.bat 的 ADMIN_INIT_PASSWORD，不入库；管理中心全部功能，后端服务管理仅此账号可用）；")
        count += 1
    elif "管理员体系（2026-11-05）" in t and "comtoapi" in t:
        set_text(p, "管理员体系（2026-11-05）：新增根管理员 Controler（密码由环境变量注入，不入库）与管理中心页面——启动爬虫按钮（含统计面板）、AI 对话端 API 接入（密钥/地址/模型均无默认值，保存即时生效）、用户删改（改角色/重置密码/删除，根管理员受保护）；")
        count += 1

doc.add_paragraph(
    "安全加固（2026-11-06）：数据库密码与 JWT 密钥改为环境变量/本地密钥文件注入（backend-env.bat / 爬虫/.dbsecret，"
    "均已 gitignore 不入库）并完成轮换；后端改用最小权限 MySQL 账号 hwapp（仅 hw_price 库增删改查，无 DDL）；"
    "根管理员 Controler 初始密码改为 ADMIN_INIT_PASSWORD 注入（代码/文档不再出现明文口令）；"
    "AI 问答增加长度限制（文本 2000 字 / 图片 2MB，超长在扣额度前拒绝）；"
    "登录/注册接口限流（同 IP 30 秒 5 次，超限 42902）；Swagger 与 CORS 白名单支持环境变量开关（SWAGGER_ENABLED / CORS_ALLOWED_ORIGINS）。",
    style="List Bullet")

doc.save(DOC)
print("doc updated, comtoapi replaced:", count)
