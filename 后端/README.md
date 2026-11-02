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
│   ├── schema.sql                   # 全部 9 张表（含二手交易预留表 t_trade）
│   ├── init_data.sql                # 演示数据：4 套餐 + 10 硬件类目 + 45 型号 + 3 平台 × 30 天价格时序
│   └── subscription_schema.sql      # 订阅模块独立脚本（3 表 + 4 套餐，可单独执行）
├── tools/
│   └── gen_sample_data.py           # init_data.sql 生成器（价格随机游走、日期相对今天）
└── src/main/
    ├── java/com/hwprice/
    │   ├── HwPriceApplication.java  # 启动类
    │   ├── common/                  # 统一响应体 Result{code,message,data}、错误码、全局异常
    │   ├── config/                  # Security/JWT、MyBatis-Plus、CORS、OpenAPI、异步、AppProperties
    │   ├── security/                # JwtUtil、JwtAuthFilter、LoginUser、BodyCacheFilter
    │   ├── entity/ + mapper/        # 9 张表实体与 Mapper
    │   ├── dto/ + vo/               # 入参出参隔离
    │   ├── quota/                   # 额度核心：QuotaInterceptor、RedisQuotaStore(Lua)、DbQuotaStore(降级)
    │   ├── ai/                      # LlmClient 网关：MockLlmClient / OpenAiCompatLlmClient
    │   ├── service/                 # User/Price/Plan/Subscription/Quota/Ai 六大业务服务
    │   ├── controller/              # Auth/Price/Ai/Subscription/Quota 五个控制器
    │   └── task/                    # 订阅到期回落免费级定时任务
    └── resources/
        ├── application.yml          # 主配置（数据库账号密码在这里改）
        ├── application-subscription.yml  # 订阅模块专属配置（额度存储、跳过支付开关）
        └── lua/                     # 额度日/月原子扣减与返还脚本
```

## 二、快速启动（本地 MySQL）

环境要求：JDK 17+、Maven 3.8+、本地 MySQL 8（Redis 可选，没有会自动降级为数据库计数器）。

```bash
# 1. 建库建表
mysql -u root -p < sql/schema.sql

# 2. 导入演示数据（4 套餐 + 硬件 + 近 30 天三平台价格）
mysql -u root -p hw_price < sql/init_data.sql

# 3. 改数据库密码：src/main/resources/application.yml 里 spring.datasource.password

# 4. 启动（IDEA 直接运行 HwPriceApplication 亦可）
mvn spring-boot:run
```

启动后：
- Swagger 接口文档：<http://localhost:8080/swagger-ui/index.html>
- 健康检查：`GET http://localhost:8080/api/public/hardware` 应返回 10 个硬件类目。

> 只做订阅模块演示时，也可以只执行 `mysql -u root -p < sql/subscription_schema.sql`（3 表 + 4 套餐）。
> 重新生成演示数据：`python tools/gen_sample_data.py`（日期用 CURDATE() 相对表达式，任何时候导入都是"最近 30 天"）。

## 三、接口清单（与文档 §五(四) 一致）

| 接口 | 方法 | 权限 | 说明 |
|---|---|---|---|
| /api/public/register | POST | 游客 | 注册（默认免费级） |
| /api/public/login | POST | 游客 | 登录，返回 JWT + 套餐 + 剩余额度 |
| /api/public/hardware | GET | 游客 | 首页硬件分类列表 |
| /api/public/search?keyword= | GET | 游客 | 搜索商品/型号/硬件类目 |
| /api/public/price/series?type=gpu | GET | 游客 | 价格时序（ECharts 折线数据源 + 推荐购买平台） |
| /api/public/price/content?type=gpu | GET | 游客 | 硬件文案（功能/场景/避坑） |
| /api/public/subscribe/plans | GET | 游客 | 4 个订阅套餐与额度权益 |
| /api/auth/ai/chat | POST | 登录 | AI 问答（文本计 1 次，图片计 2 次） |
| /api/auth/subscribe/order | POST | 登录 | 订阅下单（比赛模式跳过支付直接激活） |
| /api/auth/subscribe/me | GET | 登录 | 我的订阅（套餐/有效期/等级快照） |
| /api/auth/quota | GET | 登录 | 当前套餐与剩余额度（日/月） |
| /api/auth/quota/logs | GET | 登录 | 额度消耗明细（分页） |

