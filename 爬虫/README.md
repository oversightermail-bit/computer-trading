# 硬件价格比价与智能推荐网站 · 数据采集子系统（Python 爬虫）

依据《硬件比价网站_代码实现功能描述文档》第四章与《网站设计》需求实现的爬虫子模块（F6）：
从 **京东 / 天猫 / 淘宝** 抓取 10 类硬件的多平台价格，清洗标准化后写入 MySQL
`t_price_history` 时序表，由后端聚合为折线图与"推荐购买平台"。

技术栈：**Scrapy（并发调度，可降级直抓）+ requests/urllib（轻量页面）+ lxml/正则（解析）+
pandas（清洗归一）+ PyMySQL（入库）+ APScheduler（定时）**。

---

## 一、目录结构

```
爬虫/
├── run.py                      # 命令行入口：once / backfill / schedule / report / init
├── requirements.txt            # pip install -r requirements.txt
├── README.md
├── logs/                       # 运行日志 / 统计 / 推荐报告 / 告警（运行时生成）
├── tools/
│   ├── verify_e2e.py           # 端到端验证（临时库导入/幂等断言，不动真实库）
│   └── test_parsers.py         # 平台解析与清洗单元测试（合成样本，不走网络）
└── hwspider/
    ├── config.py               # 统一配置中心：数据库/平台/反爬/调度/阈值/商品目录
    ├── items.py                # RawItem 原始条目模型（SKU=品牌|型号|规格）
    ├── loader.py               # 目录加载、关键词生成、标题→目录匹配
    ├── fetcher.py              # 轻量页面抓取（requests，缺省退回 urllib）
    ├── cleaner.py              # pandas 清洗：价格标准化、异常剔除、中位价聚合
    ├── storage.py              # 入库：mysql / sql / jsonl 三种 sink，幂等 upsert
    ├── recommend.py            # 推荐购买平台算法（最低价 + 价差阈值并列）
    ├── mockmarket.py           # 模拟行情数据源（封禁/离线自动降级）
    ├── monitor.py              # 成功率统计、封禁检测、告警（文件 + 可选 webhook）
    ├── engine.py               # 单轮编排：调度→采集→清洗→入库→推荐→监控
    ├── scheduler.py            # 定时调度（APScheduler，缺省降级内置循环）
    ├── settings.py             # Scrapy 设置（限速/重试/中间件/管道）
    ├── middlewares.py          # UA 轮换、代理池、封禁检测中间件
    ├── pipelines.py            # Scrapy 清洗入库管道（复用 engine.ingest）
    └── spiders/                # 每平台一个 Spider（含无 Scrapy 时的直抓函数）
        ├── base.py             # 公共基类与注册表
        ├── jd.py               # 京东：搜索列表 + p.3.cn 价格接口补价
        ├── taobao.py           # 淘宝：内嵌 JSON（g_page_config）解析
        └── tmall.py            # 天猫：CSS 选择器解析
```

## 二、快速开始

```bash
# 1. 安装依赖（Python 3.9+）
pip install -r requirements.txt

# 2. 确认数据库（与后端同一 MySQL，hw_price 库，表已由 后端/sql/schema.sql 创建）
python run.py init

# 3. 回填最近 30 天时序（幂等，已有日期自动跳过）
python run.py backfill --days 30

# 4. 单轮采集（默认 auto：真实抓取，被封禁/失败自动切换模拟行情）
python run.py once

# 5. 启动每日定时调度（08:00 / 12:00 / 18:00 / 22:00）
python run.py schedule
```

> 本机没有 pymysql 时，`once/backfill` 自动降级为 SQL 脚本输出
> （`logs/crawl_sql.sql`），用 `mysql -uroot -p hw_price < logs/crawl_sql.sql`
> 导入效果与直连完全一致。

## 三、采集模式（mode）

