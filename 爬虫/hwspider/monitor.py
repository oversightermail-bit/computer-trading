# -*- coding: utf-8 -*-
"""抓取监控与告警（文档 §四(二)）。

记录每轮各平台的抓取成功率、异常页与封禁信号；满足任一条件即告警：
  - 检测到封禁信号（验证码/风险页/强制登录跳转）；
  - 真实抓取成功率低于 MONITOR.alert_success_rate；
  - 连续失败达到 MONITOR.alert_consecutive_fail 次。
告警落盘 logs/ALERT_YYYY-MM-DD.txt（追加），配置了 webhook_url 时同时推送。
统计历史写入 logs/crawl_stats.jsonl，供 `run.py report` 查询。
"""
import json
import logging
import urllib.request
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

from . import config

log = logging.getLogger("hwspider.monitor")


class PlatformStats:
    """单平台单轮统计"""

    def __init__(self, platform: str):
        self.platform = platform
        self.source = "real"          # real / mock
        self.requested = 0            # 发起的抓取请求数
        self.parsed = 0               # 成功解析出的原始条目数
        self.failed = 0               # 失败请求数
        self.banned = False           # 是否检测到封禁信号
        self.switched_to_mock = False # 是否自动切换模拟行情
        self.error = ""               # 异常信息

    @property
    def success_rate(self) -> float:
        if self.requested <= 0:
            return 0.0
        return self.parsed / self.requested

    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "source": self.source,
            "requested": self.requested,
            "parsed": self.parsed,
            "failed": self.failed,
            "success_rate": round(self.success_rate, 3),
            "banned": self.banned,
            "switched_to_mock": self.switched_to_mock,
            "error": self.error,
        }


def save_run(round_id: str, stats: List[PlatformStats],
             written: int = 0, products: int = 0, mode: str = "auto") -> None:
    """追加一轮统计到 logs/crawl_stats.jsonl（保留最近 N 轮）。

    日志目录不可写（如受限沙箱）时仅告警到日志器，不阻断采集主流程。
    """
    record = {
        "round_id": round_id,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mode": mode,
        "platforms": [s.to_dict() for s in stats],
        "prices_written": written,
        "products_upserted": products,
    }
    try:
        config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        path = config.REPORT_DIR / "crawl_stats.jsonl"
        with open(str(path), "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        _trim(path)
    except OSError as e:
        log.warning("统计落盘失败（本轮仅控制台展示）：%s", e)


def _trim(path: Path) -> None:
    keep = config.MONITOR["keep_stats_runs"]
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) > keep:
        path.write_text("\n".join(lines[-keep:]) + "\n", encoding="utf-8")


def check_alerts(stats: List[PlatformStats], previous_failures: int = 0) -> List[str]:
    """按阈值判定告警，返回告警文案列表（空 = 无告警）。"""
    alerts: List[str] = []
    for s in stats:
        if s.banned:
            alerts.append("[%s] 检测到封禁信号（验证码/风险页/强制登录），本轮已自动切换策略" % s.platform)
        elif s.switched_to_mock:
            alerts.append("[%s] 真实抓取失败，已降级为模拟行情（source=mock）" % s.platform)
        if s.source == "real" and s.requested > 0 and s.success_rate < config.MONITOR["alert_success_rate"]:
            alerts.append("[%s] 抓取成功率 %.0f%% 低于阈值 %.0f%%" %
                          (s.platform, s.success_rate * 100,
                           config.MONITOR["alert_success_rate"] * 100))
    if previous_failures >= config.MONITOR["alert_consecutive_fail"]:
        alerts.append("连续 %d 轮抓取失败，请检查网络/代理池/反爬策略" % previous_failures)
    return alerts


def fire_alerts(alerts: List[str], round_id: str) -> Optional[Path]:
    """落盘告警文件 + 可选 webhook 推送，返回告警文件路径（无告警返回 None）。"""
    if not alerts:
        return None
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = config.REPORT_DIR / ("ALERT_%s.txt" % date.today().isoformat())
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    block = "\n".join(["--- %s 轮次 %s ---" % (stamp, round_id)] + alerts)
    try:
        with open(str(path), "a", encoding="utf-8") as f:
            f.write(block + "\n")
    except OSError as e:
        log.warning("告警文件写入失败（不影响采集）：%s", e)
    log.warning("触发告警：\n%s", block)

    webhook = config.MONITOR.get("webhook_url", "")
    if webhook:
        try:
            payload = json.dumps({
                "msgtype": "text",
                "text": {"content": "【价格爬虫告警】\n" + block},
            }, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(webhook, data=payload,
                                         headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=5).read()
        except Exception as e:  # webhook 失败不影响主流程
            log.debug("webhook 推送失败：%s", e)
    return path


def read_recent_stats(limit: int = 10) -> List[dict]:
    """读取最近 N 轮统计（report 命令用）。"""
    path = config.REPORT_DIR / "crawl_stats.jsonl"
    if not path.exists():
        return []
    out: List[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out[-limit:]


def consecutive_failures(stats: List[dict]) -> int:
    """统计最近连续"真实抓取全失败"的轮数（主动 mock/回填轮次不计入）。"""
    n = 0
    for rec in reversed(stats):
        if rec.get("mode") == "mock":
            break  # 主动模拟/回填轮次：不算失败，也不延续之前的失败计数
        plats = rec.get("platforms", [])
        if not plats:
            break
        if all(p.get("source") == "mock" or p.get("parsed", 0) == 0 for p in plats):
            n += 1
        else:
            break
    return n