响应体统一为 `{code, message, data}`（与前端 Mock 层契约一致）；`code=0` 成功，
`42901` 表示 AI 额度用尽（HTTP 429，前端据此弹订阅升级窗），HTTP 401 表示未登录。

> 二手交易接口 `/api/auth/trade` 本期按文档要求暂不开发，仅预留 `t_trade` 表与 `Trade` 实体/Mapper。

## 四、订阅与额度体系（F7）

- **四级套餐**：免费版 3 次/日（仅文本）｜基础版 9.9 元 20/日 400/月｜专业版 29.9 元 80/日 1500/月｜旗舰版 69.9 元 200/日 4000/月。名称/定价/额度/多模态开关全部存于 `t_subscription_plan`，改库即时生效、无需发版。
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
- `app.ai.provider` 两种实现：
  - `mock`（默认，零配置可跑）：本地规则引擎，支持预算解析（"预算6000打游戏"）、办公/游戏/生产力场景、硬件关键词对比（"RTX 4060 和 6750XT 对比"），全部使用数据库真实价格；
  - `openai`：OpenAI 兼容协议（OpenAI/DeepSeek/通义等均可），配置 `app.ai.openai.base-url/api-key/model`；图片自动转多模态 messages 格式。
- 纯文本计 1 次、图片计 2 次；调用失败返还额度并返回业务码 `50201`。

## 六、数据库设计（9 张表）

`t_user` 用户 ｜ `t_hardware` 硬件类目与文案 ｜ `t_product` 商品主数据 ｜ `t_price_history` 价格时序（爬虫写、后端读）｜ `t_trade` 二手交易（预留）｜ `t_ai_session` AI 会话 ｜ `t_subscription_plan` 套餐配置 ｜ `t_user_subscription` 用户订阅（含等级快照与数据库额度计数器）｜ `t_ai_quota_log` 额度流水。

价格时序由 Python 爬虫子系统（`../爬虫`）持续写入；后端只负责聚合。折线图按"型号 × 日期"取多平台**中位价**，推荐购买平台 = 当日最低价平台（附次低价与差额）。

## 七、前端从 Mock 切换到真实后端

前端目前是空白占位页，后续按《订阅模块本地开发实现指南》开发时，切换只需 4 步：

1. HTML 里把 `<script src="subscription-mock-api.js">` 换成 `subscription-service.js`；
2. `subscription-service.js` 中 `API_BASE` 改为 `http://localhost:8080/api`（部署时改为正式域名）；
3. 确认响应格式：后端已是 `{code, message, data}`，与 Mock 一致，无需改动业务代码；
4. 登录后把 JWT 放入 `Authorization: Bearer <token>`，401 自动跳登录页，`code === 42901` 弹升级窗（后端已按此契约实现）。

## 八、配置速查（application.yml / application-subscription.yml）

| 配置 | 默认 | 说明 |
|---|---|---|
| spring.datasource.username/password | root/123456 | **改成你本机 MySQL 账号** |
| app.jwt.secret | dev 默认值 | 生产必须换 >= 32 字节随机串 |
| app.ai.provider | mock | mock / openai |
| app.ai.openai.* | - | provider=openai 时填写 base-url/api-key/model |
| app.quota.store | auto | auto / redis / db（额度计数器存储） |
| app.subscribe.skip-payment | true | 比赛模式跳过支付；接支付后改 false |
| app.subscribe.expire-check-cron | 每小时 | 到期回落免费级任务频率 |

## 九、验证示例

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

## 十、常见问题

- **启动报数据库连接失败**：确认 MySQL 服务已启动、密码正确、已执行 schema.sql；
- **没有 Redis 会怎样**：额度自动降级为数据库计数器，价格缓存自动直查数据库，功能不受影响；
- **429 是设计行为**：免费版每日 3 次用尽即返回 429 + code 42901，前端应弹升级弹窗而非报错；
- **额度如何重置**：Redis 方案按 key 的 TTL 到日/月末自动过期；数据库方案按 day_key/month_key 归属自动清零；也可调用 `QuotaService.resetDailyQuota/resetMonthlyQuota` 手动重置；
- **构建环境**：JDK 17+ 均可编译运行；本机验证使用 IntelliJ IDEA 自带 Maven（`C:\Program Files\JetBrains\IntelliJ IDEA 2025.3.3\plugins\maven\lib\maven3`）。
