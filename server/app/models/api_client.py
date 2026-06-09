"""第三方 API 客户端 Pydantic v2 模型组。"""
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ApiClientDoc(BaseModel):
    """对应 api_clients 集合的存储结构。"""

    model_config = ConfigDict(extra="allow")

    client_id: str
    client_name: str  # 如 "宝德ERP", "金斗云道闸"
    api_key: str  # 分配的 API Key
    api_secret_encrypted: str  # Fernet 加密的 Secret
    allowed_endpoints: List[str] = []  # 端点白名单，空=全部允许
    rate_limit: int = 100  # 每分钟请求上限
    status: str = "active"  # active | disabled
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApiClientCreateReq(BaseModel):
    """创建 API 客户端入参（明文 api_secret，由路由加密后落库）。"""

    client_name: str
    api_key: str
    api_secret: str  # 明文，由路由加密后落库
    allowed_endpoints: List[str] = []
    rate_limit: int = 100


class ApiClientPublic(BaseModel):
    """对外返回的安全视图（不含密钥）。"""

    client_id: str
    client_name: str
    api_key: str
    allowed_endpoints: List[str] = []
    rate_limit: int = 100
    status: str
    created_at: datetime
    updated_at: datetime
