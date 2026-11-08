# 硬件价格比价与智能推荐网站 · 后端服务

依据《硬件比价网站_代码实现功能描述文档》《网站设计》《订阅模块本地开发实现指南》实现的 Java 后端。

技术栈：**Spring Boot 3.5 + Spring Security(JWT) + MyBatis-Plus(MySQL) + Redis(可降级)**，AI 能力通过统一网关封装（支持本地 Mock 与 OpenAI 兼容接口）。

---

## 一、目录结构

```
后端/
├── pom.xml                          # Maven 工程（Spring Boot 3.5.16 / Java 17+）
├── README.md
├── sql/
│   ├── schema.sql                   # 10 张基础表（含二手交易预留表 t_trade；t_pay_order 见 subscription_schema.sql）
│   ├── init_data.sql                # 演示数据：4 套餐 + 10 硬件类目 + 58 型号 + 中关村在线 × 30 天价格时序
│   └── subscription_schema.sql      # 订阅模块脚本（4 表 + 4 套餐，幂等，补齐 t_pay_order 支付单表）
├── tools/
│   ├── gen_sample_data.py           # init_data.sql 生成器（价格随机游走、日期相对今天）
│   └── smoke_test.ps1               # 一键冒烟测试（自动构建 → 启动 → 15+ 接口断言 → 关闭）
└── src/main/
    ├── java/com/hwprice/
    │   ├── HwPriceApplication.java  # 启动类
    │   ├── common/                  # 统一响应体 Result{code,message,data}、错误码、全局异常
    │   ├── config/                  # Security/JWT、MyBatis-Plus、CORS、OpenAPI、异步、AppProperties
    │   ├── security/                # JwtUtil、JwtAuthFilter、LoginUser、BodyCacheFilter
    │   ├── entity/ + mapper/        # 11 张表实体与 Mapper
    │   ├── dto/ + vo/               # 入参出参隔离
    │   ├── quota/                   # 额度核心：QuotaInterceptor、RedisQuotaStore(Lua)、DbQuotaStore(降级)
    │   ├── ai/                      # LlmClient 网关：MockLlmClient / OpenAiCompatLlmClient / ConfigLlmClient（运行时路由）
    │   ├── pay/                     # 支付通道：PaymentChannel 接口 + Mock / Alipay / Wechat 三通道实现
    │   ├── service/                 # User/Price/Plan/Subscription/Quota/Ai/Crawler/Backend/Payment/AiConfig 十大业务服务
    │   ├── controller/              # Auth/Price/Ai/Subscription/Quota/Admin 六个控制器
    │   └── task/                    # 订阅到期回落免费级定时任务
    └── resources/
        ├── application.yml          # 主配置（数据库账号密码在这里改）
        ├── application-subscription.yml  # 订阅模块专属配置（额度存储、跳过支付开关）
        └── lua/                     # 额度日/月原子扣减与返还脚本
```

## 二、快速启动（本地 MySQL）

环境要求：JDK 17+、Maven 3.8+、本地 MySQL 8（Redis 可选，没有会自动降级为数据库计数器）。

```bash
# 1. 建库建表（10 张基础表）
mysql -u root -p < sql/schema.sql

# 2. 补齐订阅/支付表（t_pay_order 支付单表等，幂等）
mysql -u root -p hw_price < sql/subscription_schema.sql

# 3. 导入演示数据（4 套餐 + 10 类目 + 58 型号 + 近 30 天中关村在线价格）
mysql -u root -p hw_price < sql/init_data.sql

# 4. 配置环境变量：复制项目根目录 backend-env.example.bat → backend-env.bat
#    （Linux 用 backend-env.example.sh），填写 DB_PASSWORD / JWT_SECRET / ADMIN_INIT_PASSWORD

# 5. 启动（任选其一）
mvn spring-boot:run                        # IDEA 直接运行 HwPriceApplication 亦可
java -jar target/hw-price-backend-1.0.0.jar   # 已构建产物（无需 Maven）
start-backend.bat                          # 项目根目录一键脚本（Windows，自动找 Java 与 jar）
```

启动后：
- Swagger 接口文档：<http://localhost:8080/swagger-ui/index.html>
- 健康检查：`GET http://localhost:8080/api/public/hardware` 应返回 10 个硬件类目。

