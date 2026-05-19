"""云之家消息请求与响应的 Pydantic v2 模型。"""
from __future__ import annotations

from pydantic import BaseModel, Field


class YunzhijiaPayload(BaseModel):
    """云之家 Webhook 请求 Body 模型。"""

    type: int = Field(..., description="消息类型，文本=2，卡片=25")
    robotId: str = Field(..., description="加密的机器人 ID")
    robotName: str = Field(..., description="机器人名称")
    operatorOpenid: str = Field(..., description="加密的发送者 ID")
    operatorName: str = Field(..., description="发送者名称")
    time: int = Field(..., description="当前时间戳（毫秒）")
    msgId: str = Field(..., description="加密的消息 ID")
    content: str = Field(..., description="消息内容")


class YunzhijiaResponseData(BaseModel):
    """响应中 data 字段嵌套结构。"""

    type: int = Field(2, description="消息类型，文本=2，卡片=25")
    content: str = Field(..., description="返回的消息内容")


class YunzhijiaResponse(BaseModel):
    """云之家 Webhook 标准响应模型。"""

    success: bool = True
    data: YunzhijiaResponseData
