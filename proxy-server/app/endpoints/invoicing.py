"""开票端点。

- 1.1.01 开票申请单生成及开票
- 1.1.02 开票申请单撤回
- 1.1.03 开票申请单发票查询
"""
from __future__ import annotations

import copy
import logging

from fastapi import APIRouter, Depends, Query, Request

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


def _translate_bills(bills: list[dict], auto_invoice: bool, auto_merge: bool) -> list[dict]:
    """将 System A 的 bills 转换为金蝶 BILL.PUSH 要求的格式。

    1. 注入 autoInvoice / autoMerge（金蝶要求每张单据内部携带）
    2. 字段名映射: items → billDetail, billSourceId → detailId
    """
    result = []
    for bill in bills:
        b = copy.deepcopy(bill)
        # 注入自动开票/合并标记
        if auto_invoice:
            b.setdefault("autoInvoice", "1")
        if auto_merge:
            b.setdefault("autoMerge", "1")
        # 字段名映射: items → billDetail
        if "items" in b and "billDetail" not in b:
            b["billDetail"] = b.pop("items")
        # billDetail 内部映射: billSourceId → detailId
        if "billDetail" in b and isinstance(b["billDetail"], list):
            for detail in b["billDetail"]:
                if "billSourceId" in detail and "detailId" not in detail:
                    detail["detailId"] = detail.pop("billSourceId")
        result.append(b)
    return result


@router.post("/create", response_model=ProxyResponse)
async def invoice_create(
    req: InvoiceCreateRequest,
    request: Request,
    client_id: str = Depends(require_proxy_auth),
):
    """1.1.01 开票申请单生成及开票。

    支持 autoInvoice（自动开票）和 autoMerge（自动合并）功能。
    代理层自动将顶层 autoInvoice/autoMerge 注入每张单据，并将字段名映射为金蝶规范格式。
    """
    request.state.caller_id = client_id
    env = _get_env(request)
    tm = get_token_manager()
    access_token = await tm.get_valid_access_token(env)
    try:
        # 字段名转换 + 注入 autoInvoice / autoMerge 到每条单据
        data_content = _translate_bills(req.bills, req.autoInvoice, req.autoMerge)
        result = await kdcloud.create_invoice(data_content, access_token, req.requestId)
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
        result = await kdcloud.revoke_invoice(req.model_dump(), access_token, req.requestId)
        return ProxyResponse(data=result, message="success")
    except Exception as e:
        log.error("[proxy] invoice/revoke 失败: %s", e)
        return ProxyResponse(code=500, message=f"开票申请单撤回失败: {e}")


@router.get("/query/{apply_id}", response_model=ProxyResponse)
async def invoice_query(
    apply_id: str,
    request: Request,
    client_id: str = Depends(require_proxy_auth),
    requestId: str = Query(..., description="调用方生成的唯一请求 ID"),
):
    """1.1.03 开票申请单发票查询。"""
    request.state.caller_id = client_id
    env = _get_env(request)
    tm = get_token_manager()
    access_token = await tm.get_valid_access_token(env)
    try:
        # 构造查询参数，合并 query_params 中的额外字段
        data_content = {"serialNo": apply_id, **dict(request.query_params)}
        result = await kdcloud.query_invoice_apply(data_content, access_token, requestId)
        return ProxyResponse(data=result, message="success")
    except Exception as e:
        log.error("[proxy] invoice/query 失败: %s", e)
        return ProxyResponse(code=500, message=f"开票申请单查询失败: {e}")
