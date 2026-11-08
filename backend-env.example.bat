@echo off
REM ============================================================
REM 环境变量模板（复制为 backend-env.bat 后填写，请勿提交到公开仓库）
REM   copy backend-env.example.bat backend-env.bat
REM backend-env.bat 已被 .gitignore 忽略；start-backend.bat 启动时会自动加载
REM ============================================================

REM ---- MySQL 数据库账号（建议使用最小权限账号 hwapp，仅 hw_price 库增删改查）----
REM 创建最小权限账号（可选）：python 爬虫\tools\create_app_db_user.py
set "DB_USER=hwapp"
set "DB_PASSWORD=请填写你的MySQL密码"

REM ---- JWT 签名密钥（>= 32 字节随机串，生产环境务必替换）----
set "JWT_SECRET=请生成一段至少32字节的随机字符串"

REM ---- 根管理员 Controler 初始密码（启动时幂等创建；留空则跳过初始化）----
set "ADMIN_INIT_PASSWORD=请填写管理员初始密码"

REM ---- 可选：部署环境收紧 ----
REM set "CORS_ALLOWED_ORIGINS=https://your.domain"
REM set "SWAGGER_ENABLED=false"
