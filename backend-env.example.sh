#!/usr/bin/env bash
# ============================================================
# 环境变量模板（复制为 backend-env.sh 后填写，请勿提交到公开仓库）
#   cp backend-env.example.sh backend-env.sh && chmod +x backend-env.sh
# backend-env.sh 已被 .gitignore 忽略；start-backend.sh 启动时会自动加载
# ============================================================

# ---- MySQL 数据库账号（建议使用最小权限账号 hwapp，仅 hw_price 库增删改查）----
# 创建最小权限账号（可选）：python 爬虫/tools/create_app_db_user.py
export DB_USER="hwapp"
export DB_PASSWORD="请填写你的MySQL密码"

# ---- JWT 签名密钥（>= 32 字节随机串，生产环境务必替换）----
export JWT_SECRET="请生成一段至少32字节的随机字符串"

# ---- 根管理员 Controler 初始密码（启动时幂等创建；留空则跳过初始化）----
export ADMIN_INIT_PASSWORD="请填写管理员初始密码"

# ---- 可选：部署环境收紧 ----
# export CORS_ALLOWED_ORIGINS="https://your.domain"
# export SWAGGER_ENABLED="false"
