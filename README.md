# 硬核比价 · 硬件价格比价与智能推荐网站

面向个人装机与硬件选购的**比价与智能推荐平台**：聚合中关村在线（ZOL）真实参考报价，提供 10 类硬件近 30 天价格走势、基于可验证基准的「高性价比推荐」，并内置 **AI 装机顾问**（预算配机、型号对比、配置单图片识别）与订阅额度体系，配套管理员管理中心（爬虫控制、AI 网关配置、用户管理、后端服务管理）。

| 模块 | 技术栈 |
|---|---|
| 前端 | 原生 HTML / CSS / JavaScript + ECharts 5.5.1（本地化，离线可用；无框架） |
| 后端 | Java 17 + Spring Boot 3.5 + Spring Security(JWT) + MyBatis-Plus + MySQL 8 + Redis（可降级） |
| 数据采集 | Python 3.9+：requests / lxml / pandas / PyMySQL（Scrapy 可用但非必需） |
| AI 能力 | OpenAI 兼容协议统一网关（DeepSeek / 通义 / Kimi 等均可接入，运行时路由）+ 本地 Mock 规则引擎兜底 |

> **演示账号**：`demo` / `demo123`（登录后自动进入 Mock 演示模式，数据与后端 `init_data.sql` 完全同源）。
> 根管理员账号 Controler 不随包预置、密码不入仓库：启动前在 `backend-env.bat`（模板）中自行填写 `ADMIN_INIT_PASSWORD`，后端首次启动时幂等创建该账号。
> **在线演示（静态版）**：<https://oversightermail-bit.github.io/web-display/>（Mock 模式演示，无需安装；静态页仅支持演示账号 `demo` 登录体验）。
> **当前版本**：v1.0.3（安全加固版），版本演进见下方「版本演进」。

## 功能特性

- **10 类硬件比价**：CPU / GPU / 台式机内存 / 笔记本内存 / 固态硬盘 / 移动固态 / 移动机械硬盘 / 显示屏 / 键盘 / 鼠标，每类一个价格波动页（知识卡片 + 30 天折线图 + 高性价比推荐表）；
- **数据真实可信**：入库前三重质量校验（型号页标题回校验、±30% 合理性校验、真实/模拟 `source` 隔离），模拟价绝不冒充真实价，采不到如实显示「暂无数据」；
- **AI 装机顾问**：预算配机、两型号对比、上传配置单图片把关；系统提示词强制「简短的大白话」，并注入近 3 日真实最低价上下文；
- **订阅与额度**：免费版 / 基础版 / 专业版 / 旗舰版 4 档套餐，AI 问答按次扣减额度（文本 1 次、图片 2 次），先扣减后调用、失败自动返还；
- **管理中心**：一键启动爬虫、开启定时抓取（每日 08/12/18/22 点）、AI 网关免费/付费分档配置、用户管理、后端服务状态与一键重启（仅根管理员）；
- **双模式运行**：默认真实后端模式；`demo` 账号登录后自动切换 Mock 演示模式（本地演示数据），退出登录自动切回真实模式。

## 技术架构

```
┌─────────────┐    REST {code,message,data}    ┌──────────────────────────────┐
│   浏览器前端   │ ──────────────────────────────▶ │   后端 Spring Boot (8080)     │
│  HTML/CSS/JS │  JWT / 额度门禁 / CORS          │  Auth · Price · AI · Subscribe │
│  + ECharts   │ ◀────────────────────────────── │  Quota(Lua/DB) · Admin        │
│  Mock 双模式  │                                └──────────────┬───────────────┘
└─────────────┘                                               │ MyBatis-Plus / Redis(可降级)
                                                              ▼
┌──────────────────────┐  只写 source='real'    ┌──────────────────────────────┐
│  爬虫 Python（独立运行） │ ──────────────────────▶ │        MySQL 8 (hw_price)     │
│  ZOL 采集 + 三重校验    │                        │  11 张表 · 价格时序 · 订阅额度   │
│  定时 08/12/18/22     │                        └──────────────────────────────┘
└──────────────────────┘
```

- **采集链路**：ZOL 类目页 → 型号详情页参考报价 → 三重质量校验 → pandas 清洗 → 幂等写入（`source='real'`）；
- **展示链路**：前端 `GET /api/public/price/series` → 后端只聚合 `source='real'` 真实采集价 → 折线图 + 高性价比推荐；
- **AI 链路**：`POST /api/auth/ai/chat`（JWT + 额度门禁，先扣减后调用）→ 注入实时价格上下文 → 运行时网关按账户分档路由云端大模型 / 本地 Mock → 写消耗流水（调用失败自动返还额度）。

## 目录结构

