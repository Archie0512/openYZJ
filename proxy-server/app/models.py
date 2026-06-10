"""代理网关数据模型。

- ProxyClientDoc: proxy_clients 集合文档（独立鉴权）
- ProxyResponse: 统一响应格式
- 业务请求模型：按金蝶发票云 API 接口定义的请求体
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ── 代理调用方（MongoDB 文档）────────────────────────

class ProxyClientDoc(BaseModel):
    """对应 proxy_clients 集合的存储结构。"""

    model_config = ConfigDict(extra="allow")

    client_id: str
    client_name: str
    api_key: str
    api_secret_encrypted: str
    status: str = "active"
    allowed_endpoints: list[str] = []
    rate_limit: int = 60
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)


class ProxyClientCreateReq(BaseModel):
    """创建代理客户端入参。"""

    client_name: str
    api_key: str
    api_secret: str
    allowed_endpoints: list[str] = []
    rate_limit: int = 60


class ProxyClientUpdateReq(BaseModel):
    """更新代理客户端入参（局部更新）。"""

    client_name: Optional[str] = None
    api_secret: Optional[str] = None
    allowed_endpoints: Optional[list[str]] = None
    rate_limit: Optional[int] = None
    status: Optional[str] = None


class ProxyClientPublic(BaseModel):
    """对外返回的安全视图（不含密钥）。"""

    client_id: str
    client_name: str
    api_key: str
    allowed_endpoints: list[str] = []
    rate_limit: int = 60
    status: str
    created_at: datetime
    updated_at: datetime


# ── 统一响应 ──────────────────────────────────────────

class ProxyResponse(BaseModel):
    """代理层统一响应格式。"""

    code: int = 0
    data: Any = None
    message: str = "success"


# ── 业务请求模型 ──────────────────────────────────────


class InvoiceCreateRequest(BaseModel):
    """1.1.01 开票申请单生成及开票。"""

    model_config = ConfigDict(extra="allow")

    bills: list[dict]
    autoInvoice: bool = False
    autoMerge: bool = False


class InvoiceRevokeRequest(BaseModel):
    """1.1.02 开票申请单撤回。"""

    model_config = ConfigDict(extra="allow")

    applyId: str


class InvoiceApplyQueryRequest(BaseModel):
    """1.1.03 开票申请单发票查询。"""

    model_config = ConfigDict(extra="allow")

    applyId: str


class VehicleInfoQueryRequest(BaseModel):
    """2.2.15 机动车信息查询（数电专用）。"""

    model_config = ConfigDict(extra="allow")


class VehicleInvoiceRequest(BaseModel):
    """2.2.11 机动车发票开具。"""

    model_config = ConfigDict(extra="allow")


class DigitalBatchQueryRequest(BaseModel):
    """4.1.03 数电票发票批量查询。"""

    model_config = ConfigDict(extra="allow")

    serialNos: list[str]


class DigitalSingleQueryRequest(BaseModel):
    """4.1.04 数电票发票单张查询。"""

    model_config = ConfigDict(extra="allow")

    serialNo: str


class VehicleRedFlushRequest(BaseModel):
    """2.2.13 机动车发票红冲。"""

    model_config = ConfigDict(extra="allow")


# ── 回调请求模型（存根实现用）─────────────────────────

class CallbackRequest(BaseModel):
    """5.1.01/02/03 回调请求通用模型。"""

    model_config = ConfigDict(extra="allow")
