"""Echo Handler：直接原样回显消息内容（同步快速模式）。

匹配规则：默认兜底 handler，以及明确 /echo 前缀。
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from fastapi import BackgroundTasks

from app.models.command_log import CommandLogDoc
from app.models.yunzhijia import YunzhijiaPayload, YunzhijiaResponseData
from app.services.handlers.base import BaseHandler
from app.services.storage import save_command_log

log = logging.getLogger(__name__)


class EchoHandler(BaseHandler):
    name = "echo"
    is_async = False

    async def handle(
        self,
        payload: YunzhijiaPayload,
        sessionId: str,
        bg: BackgroundTasks,
    ) -> YunzhijiaResponseData:
        """直接回显消息内容，3s 内同步返回。"""
        start = time.monotonic()
        reply_content = f"收到：{payload.content}"
        cost_ms = int((time.monotonic() - start) * 1000)

        # 异步写入 command_log（不阻塞响应返回）
        bg.add_task(
            _write_command_log,
            payload=payload,
            sessionId=sessionId,
            reply_content=reply_content,
            cost_ms=cost_ms,
        )

        return YunzhijiaResponseData(type=2, content=reply_content)


async def _write_command_log(
    payload: YunzhijiaPayload,
    sessionId: str,
    reply_content: str,
    cost_ms: int,
) -> None:
    """后台写入 command_logs 集合（echo 成功记录）。"""
    doc = CommandLogDoc(
        msgId=payload.msgId,
        robotId=payload.robotId,
        sessionId=sessionId,
        command="echo",
        handler="echo",
        status="success",
        request_content=payload.content,
        response_content=reply_content,
        cost_ms=cost_ms,
    )
    await save_command_log(doc)
