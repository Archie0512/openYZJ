"""开票端点。

- 1.1.01 开票申请单生成及开票
- 1.1.02 开票申请单撤回
- 1.1.03 开票申请单发票查询
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request

from app.auth import require_proxy_auth
from app import kdcloud_client as kdcloud
from app.models import (
    InvoiceCreateRequest,
    InvoiceRevokeRequest,
    ProxyResponse,
)
from app.token_manager import get_token_manager

log = logging.getLogger(__name__)

router = APIRouter()


def _get_env(request: Request) -> str:
    """从 header 获取目标环境。"""
    return request.headers.get("X-Proxy-Env", "test")


@router.post("/create", response_model=ProxyResponse)
async def invoice_create(
    req: InvoiceCreateRequest,
    request: Request,
    client_id: str = Depends(require_proxy_auth),
):
    """1.1.01 开票申请单生成及开票。

    支持 autoInvoice（自动开票）和 autoMerge（自动合并）功能。
    """
    request.state.caller_id = client_id
    env = _get_env(request)
    tm = get_token_manager()
    access_token = await tm.get_valid_access_token(env)
    try:
        result = await kdcloud.create_invoice(req.model_dump(), access_token)
        return ProxyResponse(data=result, message="success")
    except Exception as e:
        log.error("[proxy] invoice/create 失败: %s", e)
        return ProxyResponse(code=500, message=f"开票申请单生成失败: {e}")


@router.post("/revoke", response_model=ProxyResponse)
async def invoice_revoke(
    req: InvoiceRevokeRequest,
    request: Request,
    client_id: str = Depends(require_proxy_auth),
):
    """1.1.02 开票申请单撤回。"""
    request.state.caller_id = client_id
    env = _get_env(request)
    tm = get_token_manager()
    access_token = await tm.get_valid_access_token(env)
    try:
        result = await kdcloud.revoke_invoice(req.model_dump(), access_token)
        return ProxyResponse(data=result, message="success")
    except Exception as e:
        log.error("[proxy] invoice/revoke 失败: %s", e)
        return ProxyResponse(code=500, message=f"开票申请单撤回失败: {e}")


@router.get("/query/{apply_id}", response_model=ProxyResponse)
async def invoice_query(
    apply_id: str,
    request: Request,
    client_id: str = Depends(require_proxy_auth),
):
    """1.1.03 开票申请单发票查询。"""
    request.state.caller_id = client_id
    env = _get_env(request)
    tm = get_token_manager()
    access_token = await tm.get_valid_access_token(env)
    try:
        params = {"applyId": apply_id, **dict(request.query_params)}
        result = await kdcloud.query_invoice_apply(params, access_token)
        return ProxyResponse(data=result, message="success")
    except Exception as e:
        log.error("[proxy] invoice/query 失败: %s", e)
        return ProxyResponse(code=500, message=f"开票申请单查询失败: {e}")