> 只做订阅模块演示时，也可以只执行 `mysql -u root -p < sql/subscription_schema.sql`（4 表 + 4 套餐，含 t_pay_order）。
> 重新生成演示数据：`python tools/gen_sample_data.py`（日期用 CURDATE() 相对表达式，任何时候导入都是"最近 30 天"）。

## 三、接口清单

| 接口 | 方法 | 权限 | 说明 |
|---|---|---|---|
| /api/public/register | POST | 游客 | 注册（默认免费级） |
| /api/public/login | POST | 游客 | 登录，返回 JWT + 套餐 + 剩余额度 |
| /api/public/hardware | GET | 游客 | 首页硬件分类列表 |
| /api/public/search?keyword= | GET | 游客 | 搜索商品/型号/硬件类目 |
| /api/public/price/series?type=gpu | GET | 游客 | 价格时序（ECharts 折线数据源 + 高性价比推荐） |
| /api/public/price/content?type=gpu | GET | 游客 | 硬件文案（功能/场景/避坑） |
| /api/public/subscribe/plans | GET | 游客 | 4 个订阅套餐与额度权益 |
| /api/auth/ai/chat | POST | 登录 | AI 问答（文本计 1 次，图片计 2 次） |
| /api/auth/subscribe/order | POST | 登录 | 订阅下单（比赛模式跳过支付直接激活） |
| /api/auth/subscribe/me | GET | 登录 | 我的订阅（套餐/有效期/等级快照） |
| /api/auth/quota | GET | 登录 | 当前套餐与剩余额度（日/月） |
| /api/auth/quota/logs | GET | 登录 | 额度消耗明细（分页） |
| /api/auth/subscribe/pay/mock/confirm | POST | 登录 | 模拟支付确认（仅 demo/根管理员，激活套餐） |
| /api/public/subscribe/pay/notify | POST | 游客 | 支付异步回调（真实渠道预留，验签后激活） |
| /api/auth/admin/crawler/start · /status | POST/GET | ADMIN | 启动爬虫（后台子进程）/ 最近一轮抓取统计 |
| /api/auth/admin/crawler/schedule/start · /stop | POST | ADMIN | 开启 / 停止定时抓取（每日 08/12/18/22 点） |
| /api/auth/admin/ai-config | GET/POST | ADMIN | AI 网关免费/付费分档配置（密钥打码） |
| /api/auth/admin/users | GET/PUT/DELETE | ADMIN | 用户列表 / 改角色改密码 / 删除 |
| /api/auth/admin/backend/status · /restart | GET/POST | 根管理员 | 后端服务状态（PID/运行时长/Java 版本）/ 一键重启 |

响应体统一为 `{code, message, data}`（与前端 Mock 层契约一致）；`code=0` 成功，
`42901` 表示 AI 额度用尽（HTTP 429，前端据此弹订阅升级窗），HTTP 401 表示未登录。

> 二手交易接口 `/api/auth/trade` 本期按文档要求暂不开发，仅预留 `t_trade` 表与 `Trade` 实体/Mapper。

## 四、订阅与额度体系（F7）

- **四级套餐**（2026-11-06 调整后）：免费版 3 次/日 · 15 次/月（仅文本）｜基础版 9.9 元 100 次/月｜专业版 29.9 元 300 次/月｜旗舰版 69.9 元 600 次/月；付费方案只限每月次数、每日不限（quota_day=0）。名称/定价/额度/多模态开关全部存于 `t_subscription_plan`，改库即时生效、无需发版。
- **双重门禁**：`/api/auth/ai/**` 先过 JWT 认证，再由 `QuotaInterceptor` 按等级原子扣减（纯文本 1 次、含图片 2 次；免费级图片问答直接 403）。
- **先扣减、后调用、失败返还**：调用大模型前置扣减，超时/失败自动返还并记负流水。
- **计数器**：
  - 默认 `auto`：优先 Redis（Lua 保证"判断+扣减"原子性，key=`quota:{userId}:{planId}:day|month:{yyyyMMdd|yyyyMM}`，TTL 到日/月末自动过期清零，**无需定时重置任务**）；
  - Redis 连不上自动降级为 `t_user_subscription.day_used/month_used` 数据库计数器（单条条件 UPDATE 同样原子，跨日/跨月自动清零），比赛环境没有 Redis 也能完整演示。
  - 配置 `app.quota.store=auto|redis|db`。
