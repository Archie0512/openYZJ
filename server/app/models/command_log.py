"""command_logs 集合文档模型：指令处理结果与外部 API 调用记录。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ApiCallLog(BaseModel):
    """单次外部 API 调用的轻量记录。"""

    url: str
    method: str = "POST"
    status_code: Optional[int] = None
    cost_ms: Optional[int] = None
    error: Optional[str] = None


class CommandLogDoc(BaseModel):
    """记录一次 webhook 处理过程中的指令路由与外部 API 调用详情。

    任务 #4 暂不真正写入此集合，仅定义结构与索引；
    任务 #5 接入 handler 路由后由 services.storage.save_command_log 写入。
    """

    model_config = ConfigDict(extra="allow")

    msgId: str
    robotId: str
    sessionId: str
    command: str  # 路由命中的命令名（task #5 填充，task #4 默认 'echo'）
    handler: str  # 命中的 handler 名
    status: str  # success / failed / pending
    request_content: str
    response_content: Optional[str] = None
    external_api_calls: List[ApiCallLog] = Field(default_factory=list)
    cost_ms: Optional[int] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
