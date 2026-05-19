"""messages 集合文档模型（落库结构）。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MessageDoc(BaseModel):
    """对应 messages 集合的文档结构。

    字段语义说明：
      - robot_code: 业务侧机器人代号，来自 webhook url path 参数
      - robotId / robotName / operatorOpenid / operatorName / msgId / content / type / time:
        云之家 webhook 原始 payload 字段
      - sessionId: 来自 header sessionId，用于关联 30 分钟会话
      - sign_algo: 实际命中的签名算法（sha256 / sha1），便于排查
      - is_test: 是否测试请求（robotId == 'test-robotId'），便于后续清理
      - received_at: 落库时间（UTC）
      - raw_payload: 原始请求体全量保留以备追溯
    """

    model_config = ConfigDict(extra="allow")

    robot_code: str
    robotId: str
    robotName: str
    operatorOpenid: str
    operatorName: str
    msgId: str
    content: str
    type: int
    time: int
    sessionId: str
    sign_algo: Optional[str] = None
    is_test: bool = False
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raw_payload: dict = Field(default_factory=dict)
