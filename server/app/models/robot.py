"""机器人配置 Pydantic v2 模型组。"""
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RobotDoc(BaseModel):
    """对应 robots 集合的存储结构（appSecret 加密后）。"""
    model_config = ConfigDict(extra="allow")

    robot_code: str
    robotId: Optional[str] = None        # 云之家激活前可为空
    name: str
    appSecret_encrypted: str
    status: str = "active"               # active | disabled
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RobotCreateReq(BaseModel):
    """创建 robot 入参（明文 appSecret，由路由加密后落库）。"""
    robot_code: str
    name: str
    appSecret: str
    robotId: Optional[str] = None
    description: Optional[str] = None


class RobotUpdateReq(BaseModel):
    """更新 robot 入参（所有字段可选）。"""
    name: Optional[str] = None
    appSecret: Optional[str] = None      # 提供则重新加密
    robotId: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None


class RobotPublic(BaseModel):
    """对外返回的安全视图（不含密钥）。"""
    robot_code: str
    robotId: Optional[str] = None
    name: str
    status: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
