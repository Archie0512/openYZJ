"""AI Handler：异步占位模式。

1. 主流程立即返回"思考中..."占位响应，确保 3s 内回复云之家
2. BackgroundTask 完成真实 AI 调用后：
   - 更新 command_logs 状态为 success/failed
   - 调用 outbound.push_card_message（v2 占位）将结果推回云之家
"""
from __future__ import annotations

import logging
import time

from fastapi import BackgroundTasks

from app.models.command_log import CommandLogDoc
from app.models.yunzhijia import YunzhijiaPayload, YunzhijiaResponseData
from app.services.ai_caller import AICaller
from app.services.handlers.base import BaseHandler
from app.services.outbound import push_card_message
from app.services.storage import save_command_log, update_command_log

log = logging.getLogger(__name__)

PLACEHOLDER_REPLY = "正在思考中，结果稍后推送…"
# AI 触发前缀（路由层已做小写处理，此处仅用于剥离正文）
_AI_PREFIXES = ("/ai", "#ai")


class AIHandler(BaseHandler):
    name = "ai"
    is_async = True

    def __init__(self) -> None:
        self.caller = AICaller()

    async def handle(
        self,
        payload: YunzhijiaPayload,
        sessionId: str,
        bg: BackgroundTasks,
        robot_code: str = "",
    ) -> YunzhijiaResponseData:
        """主流程：注册后台任务并立即返回占位文本。"""
        # 已经命中本 handler 才会进来，剥离前缀拿到真正的 prompt
        prompt = _strip_prefix(payload.content)

        # 关键：主流程不等待真实计算，直接返回占位响应
        bg.add_task(
            _run_ai,
            caller=self.caller,
            payload=payload,
            sessionId=sessionId,
            prompt=prompt,
            robot_code=robot_code,
        )

        return YunzhijiaResponseData(type=2, content=PLACEHOLDER_REPLY)


def _strip_prefix(content: str) -> str:
    """剥离 /ai 或 #AI 前缀（兼容空格 / 冒号分隔符），返回剩余正文。"""
    raw = (content or "").strip()
    lower = raw.lower()
    for p in _AI_PREFIXES:
        if lower.startswith(p):
            tail = raw[len(p):]
            # 兼容 ": " / " " 等分隔符
            return tail.lstrip(" :：\t").strip()
    return raw


async def _run_ai(
    caller: AICaller,
    payload: YunzhijiaPayload,
    sessionId: str,
    prompt: str,
    robot_code: str = "",
) -> None:
    """后台任务：写 pending → 调 AI → 更新 success/failed → 推送 outbound。"""
    start = time.monotonic()

    # ── 1) 先写 pending command_log ──
    pending_doc = CommandLogDoc(
        msgId=payload.msgId,
        robotId=payload.robotId,
        sessionId=sessionId,
        command="ai",
        handler="ai",
        status="pending",
        request_content=payload.content,
    )
    await save_command_log(pending_doc)

    # ── 2) 调用 AI ──
    try:
        reply = await caller.chat(prompt or "（空 prompt）")
        cost_ms = int((time.monotonic() - start) * 1000)
        await update_command_log(
            {"msgId": payload.msgId, "command": "ai", "status": "pending"},
            {
                "status": "success",
                "response_content": reply,
                "cost_ms": cost_ms,
            },
        )
        # ── 3) 推送结果 ──
        await push_card_message(payload.robotId, sessionId, reply, robot_code=robot_code)
        log.info("ai_handler success cost_ms=%d", cost_ms)
    except Exception as e:  # noqa: BLE001
        cost_ms = int((time.monotonic() - start) * 1000)
        await update_command_log(
            {"msgId": payload.msgId, "command": "ai", "status": "pending"},
            {
                "status": "failed",
                "error": str(e),
                "cost_ms": cost_ms,
            },
        )
        log.warning("ai_handler failed cost_ms=%d err=%s", cost_ms, e)