```
├── 前端/                    # 表现层：14 个页面 + 本地 ECharts + Mock/Real 双 API 层
├── 后端/                    # Spring Boot 服务：源码 src/、SQL 脚本 sql/、冒烟测试 tools/
├── 爬虫/                    # 数据采集子系统：run.py 入口、hwspider/ 引擎、tools/ 维护脚本
├── start-backend.bat/.sh    # 后端一键启动脚本（自动定位 jar 与 Java）
├── restart-backend.bat/.sh  # 后端重启脚本
├── backend-env.example.bat  # 环境变量模板（复制为 backend-env.bat 并填写，勿提交）
├── backend-env.example.sh
├── perf_benchmarks.json     # 性能分基准单一数据源（CPU/GPU/内存/固态等公开基准）
└── 各子模块 README：前端/README.md · 后端/README.md · 爬虫/README.md
```

## 快速开始

### 方式一：零依赖演示（推荐评委体验）

- **在线静态演示**（免下载安装）：访问 <https://oversightermail-bit.github.io/web-display/>（Mock 模式，仅支持演示账号 `demo` / `demo123` 登录）；
- **本地演示**：启动后端（见方式二）后双击 **`前端/首页/shouye.html`**，用 `demo` / `demo123` 登录即自动进入 Mock 演示模式——数据、图表、登录、订阅、AI 问答全部本地模拟，此后离线亦可完整演示。

### 方式二：完整启动（前端 + 后端 + MySQL）

1. 安装 **JDK 17+**、**MySQL 8**（Redis 可选，缺失自动降级）；
2. 建库导入：`mysql -u root -p < 后端/sql/schema.sql`，`mysql -u root -p hw_price < 后端/sql/subscription_schema.sql`（补齐订阅/支付表），`mysql -u root -p hw_price < 后端/sql/init_data.sql`；
3. 复制环境变量模板并填写本机 MySQL 密码（见下节「环境配置」）；
4. 双击根目录 `start-backend.bat`（Linux：`./start-backend.sh`），或 `java -jar 后端/target/hw-price-backend-1.0.0.jar`；
5. 访问 <http://127.0.0.1:8080/swagger-ui/index.html> 验证接口；前端默认 `API_MODE='real'` 直连本地后端（`前端/assets/js/config.js` 可切换）。

### 方式三：启动爬虫（可选）

```bash
cd 爬虫
pip install -r requirements.txt
python run.py once --mode real   # 单轮真实采集（只写真实价）
python run.py backfill --days 30 # 回填 30 天演示时序（source='mock'）
python run.py schedule           # 每日 4 次定时调度
```

## 环境配置说明

所有敏感配置均通过**环境变量 / 本地密钥文件**注入，仓库中不含任何明文密钥：

| 环境变量 | 用途 | 默认值 | 必填 |
|---|---|---|---|
| `DB_USER` / `DB_PASSWORD` | 后端 MySQL 账号（建议最小权限账号 hwapp，仅增删改查） | `root` / 无 | `DB_PASSWORD` 必填 |
| `JWT_SECRET` | JWT HS256 签名密钥（≥32 字节随机串） | 无 | 必填 |
| `ADMIN_INIT_PASSWORD` | 根管理员 Controler 初始密码（启动时幂等创建） | 空（跳过初始化） | 建议填写 |
| `HW_DB_USER` / `HW_DB_PASSWORD` | 爬虫 MySQL 账号；未设置时回退 `爬虫/.dbsecret` 文件 | `root` / 文件 | 爬虫入库时必填其一 |
| `CORS_ALLOWED_ORIGINS` | CORS 白名单（逗号分隔）；空 = 开发期全放行 | 空 | 部署时建议设置 |
| `SWAGGER_ENABLED` | 是否开启 Swagger 接口文档 | `true` | 部署时建议 `false` |

使用步骤：

```bash
# Windows：复制模板 → 填写本机值 → 启动脚本自动加载（模板与真实文件均已 gitignore）
copy backend-env.example.bat backend-env.bat
# Linux：cp backend-env.example.sh backend-env.sh && chmod +x backend-env.sh
# 爬虫（可选）：echo "你的数据库密码" > 爬虫/.dbsecret
```

## 依赖清单

- **前端**：无任何第三方运行时依赖（ECharts 已本地化，离线可用）；
- **后端**：JDK 17+、Maven 3.8+（仅构建需要；已附编译产物 jar 时无需 Maven）、MySQL 8、Redis 可选；
- **爬虫**：Python 3.9+，`pip install -r 爬虫/requirements.txt`（Scrapy / lxml / pandas / PyMySQL 等，详见该文件）。

## 版本演进

### v1.0.0 ｜ 后端与爬虫完成（核心服务与数据链路闭环）

