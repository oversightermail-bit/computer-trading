# -*- coding: utf-8 -*-
"""本地数据库密码读取（不入 Git）：环境变量 HW_DB_PASSWORD 优先，其次 爬虫/.dbsecret。

供 tools 下的维护脚本复用：
    from dbconn import password
    conn = pymysql.connect(host="127.0.0.1", user="root", password=password(), ...)
"""
import os
import pathlib


def password() -> str:
    v = os.environ.get("HW_DB_PASSWORD")
    if v:
        return v
    f = pathlib.Path(__file__).resolve().parent.parent / ".dbsecret"
    if f.exists():
        return f.read_text(encoding="utf-8").strip()
    raise RuntimeError("数据库密码未配置：请设置环境变量 HW_DB_PASSWORD，或在 爬虫/.dbsecret 写入密码")
