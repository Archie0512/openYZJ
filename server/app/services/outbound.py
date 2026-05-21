"""出站消息推送。

用于异步 handler 在后台计算完成后，把结果主动推回云之家会话。

支持每台机器人独立的 webhook 推送地址（webhook_push_url），
未配置时 fallback 全局 yunzhijia_webhook_url。
"""
from __future__ import annotations

import logging

import httpx

from app.config import settings
from app.db import mongodb

log = logging.getLogger(__name__)


async def push_card_message(
    robot_id: str,
    sessionId: str,
    content: str,
    robot_code: str = "",
) -> None:
    """向云之家推送卡片消息。

    参数：
        robot_id   云之家机器人身份标识（与 payload.robotId 语义一致）
        sessionId  当前会话 ID
        content    要推送的文本内容
        robot_code 机器人代号，用于查找 per-robot 推送地址
    """
    payload = {
        "robotId": robot_id,
        "sessionId": sessionId,
        "content": content,
    }

    # 优先使用 per-robot webhook_push_url，fallback 全局配置
    url = settings.yunzhijia_webhook_url
    if robot_code:
        db = mongodb.get_db()
        doc = await db.robots.find_one(
            {"robot_code": robot_code}, {"webhook_push_url": 1}
        )
        if doc and doc.get("webhook_push_url"):
            url = doc["webhook_push_url"]

    log.info("[outbound] 推送消息 robot_id=%s code=%s session=%s", robot_id, robot_code, sessionId)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            log.info("[outbound] 推送成功 status=%d url=%s body=%s", resp.status_code, url[:50], resp.text[:200])
    except httpx.HTTPStatusError as e:
        log.error(
            "[outbound] 推送失败 robot_id=%s status=%d url=%s body=%s",
            robot_id, e.response.status_code, url[:50], e.response.text[:200],
        )
    except Exception as e:
        log.error("[outbound] 推送异常 robot_id=%s url=%s error=%s", robot_id, url[:50], e)
