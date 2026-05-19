"""同步快速 HTTP 客户端封装。

设计目标：
  - 用于 task #5 中 api_handler 等"同步快速模式" handler 调外部 API
  - 严格执行 3 秒超时硬约束：默认 timeout=2.0s，配合上层 handler 自身 ≤2.5s 总耗时预算
  - 调用结果统一返回 (响应体, ApiCallLog)，便于上层把 ApiCallLog 写入 command_logs.external_api_calls
"""
from __future__ import annotations

import logging
import time
from typing import Any, Optional, Tuple

import httpx

from app.models.command_log import ApiCallLog

log = logging.getLogger(__name__)


class APICaller:
    """异步 HTTP 调用器（同步快速模式专用）。"""

    def __init__(self, timeout: float = 2.0):
        # timeout 上限 2.0s，避免 webhook 总耗时超过 3s 硬约束
        self.timeout = timeout

    async def call(
        self,
        method: str,
        url: str,
        *,
        json: Optional[dict] = None,
        headers: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> Tuple[Any, ApiCallLog]:
        """发起一次 HTTP 调用并返回 (响应体, 调用日志)。

        - 优先按 JSON 解析响应；若解析失败则返回原始文本
        - 任意阶段抛错时由调用方捕获，但 ApiCallLog 仍记录耗时 / error
        """
        log_entry = ApiCallLog(url=url, method=method.upper())
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.request(
                    method, url, json=json, headers=headers, params=params
                )
                log_entry.status_code = resp.status_code
                log_entry.cost_ms = int((time.monotonic() - start) * 1000)
                resp.raise_for_status()
                # 优先 json 解析，失败回退到 text
                try:
                    return resp.json(), log_entry
                except Exception:  # noqa: BLE001
                    return resp.text, log_entry
        except Exception as e:  # noqa: BLE001
            log_entry.cost_ms = int((time.monotonic() - start) * 1000)
            log_entry.error = str(e)
            log.warning("api_caller failed url=%s err=%s", url, e)
            raise
