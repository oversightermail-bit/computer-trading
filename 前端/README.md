# 硬核比价 · 前端（HTML + CSS + JavaScript + ECharts）

硬件价格比价与智能推荐网站的**表现层**。原生 HTML/CSS/JS，无重型框架；图表统一使用本地 ECharts 5.5.1；与 Java 后端、Python 爬虫通过 REST 接口协作，并内置与后端演示数据**完全同源**的 Mock 数据层，双击 HTML 即可完整演示。

## 一、快速开始

**方式 A：双击运行 + 演示账号（比赛演示推荐）**

直接双击 `首页/shouye.html`（或本目录 `index.html`）打开。页面默认连接真实后端（`http://127.0.0.1:8080/api`）；按根目录 README 启动后端后，用演示账号 `demo` / `demo123` 登录，页面自动切换为 Mock 演示模式（数据、图表、登录、订阅、AI 问答全部本地模拟，此后离线也可完整演示）。纯零安装体验可直接访问在线静态演示：<https://oversightermail-bit.github.io/web-display/>。

**方式 B：本地静态服务器**

```bash
cd 前端
python -m http.server 8000      # 或 npx serve / VS Code Live Server（避开后端占用的 8080）
```

访问 `http://localhost:8000/首页/shouye.html`。

> 演示账号：用户名 `demo`，密码 `demo123`（初始为免费版 · 3 次/日 AI 问答，可在账户页任意切换 4 档套餐）。
> 推荐演示闭环：登录 → 账户页查看套餐与额度 → 使用免费额度进行 AI 问答 → 额度用尽自动弹出订阅升级窗 → 订阅升级即时生效 → 继续 AI 问答 → 账户页查看额度消耗明细。

## 二、页面清单（14 页）

| 页面 | 文件 | 说明 |
|---|---|---|
| 首页 | `首页/shouye.html` | 搜索栏、10 类硬件价格波动入口、AI 问答入口、额度徽章、数据来源 |
| 价格波动页 ×10 | 各硬件文件夹 | 功能作用 / 适用场景 / 易踩坑点 + 多型号折线图（图例显隐）+ 高性价比推荐 + 返回首页 |
| 登录 / 注册 | `登录界面/denlu.html` | 游客浏览；登录后解锁 AI 咨询 |
| 我的账户 | `账户/gerenxingxi.html` | 当前订阅、日/月额度进度、套餐订阅、额度消耗明细 |
| 管理中心 | `管理/guanli.html` | 仅管理员：爬虫启动与定时抓取、AI 网关免费/付费分档配置、用户管理；后端服务管理仅根管理员 |

价格波动页与后端 `t_hardware.type` 编码一一对应：

| type | 页面 |
|---|---|
| cpu / gpu | `CPU/cpu.html`、`GPU/gpu.html` |
| mem_desktop / mem_laptop | `台式机内存/neichun pc.html`、`笔记本内存/neichun bookpc.html` |
| ssd / ssd_usb / hdd_usb | `固态硬盘/gutai.html`、`移动便携固态硬盘/yidong gutaiyingpan.html`、`移动便携机械硬盘/yidong jixieyingpan.html` |
| monitor / keyboard / mouse | `显示屏/xianshiping.html`、`键盘/jianpan.html`、`鼠标/shubiao.html` |

> 二手硬件交易（F5）按排期本期不开发，前端不渲染该入口。

## 三、目录结构

