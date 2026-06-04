from __future__ import annotations

import threading
import time

import requests

from config.settings import RATE_LIMIT

_lock = threading.Lock()
_next_request_at = 0.0


def _wait_for_rate_limit() -> None:
    if RATE_LIMIT <= 0:
        return

    interval = 1 / RATE_LIMIT

    global _next_request_at
    with _lock:
        now = time.monotonic()
        wait = max(0.0, _next_request_at - now)
        _next_request_at = max(now, _next_request_at) + interval

    if wait:
        time.sleep(wait)


def get(url: str, **kwargs) -> requests.Response:
    _wait_for_rate_limit()
    return requests.get(url, **kwargs)