- **流水对账**：每次消耗/返还异步写入 `t_ai_quota_log`（`quota_type=AI_CHAT/AI_REFUND`），可展示明细、可凭流水重建计数器。
- **到期回落**：定时任务（默认每小时）把过期的付费订阅置为失效，自动回落免费级；额度不足返回 `429 + code 42901`，响应体带当前等级、已用量与可升级套餐列表。

## 五、AI 问答（F4）

- 系统提示词强制"简短的大白话"，并注入网站近 3 日各硬件最低价 TOP3（含平台），回答经压缩（默认 500 字内）。
- 大模型网关运行时路由（`ConfigLlmClient`，2026-11 起）：
  - 管理员在「管理中心 → AI 对话端 API 接入」按**免费/付费两档**分别配置密钥、接口地址与模型名（`ai.free.*` / `ai.paid.*`，**均无默认值**，任意 OpenAI 兼容网关如 DeepSeek/通义/Kimi），保存后即时生效、无需重启；路由按用户套餐判定（非免费套餐走付费档）；
  - 某档未配置密钥仅该档回落本地 Mock 演示模型（零配置可跑：预算解析、场景推荐、型号对比，全部使用数据库真实价格）；
  - 云端走 OpenAI 兼容协议，图片自动转多模态 messages 格式。
- 纯文本计 1 次、图片计 2 次；调用失败返还额度并返回业务码 `50201`。

## 六、数据库设计（11 张表）

`t_user` 用户 ｜ `t_hardware` 硬件类目与文案 ｜ `t_product` 商品主数据（含 `perf_score/perf_basis/perf_updated` 基准性能分）｜ `t_price_history` 价格时序（含 `source` 列：real=真实采集 mock=模拟演示）｜ `t_trade` 二手交易（预留）｜ `t_ai_session` AI 会话 ｜ `t_subscription_plan` 套餐配置 ｜ `t_user_subscription` 用户订阅 ｜ `t_ai_quota_log` 额度流水 ｜ `t_app_config` 应用配置（AI 密钥等）｜ `t_pay_order` 订阅支付单（mock/alipay/wechat 三通道）。

价格时序由 Python 爬虫子系统（`../爬虫`）持续写入；后端只聚合 `source='real'` 的真实采集价（模拟演示数据绝不冒充真实价，采不到显示"暂无数据"）。**高性价比推荐** = 性能分（基准自动映射 1-100：PassMark CPU Mark / 3DMark Time Spy / 官方规格，依据与日期记录在 `perf_basis/perf_updated`）÷ ln(参考价) × 100 得出性价比指数（对数归一化，抑制"越便宜分越高"偏差），前端按指数降序展示并标注"高性价比之选"。

## 七、前端从 Mock 切换到真实后端

前端已支持运行时切换（`assets/js/config.js` 的 `AppConfig.setMode`）：

1. 默认 `API_MODE='real'`：全部用户（含游客）走真实后端，`API_BASE` 默认 `http://127.0.0.1:8080/api`（后端已全放行 CORS）；
2. 内置演示账号 `demo`（后端同样存在，登录校验一致）登录成功后自动切换 `mock` 模式（本地演示数据），顶栏显示"演示模式"徽章；退出登录自动切回 `real`；
3. 注册用户一律走真实后端，不进入 mock 模式；演示账号不在任何页面展示；
4. 内置管理员 `Controler` 不随包预置、密码不入仓库：由环境变量 `ADMIN_INIT_PASSWORD` 注入（部署时在 `backend-env` 模板中自行填写），启动时幂等创建，顶栏出现"管理"入口：启动爬虫、AI 网关分档配置、用户删改。

## 八、配置速查（application.yml / application-subscription.yml）