| 模式 | 行为 | 适用场景 |
|---|---|---|
| `auto`（默认） | 先真实抓取；检测到**封禁信号 / 零解析 / 网络失败**时，该平台自动切换**模拟行情**，其余平台不受影响 | 日常运行、比赛演示 |
| `real` | 只走真实抓取，失败不降级 | 验证真实反爬策略 |
| `mock` | 直接使用模拟行情（固定种子随机游走，确定可复现） | 无网演示、回填历史 |

模拟行情与后端演示数据同思路（固定种子随机游走、平台价差系数 京东1.00/天猫0.985/淘宝0.97、
小概率促销），同一天多次运行结果完全一致，不会产生自相矛盾的历史数据。

## 四、与后端的契约

- 写入两张表：`t_product`（按 硬件类型+品牌+型号+规格 幂等 upsert，自动复用后端
  init_data.sql 已有的 id 1-45）与 `t_price_history`（商品 × 平台 × 日期一行，
  同日重跑刷新价格，绝不产生重复行）。
- 平台名与后端一致：**京东 / 天猫 / 淘宝**；硬件类型编码与 `t_hardware.type` 一致
  （cpu/gpu/mem_desktop/mem_laptop/ssd/ssd_usb/hdd_usb/monitor/keyboard/mouse）。
- 后端 `/api/public/price/series` 直接聚合 `t_price_history` 出折线 +
  推荐购买平台；爬虫侧 `logs/recommend_YYYY-MM-DD.txt` 输出同口径报告供核对。
- 二手交易（F5）本期不开发，爬虫不涉及 `t_trade`。

## 五、扩展指南（配置化扩展，无需改代码）

1. **新增硬件类目 / 型号**：在 `hwspider/config.py` 的 `CATALOG` 追加
   `{"type": ..., "brand": ..., "model": ..., "spec": ..., "base": ...}`，
   Spider 自动生成该类型的搜索关键词。
2. **新增平台**：新建 `hwspider/spiders/xxx.py`，实现 `search_url / parse_search /
   detect_ban / collect` 四个函数（可仿照 `jd.py`），并在 `spiders/base.py` 的
   `collectors()` 注册；把平台名加入 `config.PLATFORMS` 与 `PLATFORM_FACTOR`。
3. **调反爬**：UA 池 / 代理池 / 限速 / 重试 / 封禁特征词都在 `config.py` 的
   `ANTI_CRAWL` 中。
4. **调调度**：`config.SCHEDULE.times` 修改每日抓取时刻。
5. **推荐阈值**：`config.RECOMMEND.tie_threshold`（价差 ≤ 该值并列推荐）。

## 六、监控与告警

- 每轮统计写入 `logs/crawl_stats.jsonl`（保留最近 30 轮），`python run.py report` 查看；
- 告警条件（任一触发即写 `logs/ALERT_YYYY-MM-DD.txt`，配置 webhook 后同时推送）：
  - 检测到封禁信号（验证码/风险页/强制登录跳转）；
  - 真实抓取成功率低于 50%；
  - 连续 3 轮全平台失败。
- 运行日志：`logs/crawler.log`（控制台同款输出）。

## 七、常见问题

- **`pip install scrapy` 失败（Windows）**：先 `pip install wheel`，或安装
  Visual C++ Build Tools；缺 Scrapy 也能跑（自动用内置直抓引擎，功能等价）。
- **真实抓取全是 0 条**：京东/淘宝/天猫反爬严格，登录墙/验证码属正常现象，
  auto 模式已自动切换模拟行情；如需真实数据，在 `config.ANTI_CRAWL.proxies`
  配置代理池并降低频率。
- **连接数据库失败**：核对 `config.DATABASE` 与后端 `application.yml` 一致
  （默认 root/123456@127.0.0.1:3306/hw_price）。
- **回填后折线没变化**：回填默认跳过已有日期（不覆盖后端演示数据），
  加 `--overwrite` 才会覆盖历史。
