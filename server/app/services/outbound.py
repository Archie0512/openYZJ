"""出站消息推送。

用于异步 handler 在后台计算完成后，把结果主动推回云之家会话。
"""
from __future__ import annotations

import logging

import httpx

from app.config import settings

log = logging.getLogger(__name__)


async def push_card_message(robot_id: str, sessionId: str, content: str) -> None:
    """向云之家推送卡片消息。

    参数：
        robot_id  云之家机器人身份标识（与 payload.robotId 语义一致）
        sessionId 当前会话 ID
        content   要推送的文本内容
    """
    payload = {
        "robotId": robot_id,
        "sessionId": sessionId,
        "content": content,
    }
    url = settings.yunzhijia_webhook_url
    log.info("[outbound] 推送消息 robot_id=%s session=%s", robot_id, sessionId)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            log.info("[outbound] 推送成功 status=%d body=%s", resp.status_code, resp.text[:200])
    except httpx.HTTPStatusError as e:
        log.error(
            "[outbound] 推送失败 robot_id=%s status=%d body=%s",
            robot_id, e.response.status_code, e.response.text[:200],
        )
    except Exception as e:
        log.error("[outbound] 推送异常 robot_id=%s error=%s", robot_id, e)
