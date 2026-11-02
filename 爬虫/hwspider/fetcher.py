# -*- coding: utf-8 -*-
"""轻量页面抓取（文档 §四(二)：requests 处理轻量页面）。

优先使用 requests（带超时/重试/UA 轮换）；未安装时退回标准库 urllib，
保证任何环境都能发起真实请求（是否成功取决于目标站反爬）。
"""
import random
from typing import Tuple

from . import config

try:
    import requests  # type: ignore
    HAS_REQUESTS = True
except ImportError:  # pragma: no cover
    HAS_REQUESTS = False


def random_ua() -> str:
    return random.choice(config.ANTI_CRAWL["user_agents"])


def fetch(url: str, timeout: int = None) -> Tuple[str, str, str]:
    """抓取页面，返回 (html, final_url, error)；error 非空表示失败。

    final_url 用于检测"强制登录跳转"类封禁信号。
    """
    timeout = timeout or config.ANTI_CRAWL["timeout"]
    headers = {
        "User-Agent": random_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    if HAS_REQUESTS:
        try:
            r = requests.get(url, headers=headers, timeout=timeout,
                             allow_redirects=True)
            return r.text, r.url, ""
        except Exception as e:
            return "", url, str(e)
    # urllib 兜底（标准库，无 requests 时使用）
    import urllib.error
    import urllib.request
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            charset = resp.headers.get_content_charset() or "utf-8"
            return body.decode(charset, errors="replace"), resp.geturl(), ""
    except Exception as e:
        return "", url, str(e)