| 配置 | 默认 | 说明 |
|---|---|---|
| spring.datasource.username/password | `${DB_USER:root}` / 环境变量 `DB_PASSWORD` | 部署建议用最小权限账号 hwapp（仅 hw_price 库增删改查）；从 `backend-env.example` 模板复制 `backend-env.bat` 注入（gitignore） |
| app.jwt.secret | 环境变量 `JWT_SECRET` | 不入库：从 `backend-env.example` 模板复制 `backend-env.bat` 注入（>= 32 字节随机串） |
| app.security.admin-init-password | 环境变量 `ADMIN_INIT_PASSWORD` | 根管理员初始密码（部署时自行填写），为空则跳过初始化 |
| app.security.cors-allowed-origins | 环境变量 `CORS_ALLOWED_ORIGINS`（逗号分隔） | 空 = 开发期全放行；部署时按白名单收紧 |
| SWAGGER_ENABLED | true | 部署时设 false 关闭 Swagger/OpenAPI 文档 |
| app.ai.compress-max-chars / timeout-seconds | 500 / 30 | 回答压缩长度与调用超时 |
| app.crawler.work-dir | ../爬虫 | 管理页"启动爬虫"的工作目录 |
| app.crawler.command | python run.py once --mode real | 启动爬虫命令（只写真实采集价） |
| app.crawler.schedule-command | python run.py schedule --mode real | 定时抓取命令（每日 08/12/18/22 点，常驻调度） |
| app.quota.store | auto | auto / redis / db（额度计数器存储） |
| app.subscribe.skip-payment | true | 比赛模式跳过支付；接支付后改 false |
| app.subscribe.payment.channel | mock | 支付通道：mock / alipay / wechat（营业执照办理后切换真实渠道） |
| app.subscribe.expire-check-cron | 每小时 | 到期回落免费级任务频率 |

## 九、后端启动 / 重启脚本（Windows 与 Linux 服务器通用）

项目根目录提供四个脚本（ASCII 文件名，Windows 双击 `.bat`，Linux 先 `chmod +x` 再 `./xxx.sh`）：

| 脚本 | 用途 |
|---|---|
| `start-backend.bat` / `start-backend.sh` | 启动后端服务（自动定位 jar、自动找 Java：IDEA JBR → JAVA_HOME → PATH；端口占用检测；日志 `backend-runtime.log` / `后端/target/app.log`，Linux 另写 `app.pid`） |
| `restart-backend.bat` / `restart-backend.sh` | 结束旧进程并重启（管理中心"重启后端服务"按钮调用，Windows/Linux 自动选择对应脚本） |

管理中心"后端服务"卡片**仅根管理员 Controler 可见**（其余管理员 403），提供状态（PID/启动时间/运行时长/Java 版本）与"重启后端服务"按钮。后端未运行时管理页无法访问，此时直接运行启动脚本即可。

服务器部署注意：安装 JDK 17+（或设置 `JAVA_HOME`）；8080 端口按需放行/反向代理；`app.jwt.secret` 必须更换为随机长字符串。

## 十、验证示例

一键冒烟测试（自动构建 → 启动 → 15+ 个接口断言 → 关闭）：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\smoke_test.ps1
```

```bash
# 注册
curl -X POST http://localhost:8080/api/public/register -H "Content-Type: application/json" -d "{\"username\":\"demo\",\"password\":\"123456\"}"
# 登录拿 token
curl -X POST http://localhost:8080/api/public/login -H "Content-Type: application/json" -d "{\"username\":\"demo\",\"password\":\"123456\"}"
# 查额度（免费版 3 次/日）
curl http://localhost:8080/api/auth/quota -H "Authorization: Bearer <token>"
# AI 问答（连问 4 次，第 4 次返回 429 + code 42901）
curl -X POST http://localhost:8080/api/auth/ai/chat -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d "{\"content\":\"预算5000打游戏怎么配\"}"
# 升级套餐（比赛模式直接激活）
curl -X POST http://localhost:8080/api/auth/subscribe/order -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d "{\"planId\":3}"
```

## 十一、常见问题

- **启动报数据库连接失败**：确认 MySQL 服务已启动、密码正确、已执行 schema.sql；
- **没有 Redis 会怎样**：额度自动降级为数据库计数器，价格缓存自动直查数据库，功能不受影响；
- **429 是设计行为**：免费版每日 3 次用尽即返回 429 + code 42901，前端应弹升级弹窗而非报错；
- **额度如何重置**：Redis 方案按 key 的 TTL 到日/月末自动过期；数据库方案按 day_key/month_key 归属自动清零；也可调用 `QuotaService.resetDailyQuota/resetMonthlyQuota` 手动重置；
- **构建环境**：JDK 17+ 均可编译运行；本机验证使用 IntelliJ IDEA 自带 Maven（`C:\Program Files\JetBrains\IntelliJ IDEA 2025.3.3\plugins\maven\lib\maven3`）。
