"""云之家消息请求与响应的 Pydantic v2 模型。"""
from __future__ import annotations

from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict


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


class CardBaseInfo(BaseModel):
    templateId: str
    dataContent: str  # JSON 字符串


class CardParam(BaseModel):
    baseInfo: CardBaseInfo
    personInfoList: Optional[List[dict]] = None
    outTrackId: Optional[str] = None
    appId: Optional[str] = None


class YunzhijiaResponseData(BaseModel):
    """响应中 data 字段嵌套结构。"""

    model_config = ConfigDict(exclude_none=True)

    type: int = Field(2, description="消息类型，文本=2，卡片=25")
    content: Optional[str] = Field(None, description="返回的消息内容，type=25时可不传")
    forwardControl: Optional[str] = None  # "0"允许转发/"2"禁止
    param: Optional[CardParam] = None     # type=25 时必填


class YunzhijiaResponse(BaseModel):
    """云之家 Webhook 标准响应模型。"""

    model_config = ConfigDict(exclude_none=True)

    success: bool = True
    data: YunzhijiaResponseData