```
前端/
├─ index.html                 # 入口（跳转首页）
├─ assets/                    # 共享资源
│  ├─ css/common.css          # 设计系统：暗色科技风（NVIDIA）+ 青绿点缀（希捷）
│  ├─ css/price.css           # 价格波动页样式
│  ├─ js/config.js            # ★ API 模式开关（mock / real）
│  ├─ js/data.js              # Mock 数据（与 后端/sql/init_data.sql 同源，自动生成）
│  ├─ js/api.js               # 双 API 层：MockApi + RealApi 统一封装
│  ├─ js/auth.js              # 登录态（JWT/localStorage）+ 顶栏用户区
│  ├─ js/quota.js             # 额度徽章 + 升级弹窗（42901/40301 引导）
│  ├─ js/chart.js             # ECharts 折线渲染（图例显隐/缩放）
│  ├─ js/ai.js                # AI 助手悬浮按钮 + 问答抽屉（文本/图片）
│  ├─ js/price-page.js        # 10 个价格波动页共用逻辑
│  ├─ js/ui.js                # Toast / Modal / 格式化
│  └─ js/vendor/echarts.min.js # ECharts 5.5.1（本地化，离线可用）
├─ 首页|CPU|GPU|台式机内存|笔记本内存|固态硬盘|移动便携固态硬盘|移动便携机械硬盘|显示屏|键盘|鼠标|登录界面|账户|管理/
│   ├─ *.html                 # 页面
│   ├─ css/ js/               # 页面专属样式与逻辑（硬件页为统一模板生成）
│   └─ images/ pages/         # 预留
```

## 四、Mock / 真实 API 切换（一步切换）

所有页面通过 `assets/js/config.js` 的 `API_MODE` 切换数据源：

```js
window.AppConfig = {
  API_MODE: 'real',                      // 默认 'real'：游客也走真实后端
  API_BASE: 'http://127.0.0.1:8080/api', // 真实后端地址前缀
};
```

- 运行时切换：演示账号 `demo` 登录成功后自动 `setMode('mock')`（本地演示数据，顶栏显示「演示模式」徽章），退出登录自动切回 `'real'`；注册用户始终走真实后端；模式持久化于 localStorage（`hwprice_api_mode`），跨页面保持一致。

- `mock`：`api.js` 内置的 MockApi —— 数据与 `后端/sql/init_data.sql` 完全一致（10 类硬件、58 型号、中关村在线 × 30 天价格、4 档套餐），本地 localStorage 模拟用户/登录/订阅/额度，AI 为本地规则应答（简短大白话）。
- `real`：fetch 调用 Java 后端 REST 接口，自动携带 JWT；HTTP 401 自动跳登录页。切换后前端业务代码**零改动**。

后端接口契约（统一响应 `{code, message, data}`，code=0 成功；42901 额度用尽 → 升级弹窗）：

| 接口 | 权限 | 说明 |
|---|---|---|
| `GET /api/public/hardware` | 游客 | 首页硬件分类列表 |
| `GET /api/public/search?keyword=` | 游客 | 关键词搜索 |
| `GET /api/public/price/series?type=` | 游客 | 折线图数据（多型号 × 30 天 + 推荐平台） |
| `GET /api/public/price/content?type=` | 游客 | 功能/场景/避坑文案 |
| `POST /api/public/register` `POST /api/public/login` | 游客 | 注册 / 登录（JWT） |
| `POST /api/auth/ai/chat` | 登录 | AI 问答（文本 1 次 / 含图 2 次额度） |
| `GET /api/public/subscribe/plans` | 游客 | 套餐列表 |
| `GET /api/auth/quota` `GET /api/auth/quota/logs` | 登录 | 剩余额度 / 消耗明细 |
| `POST /api/auth/subscribe/order` | 登录 | 订阅下单（比赛模式跳过支付直接激活） |
| `GET /api/auth/subscribe/me` | 登录 | 我的订阅（套餐/有效期/等级快照） |

> 完整接口清单（含支付回调与管理接口）见 `后端/README.md`。

## 五、Mock 数据再生成（可选）

`data.js` 由 `后端/sql/init_data.sql` 自动生成，后端数据更新后执行：

```bash
python ../gen_mock_data.py      # 重新生成 assets/js/data.js
python ../gen_price_pages.py    # 重新生成 10 个价格波动页
```

## 六、设计风格说明

参考 NVIDIA 官网（暗色背景、荧光绿 `#76B900` 主色、大标题、网格卡片、霓虹光晕）与希捷官网（清爽排版、青绿 `#19B7A8` 点缀、专业克制），形成「暗色科技 + 绿色霓虹 + 青绿数据色」的统一设计语言；主题色与卡片/按钮/图表配色全部收敛在 `assets/css/common.css` 的 CSS 变量中。
