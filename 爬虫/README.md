# 硬件价格比价与智能推荐网站 · 数据采集子系统（Python 爬虫）

依据《硬件比价网站_代码实现功能描述文档》第四章与《网站设计》需求实现的爬虫子模块（F6）：
从 **中关村在线（ZOL）** 抓取 10 类硬件的参考报价，清洗标准化后写入 MySQL
`t_price_history` 时序表，由后端聚合为折线图与"推荐购买平台"。

> **数据源变更（2026-11）**：原定京东 / 天猫 / 淘宝三平台真实抓取在 2026 年已被
> 反爬全面封死（实测：京东风控页、淘宝 SPA 空壳、天猫 302 到淘宝），已改为抓取
> 中关村在线（ZOL）参考报价——无需登录、无验证码、结构稳定，且覆盖全部 10 个
> 硬件类目。旧三平台 Spider（jd/taobao/tmall.py）保留备用；如需恢复多平台真实价，
> 见 `真实抓取改进建议.md` 的京东联盟 API / Playwright 路线。

技术栈：**requests（轻量页面，含限速/重试/UA 轮换）+ lxml（解析）+
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
│   ├── test_parsers.py         # 平台解析与清洗单元测试（合成样本，不走网络）
│   ├── migrate_quality.py      # 一次性迁移（建列 / 基准性能分 / 清空模拟价）
│   ├── probe_zol_*.py          # ZOL 页面改版探针（复测并更新 zol.py 选择器）
│   └── ...                     # 其余为一次性维护 / 探测脚本
└── hwspider/
    ├── config.py               # 统一配置中心：数据库/平台/反爬/调度/阈值/商品目录
    ├── items.py                # RawItem 原始条目模型（SKU=品牌|型号|规格）
    ├── loader.py               # 目录加载、关键词生成、标题→目录匹配
    ├── fetcher.py              # 轻量页面抓取（requests，缺省退回 urllib）
    ├── cleaner.py              # pandas 清洗：价格标准化、异常剔除、中位价聚合
    ├── storage.py              # 入库：mysql / sql / jsonl 三种 sink，幂等 upsert
    ├── recommend.py            # 推荐购买平台算法（最低价 + 价差阈值并列）
    ├── mockmarket.py           # 模拟行情数据源（仅 --mode mock 与 backfill 演示使用，不自动降级）
    ├── monitor.py              # 成功率统计、封禁检测、告警（文件 + 可选 webhook）
    ├── engine.py               # 单轮编排：调度→采集→清洗→入库→推荐→监控
    ├── scheduler.py            # 定时调度（APScheduler，缺省降级内置循环）
    ├── settings.py             # Scrapy 设置（限速/重试/中间件/管道）
    ├── middlewares.py          # UA 轮换、代理池、封禁检测中间件
    ├── pipelines.py            # Scrapy 清洗入库管道（复用 engine.ingest）
    └── spiders/                # 每平台一个 Spider（含无 Scrapy 时的直抓函数）
        ├── base.py             # 公共基类与注册表
        ├── zol.py              # 中关村在线：分类页定位型号 → 详情页取参考报价（当前主源）
        ├── jd.py               # 京东（备用，2026 起需登录 Cookie，见改进建议）
        ├── taobao.py           # 淘宝（备用，页面已 SPA 化，需 mtop 接口或浏览器渲染）
        └── tmall.py            # 天猫（备用，同淘宝）
```

## 二、快速开始

```bash
# 1. 安装依赖（Python 3.9+）
pip install -r requirements.txt

# 2. 确认数据库（与后端同一 MySQL，hw_price 库，表已由 后端/sql/schema.sql 创建）
python run.py init

# 3. 回填最近 30 天时序（幂等，已有日期自动跳过）
python run.py backfill --days 30

# 4. 单轮采集（默认 real：只走真实抓取，失败/封禁不降级，采不到显示"暂无数据"）
python run.py once --mode real

