"""消息处理总入口：路由 → handler 调度，并兜底异常。

webhook 在验签 / 落库后调用 handle()，3s 内必须返回 YunzhijiaResponseData。
"""
from __future__ import annotations

import logging
import re
import time

from fastapi import BackgroundTasks

from app.models.yunzhijia import YunzhijiaPayload, YunzhijiaResponseData
from app.services.command_router import route

log = logging.getLogger(__name__)

# 同步 handler 总耗时硬上限（毫秒），超出则上层兜底
_SYNC_BUDGET_MS = 2500
FALLBACK_TEXT = "哎呀,出现了点小问题,要不等会再试试？"

_AT_MENTION_RE = re.compile(r"^@\S+\s*")


def _strip_at_mention(content: str) -> str:
    """去掉消息开头的 @机器人名 前缀。"""
    return _AT_MENTION_RE.sub("", content).strip()


async def handle(
    payload: YunzhijiaPayload,
    sessionId: str,
    bg: BackgroundTasks,
    robot_code: str = "",
) -> YunzhijiaResponseData:
    """路由并执行匹配的 handler。

    - 任何 handler 抛错都会被吞掉，统一返回 fallback 文案
    - 总耗时仅做日志监控；真正硬约束由 APICaller / 上层 timeout 协同保障
    """
    clean_content = _strip_at_mention(payload.content or "")
    handler = route(clean_content)
    log.info(
        "routed to handler=%s for content=%s",
        handler.name, clean_content[:50],
    )
    # 临时将 payload.content 替换为 clean_content 传给 handler
    original_content = payload.content
    payload.content = clean_content
    start = time.monotonic()
    try:
        result = await handler.handle(payload, sessionId, bg, robot_code=robot_code)
        cost_ms = int((time.monotonic() - start) * 1000)
        if not handler.is_async and cost_ms > _SYNC_BUDGET_MS:
            log.warning(
                "sync handler=%s exceeded budget cost_ms=%d > %d",
                handler.name, cost_ms, _SYNC_BUDGET_MS,
            )
        log.info("handler=%s done cost_ms=%d", handler.name, cost_ms)
        return result
    except Exception:  # noqa: BLE001
        log.exception("handler=%s crashed", handler.name)
        fallback = f"哎呀,出现了点小问题,要不等会再试试？(机器人:{robot_code})" if robot_code else FALLBACK_TEXT
        return YunzhijiaResponseData(type=2, content=fallback)
