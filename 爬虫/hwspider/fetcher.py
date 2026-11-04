# -*- coding: utf-8 -*-
"""轻量页面抓取（文档 §四(二)：requests 处理轻量页面）。

优先使用 requests（带超时/重试/UA 轮换/Referer/Cookie）；未安装时退回标准库
urllib，保证任何环境都能发起真实请求（是否成功取决于目标站反爬）。
"""
import random
import time
from typing import Tuple

from . import config

try:
    import requests  # type: ignore
    HAS_REQUESTS = True
except ImportError:  # pragma: no cover
    HAS_REQUESTS = False


def random_ua() -> str:
    return random.choice(config.ANTI_CRAWL["user_agents"])


def fetch(url: str, timeout: int = None, referer: str = None,
          cookies: str = None, retries: int = None) -> Tuple[str, str, str]:
    """抓取页面，返回 (html, final_url, error)；error 非空表示失败。

    final_url 用于检测"强制登录跳转"类封禁信号。
    失败按 retries 指数退避重试（默认取 config.ANTI_CRAWL["retry_times"]）。
    """
    timeout = timeout or config.ANTI_CRAWL["timeout"]
    retries = config.ANTI_CRAWL["retry_times"] if retries is None else retries
    headers = {
        "User-Agent": random_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                  "image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        # 浏览器指纹头：ZOL 等站点对无指纹请求返回精简版页面（商品列表不全）
        "sec-ch-ua": '"Chromium";v="126", "Not)A;Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "Upgrade-Insecure-Requests": "1",
    }
    if referer:
        headers["Referer"] = referer
    if cookies:
        headers["Cookie"] = cookies

    if HAS_REQUESTS:
        last_err = ""
        for attempt in range(retries + 1):
            try:
                r = requests.get(url, headers=headers, timeout=timeout,
                                 allow_redirects=True)
                if r.status_code >= 400 and attempt < retries:
                    time.sleep(config.ANTI_CRAWL["download_delay"] * (attempt + 1))
                    continue
                return r.text, r.url, ""
            except Exception as e:
                last_err = str(e)
                if attempt < retries:
                    time.sleep(config.ANTI_CRAWL["download_delay"] * (attempt + 1))
        return "", url, last_err

    # urllib 兜底（标准库，无 requests 时使用）
    import urllib.error
    import urllib.request
    last_err = ""
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read()
                charset = resp.headers.get_content_charset() or "utf-8"
                return body.decode(charset, errors="replace"), resp.geturl(), ""
        except Exception as e:
            last_err = str(e)
            if attempt < retries:
                time.sleep(config.ANTI_CRAWL["download_delay"] * (attempt + 1))
    return "", url, last_err