# 5. 启动每日定时调度（08:00 / 12:00 / 18:00 / 22:00）
python run.py schedule
```

> 本机没有 pymysql 时，`once/backfill` 自动降级为 SQL 脚本输出
> （`logs/crawl_sql.sql`），用 `mysql -uroot -p hw_price < logs/crawl_sql.sql`
> 导入效果与直连完全一致。

## 三、采集模式（mode，2026-11-05 起收紧口径）

| 模式 | 行为 | 适用场景 |
|---|---|---|
| `real`（默认） | 只走真实抓取；**失败/封禁/零解析一律不降级**。采不到的 SKU 当日不写库，后端聚合自动"沿用上一真实价"，完全无数据显示"暂无数据" | 日常运行、后端管理页"启动爬虫"按钮 |
| `auto` | 同 `real`（保留兼容，不再自动切换模拟行情） | - |
| `mock` | 直接使用模拟行情（固定种子随机游走，确定可复现），入库 `source='mock'`，后端只聚合 `source='real'`，模拟价绝不会冒充真实价 | 仅比赛演示 / `backfill` 回填 |

**价格质量三重校验（防错配 / 防脏数据）**：
1. 型号页标题回校验：详情页 `<title>` 必须匹配回目录 SKU，不匹配直接丢弃
   （统计字段 `mismatch`）；
2. 合理性校验：与目录基准价偏差超出 **±30%**（`config.PLAUSIBILITY`）视为
   错配/脏数据丢弃，当日不写入 → 后端自然沿用上一真实价；
3. 采不到即"暂无数据"：绝不生成模拟价填充（模拟价仅显式 `--mode mock` 时
   写入，且与真实数据按 `t_price_history.source` 完全隔离）。

每轮结束打印"未采到真实价的 SKU：沿用上一真实价 N ｜ 暂无数据 M"。

模拟行情与后端演示数据同思路（固定种子随机游走、中关村在线系数 0.99、
小概率促销），同一天多次运行结果完全一致，不会产生自相矛盾的历史数据。

## 四、与后端的契约

- 写入两张表：`t_product`（按 硬件类型+品牌+型号+规格 幂等 upsert）与
  `t_price_history`（商品 × 平台 × 日期一行，含 `source` 列：real/mock，
  同日重跑刷新价格，绝不产生重复行）。
- 平台名与后端一致：**中关村在线**；硬件类型编码与 `t_hardware.type` 一致
  （cpu/gpu/mem_desktop/mem_laptop/ssd/ssd_usb/hdd_usb/monitor/keyboard/mouse）。
- 后端 `/api/public/price/series` 只聚合 `source='real'` 的真实采集价出折线 +
  高性价比推荐（性能分由 PassMark/3DMark/官方规格自动映射 1-100，见
  `../../perf_benchmarks.json`；性价比指数 = 性能分 ÷ ln(参考价) × 100）；
  爬虫侧 `logs/recommend_YYYY-MM-DD.txt` 输出当日各型号参考价清单供采集核对。
- 二手交易（F5）本期不开发，爬虫不涉及 `t_trade`。

## 五、扩展指南（配置化扩展，无需改代码）

1. **新增硬件类目 / 型号**：在 `hwspider/config.py` 的 `CATALOG` 追加
   `{"type": ..., "brand": ..., "model": ..., "spec": ..., "base": ...}`；
   ZOL 采集器按类目页标题自动匹配型号页（可选 `"zol_url"` 手动指定型号页）。
2. **新增平台**：新建 `hwspider/spiders/xxx.py`，实现 `search_url / parse_search /
   detect_ban / collect` 四个函数（可仿照 `zol.py`），并在 `spiders/base.py` 的
   `collectors()` 注册；把平台名加入 `config.PLATFORMS` 与 `PLATFORM_FACTOR`。
3. **调 ZOL 采集**：类目页 URL 在 `config.ZOL_CATEGORIES`；限速/重试/UA 池/封禁
   特征词在 `config.ANTI_CRAWL`（ZOL 有防刷限流，`download_delay` 勿低于 2 秒）。
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

- **`pip install scrapy` 失败（Windows）**：Scrapy 可选；ZOL 采集走内置直抓引擎
  （requests + lxml），无需 Scrapy。
- **ZOL 真实抓取全是 0 条**：先查是不是触发了防刷验证（页面跳
  `service.zol.com.cn/checking`）——把 `config.ANTI_CRAWL.download_delay` 调到
  5 秒以上、换网络/代理后再试；若是"解析 0 条"，说明 ZOL 页面改版，用
  `tools/probe_zol_*.py` 探针复测并更新 `zol.py` 的选择器。
- **个别型号没有价格**：ZOL 类目列表里没有该型号、或回校验/合理性校验被拦截时
  该 SKU 当日无数据，属正常（页面显示"暂无数据"，后端沿用上一真实价）；
  可在 `config.CATALOG` 给该条目加 `"zol_url"` 手动指定型号页。
- **连接数据库失败**：核对 `config.DATABASE` 与后端 `application.yml` 一致
  （127.0.0.1:3306/hw_price）；密码不入库——优先读环境变量 `HW_DB_PASSWORD`，
  否则读 `爬虫/.dbsecret`（已 gitignore），首次部署在该文件写入本机 MySQL 密码即可。
- **回填后折线没变化**：`backfill` 写入的是 `source='mock'` 演示数据，
  后端只聚合 `source='real'`，因此回填不会出现在真实页面；要真实历史只能
  靠每日多次真实采集持续积累。首次部署可执行 `tools/migrate_quality.py`
  （建列 / 基准性能分 / 清空模拟价），随后 `python run.py once` 真实采集。
