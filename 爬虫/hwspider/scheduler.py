# -*- coding: utf-8 -*-
"""定时调度器（文档 §四(二) 调度器：每日多次，保证价格时序连续）。

优先 APScheduler（Cron 定时）；未安装时退化为内置线程循环，
按 config.SCHEDULE.times 计算下一次运行时间，功能等价。
"""
import logging
import threading
import time as _time
from datetime import datetime, timedelta

from . import config

log = logging.getLogger("hwspider.scheduler")

try:
    from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
    from apscheduler.triggers.cron import CronTrigger  # type: ignore
    HAS_APSCHEDULER = True
except ImportError:  # pragma: no cover
    HAS_APSCHEDULER = False


def _hour_minute(time_str: str):
    h, m = time_str.split(":")
    return int(h), int(m)


def start(job, times=None, run_immediately: bool = True) -> object:
    """启动调度，返回调度器对象（阻塞由调用方控制）。"""
    times = times or config.SCHEDULE["times"]
    if HAS_APSCHEDULER:
        sched = BackgroundScheduler(timezone=config.SCHEDULE["timezone"])
        for t in times:
            h, m = _hour_minute(t)
            sched.add_job(job, CronTrigger(hour=h, minute=m, timezone=config.SCHEDULE["timezone"]),
                          id="crawl_%s" % t, replace_existing=True)
        sched.start()
        if run_immediately:
            job()
        return sched

    # 无 APScheduler：内置循环线程，每小时对一次表
    stop = threading.Event()
    if run_immediately:
        job()

    def loop():
        while not stop.is_set():
            nxt = _next_run(datetime.now(), times)
            stop.wait((nxt - datetime.now()).total_seconds() + 1)
            if not stop.is_set() and datetime.now() >= nxt:
                job()

    threading.Thread(target=loop, daemon=True, name="hw-crawl-scheduler").start()
    return stop


def _next_run(now: datetime, times) -> datetime:
    """计算下一个触发时刻。"""
    today = now.date()
    for t in times:
        h, m = _hour_minute(t)
        at = datetime(today.year, today.month, today.day, h, m)
        if at > now:
            return at
    first = sorted(times)[0]
    h, m = _hour_minute(first)
    tomorrow = today + timedelta(days=1)
    return datetime(tomorrow.year, tomorrow.month, tomorrow.day, h, m)


def stop(sched) -> None:
    """停止调度（兼容 APScheduler 与内置 Event）。"""
    try:
        if hasattr(sched, "shutdown"):
            sched.shutdown(wait=False)
        elif hasattr(sched, "set"):
            sched.set()
    except Exception:
        pass
