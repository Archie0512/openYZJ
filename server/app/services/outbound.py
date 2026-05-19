"""出站消息推送（v2 占位）。

用于异步 handler 在后台计算完成后，把结果主动推回云之家会话。
"""
from __future__ import annotations

import logging

log = logging.getLogger(__name__)


async def push_card_message(robot_id: str, sessionId: str, content: str) -> None:
    """TODO(v2): 接入云之家“主动推送卡片消息”接口。

    - Researcher 已确认 v1 阶段官方文档未公开此接口，等待补充
    - 当前实现仅打印日志，便于联调时观察异步链路是否到达此步骤
    - 任务 #5 暂不实现真实推送，但保留此函数签名作为后续扩展锚点

    参数：
        robot_id  云之家机器人身份标识（与 payload.robotId 语义一致）
        sessionId 当前会话 ID
        content   要推送的文本内容
    """
    log.info(
        "[outbound TODO] robot_id=%s session=%s content=%s",
        robot_id, sessionId, content[:100],
    )
