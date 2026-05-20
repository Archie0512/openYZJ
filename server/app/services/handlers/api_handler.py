"""API Handler：演示"接收信息后调用其他 API 接口"的核心能力（同步快速模式）。

调用 https://httpbin.org/anything 作为公共 echo 接口演示，将其响应中的 origin 字段
拼接到回复文本，整体耗时控制在 ≤2s。
"""
from __future__ import annotations

import logging
import time
from typing import Any, List

from fastapi import BackgroundTasks

from app.models.command_log import ApiCallLog, CommandLogDoc
from app.models.yunzhijia import YunzhijiaPayload, YunzhijiaResponseData
from app.services.api_caller import APICaller
from app.services.handlers.base import BaseHandler
from app.services.storage import save_command_log

log = logging.getLogger(__name__)

# 演示用公共 API（GET 形式，echo 请求信息）
DEMO_API_URL = "https://httpbin.org/anything"
FALLBACK_TEXT = "调用外部接口失败，请稍后重试"


class ApiHandler(BaseHandler):
    name = "api_call"
    is_async = False

    def __init__(self) -> None:
        # 严格 2s 超时，预留 0.5s 给 DB / 序列化等开销
        self.caller = APICaller(timeout=2.0)

    async def handle(
        self,
        payload: YunzhijiaPayload,
        sessionId: str,
        bg: BackgroundTasks,
        robot_code: str = "",
    ) -> YunzhijiaResponseData:
        """同步调用外部 API 并组装回复。"""
        start = time.monotonic()
        external_calls: List[ApiCallLog] = []
        status = "success"
        error_msg: str | None = None
        reply_content: str

        try:
            body, call_log = await self.caller.call(
                "GET", DEMO_API_URL, params={"source": "openyzj"}
            )
            external_calls.append(call_log)
            origin = _extract_origin(body)
            reply_content = (
                f"已调用外部 API，请求来自 {origin}，耗时 {call_log.cost_ms}ms"
            )
        except Exception as e:  # noqa: BLE001
            # APICaller 内部已记录 ApiCallLog（含 error / cost_ms）但不返回，
            # 这里补一条最小记录便于落库观察
            external_calls.append(
                ApiCallLog(
                    url=DEMO_API_URL,
                    method="GET",
                    error=str(e),
                    cost_ms=int((time.monotonic() - start) * 1000),
                )
            )
            status = "failed"
            error_msg = str(e)
            reply_content = FALLBACK_TEXT
            log.warning("api_handler external call failed: %s", e)

        cost_ms = int((time.monotonic() - start) * 1000)

        bg.add_task(
            _write_command_log,
            payload=payload,
            sessionId=sessionId,
            reply_content=reply_content,
            cost_ms=cost_ms,
            status=status,
            error_msg=error_msg,
            external_calls=external_calls,
        )

        return YunzhijiaResponseData(type=2, content=reply_content)


def _extract_origin(body: Any) -> str:
    """从 httpbin /anything 响应里取出 origin 字段。"""
    if isinstance(body, dict):
        return str(body.get("origin") or "未知来源")
    return "未知来源"


async def _write_command_log(
    payload: YunzhijiaPayload,
    sessionId: str,
    reply_content: str,
    cost_ms: int,
    status: str,
    error_msg: str | None,
    external_calls: List[ApiCallLog],
) -> None:
    """后台写入 command_logs（含 external_api_calls 数组）。"""
    doc = CommandLogDoc(
        msgId=payload.msgId,
        robotId=payload.robotId,
        sessionId=sessionId,
        command="api",
        handler="api_call",
        status=status,
        request_content=payload.content,
        response_content=reply_content,
        external_api_calls=external_calls,
        cost_ms=cost_ms,
        error=error_msg,
    )
    await save_command_log(doc)