- **后端（Java 17 + Spring Boot 3.5）**：统一响应 `{code, message, data}` 与全局异常；JWT 注册 / 登录；硬件类目、搜索、价格时序、硬件文案等公开接口；订阅与额度体系（4 档套餐，先扣减后调用、失败自动返还）；AI 问答（本地 Mock 演示模型 + OpenAI 兼容网关接口）；管理员接口（爬虫控制 / AI 网关配置 / 用户管理 / 后端服务管理）；MySQL 11 张表（`schema.sql` 10 张基础表 + `subscription_schema.sql` 支付单表），配套 `tools/gen_sample_data.py` 演示数据生成与 `tools/smoke_test.ps1` 一键冒烟测试。
- **爬虫（Python 3.9+）**：`run.py` 命令入口（once / backfill / schedule / report / init）；`hwspider/` 引擎（采集 → 清洗 → 入库 → 推荐 → 监控）；按需求文档实现京东 / 天猫 / 淘宝三平台 Spider；pandas 清洗 + 幂等 upsert 入库（`t_product` / `t_price_history`，真实/模拟 `source` 隔离）；APScheduler 每日 08/12/18/22 定时调度，日志、统计与告警。

### v1.0.1 ｜ 前端完成（14 个页面 + Mock/Real 双模式）

- **14 个页面**：首页、10 类硬件价格波动页（知识卡片 + 30 天折线图 + 高性价比推荐）、登录/注册、我的账户、管理中心；ECharts 5.5.1 本地化、离线可用；「暗色科技 + 绿色霓虹」设计系统（参考 NVIDIA × 希捷）。
- **Mock/Real 双 API 层**：`assets/js/config.js` 一键切换数据源；演示账号 `demo` 登录自动进入 Mock 演示模式（数据与 `init_data.sql` 完全同源：10 类硬件、58 型号 × 30 天价格、4 档套餐），退出登录自动切回真实后端；`gen_mock_data.py` / `gen_price_pages.py` 支持 Mock 数据与 10 个价格波动页一键再生成。

### v1.0.2 ｜ 爬虫修改补充（数据源切换 + 数据质量加固，2026-11）

- **数据源切换**：京东 / 天猫 / 淘宝真实抓取被反爬全面封死（实测：风控页、SPA 空壳、302 跳转），改用**中关村在线（ZOL）参考报价**——无需登录、无验证码、结构稳定、覆盖全部 10 类硬件；旧三平台 Spider 保留备用（恢复路线见 `爬虫/真实抓取改进建议.md`）。
- **采集口径收紧（2026-11-05 起）**：`real`（默认）只走真实抓取，失败/封禁/零解析一律不降级；`auto` 与 real 行为一致（保留兼容）；`mock` 仅比赛演示与回填使用。
- **价格质量三重校验**：型号页标题回校验 → ±30% 合理性校验（`PLAUSIBILITY`）→ 真实/模拟 `source` 完全隔离；模拟价绝不冒充真实价，采不到如实显示「暂无数据」。
- **工具与监控补充**：`tools/migrate_quality.py`（建列 / 基准性能分 / 清空模拟价）、`probe_zol_*.py` 页面改版探针、`verify_e2e.py` 端到端验证、`test_parsers.py` 解析单测；告警条件（真实成功率 < 50%、连续 3 轮全平台失败、封禁信号）。
- **后端契约同步**：`/api/public/price/series` 只聚合 `source='real'` 真实采集价；未采到的 SKU 自动沿用上一真实价。

### v1.0.3 ｜ 安全漏洞修补（敏感信息外置 + 权限加固）

- **密钥与密码全部外置**：`DB_PASSWORD` / `JWT_SECRET`（≥32 字节随机串）/ `ADMIN_INIT_PASSWORD` / `CORS_ALLOWED_ORIGINS` / `SWAGGER_ENABLED` 均通过环境变量或本地密钥文件注入，仓库不含任何明文密钥；`backend-env.*`、`爬虫/.dbsecret` 全部 gitignore；提供 `爬虫/tools/rotate_db_password.py` 密码轮换脚本。
- **最小权限**：应用改用 `hwapp` 数据库账号（仅 `hw_price` 库增删改查、无 DDL），配套 `爬虫/tools/create_app_db_user.py` 一键创建。
- **接口与额度加固**：JWT + 额度门禁双重校验；先扣减、后调用、失败自动返还（防额度绕过与超扣）；免费级图片问答直接 403（code 40301）、额度用尽 429（code 42901）；AI 网关密钥管理页回显打码；根管理员 Controler 密码由环境变量注入、幂等创建、不随包预置；后端服务管理仅根管理员可见（其余管理员 403）；CORS 白名单与 Swagger 开关支持部署时收紧。

> 各里程碑的模块级细节见：`前端/README.md` · `后端/README.md` · `爬虫/README.md`。

## 安全声明（参赛）

- 数据库密码、JWT 密钥、管理员初始密码、AI API 密钥均不在仓库中出现：数据库与 JWT 走环境变量、AI 密钥由管理员在管理中心页面配置后存库（接口回显打码）；
- 应用连接数据库使用最小权限账号（仅 `hw_price` 库增删改查，无 DDL）；
- 仓库遵循 `.gitignore`：本地密钥文件（`backend-env.*`、`爬虫/.dbsecret`）、日志、构建产物均不入库。
