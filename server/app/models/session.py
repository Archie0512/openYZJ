"""sessions 集合文档模型：30 分钟会话上下文。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SessionDoc(BaseModel):
    """对应 sessions 集合，承载 30 分钟会话上下文。

    TTL 索引建立在 updated_at 字段，expireAfterSeconds=1800。
    每次同一 sessionId 命中时刷新 updated_at，相当于让 TTL 倒计时重置，
    实现"最后一次活动后 30 分钟"的语义。
    """

    model_config = ConfigDict(extra="allow")

    sessionId: str
    robot_code: str
    robotId: str
    operatorOpenid: str
    operatorName: str
    last_msgId: Optional[str] = None
    last_content: Optional[str] = None
    message_count: int = 0
    # 留给后续 handler 写入会话上下文（例如多轮对话状态机）
    context: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
