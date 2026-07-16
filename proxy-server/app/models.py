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
    callback_url: str = ""
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)


class ProxyClientCreateReq(BaseModel):
    """创建代理客户端入参。"""

    client_name: str
    api_key: str
    api_secret: str
    allowed_endpoints: list[str] = []
    rate_limit: int = 60
    callback_url: str = ""


class ProxyClientUpdateReq(BaseModel):
    """更新代理客户端入参（局部更新）。"""

    client_name: Optional[str] = None
    api_secret: Optional[str] = None
    allowed_endpoints: Optional[list[str]] = None
    rate_limit: Optional[int] = None
    status: Optional[str] = None
    callback_url: Optional[str] = None


class ProxyClientPublic(BaseModel):
    """对外返回的安全视图（不含密钥）。"""

    client_id: str
    client_name: str
    api_key: str
    allowed_endpoints: list[str] = []
    rate_limit: int = 60
    callback_url: str = ""
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

    requestId: str
    bills: list[dict]
    autoInvoice: bool = False
    autoMerge: bool = False


class InvoiceRevokeRequest(BaseModel):
    """1.1.02 开票申请单撤回。

    直接透传客户端请求体数据到金蝶 API。
    金蝶要求 data 内层字段：serialNos（单据编号数组），可选 orgCode / sellerTaxpayerId。
    """

    model_config = ConfigDict(extra="allow")

    requestId: str


class InvoiceApplyQueryRequest(BaseModel):
    """1.1.03 开票申请单发票查询。"""

    model_config = ConfigDict(extra="allow")

    requestId: str
    applyId: str


class VehicleInfoQueryRequest(BaseModel):
    """2.2.15 机动车信息查询（数电专用）。"""

    model_config = ConfigDict(extra="allow")

    requestId: str


class VehicleInvoiceRequest(BaseModel):
    """2.2.11 机动车发票开具。"""

    model_config = ConfigDict(extra="allow")

    requestId: str


class DigitalBatchQueryRequest(BaseModel):
    """4.1.03 数电票发票批量查询。"""

    model_config = ConfigDict(extra="allow")

    requestId: str
    serialNos: list[str]


class DigitalSingleQueryRequest(BaseModel):
    """4.1.04 数电票发票单张查询。

    金蝶 API ``data`` 内层字段：
    - ``serialNo`` 流水号（与 invoiceNum 二选一）
    - ``sellerTaxpayerId``（必填）销售方纳税人识别号
    """

    model_config = ConfigDict(extra="allow")

    requestId: str
    serialNo: str
    sellerTaxpayerId: str = Field(..., description="销售方纳税人识别号，金蝶 API 必填")


class VehicleRedFlushRequest(BaseModel):
    """2.2.13 机动车发票红冲。"""

    model_config = ConfigDict(extra="allow")

    requestId: str


# 注：回调请求（5.1.01/02/03）不使用 pydantic 模型，直接在 endpoints/callbacks.py
# 里读取 raw body 落库，避免第三方 Content-Type / 结构不符时 FastAPI 校验阶段返回 422。


# ── 出站转发相关 ──────────────────────────────────

class ForwardingConfigReq(BaseModel):
    """PUT /api/admin/forwarding-config 入参（运行时自动转发开关）。"""

    auto_forward_enabled: bool
