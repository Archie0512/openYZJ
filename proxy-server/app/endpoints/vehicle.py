"""机动车端点。

- 2.2.15 机动车信息查询（数电专用）
- 2.2.11 机动车发票开具（请求体数据来源于 2.2.15 响应）
- 2.2.13 机动车发票红冲
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request

from app.auth import require_proxy_auth
from app import kdcloud_client as kdcloud
from app.models import (
    ProxyResponse,
    VehicleInfoQueryRequest,
    VehicleInvoiceRequest,
    VehicleRedFlushRequest,
)
from app.token_manager import get_token_manager

log = logging.getLogger(__name__)

router = APIRouter()


def _get_env(request: Request) -> str:
    return request.headers.get("X-Proxy-Env", "test")


@router.post("/info", response_model=ProxyResponse)
async def vehicle_info(
    req: VehicleInfoQueryRequest,
    request: Request,
    client_id: str = Depends(require_proxy_auth),
):
    """2.2.15 机动车信息查询（数电专用）。

    返回的车辆信息是 2.2.11 机动车发票开具的前置依赖数据。
    """
    request.state.caller_id = client_id
    env = _get_env(request)
    tm = get_token_manager()
    access_token = await tm.get_valid_access_token(env)
    try:
        result = await kdcloud.query_vehicle_info(req.model_dump(), access_token, req.requestId)
        return ProxyResponse(data=result, message="success")
    except Exception as e:
        log.error("[proxy] vehicle/info 失败: %s", e)
        return ProxyResponse(code=500, message=f"机动车信息查询失败: {e}")


@router.post("/invoice", response_model=ProxyResponse)
async def vehicle_invoice(
    req: VehicleInvoiceRequest,
    request: Request,
    client_id: str = Depends(require_proxy_auth),
):
    """2.2.11 机动车发票开具。

    请求体中的车辆信息字段通常来自 2.2.15 的响应 data。
    代理层不做字段级校验，由 System A 负责组装完整请求体。
    """
    request.state.caller_id = client_id
    env = _get_env(request)
    tm = get_token_manager()
    access_token = await tm.get_valid_access_token(env)
    try:
        result = await kdcloud.issue_vehicle_invoice(req.model_dump(), access_token, req.requestId)
        return ProxyResponse(data=result, message="success")
    except Exception as e:
        log.error("[proxy] vehicle/invoice 失败: %s", e)
        return ProxyResponse(code=500, message=f"机动车发票开具失败: {e}")


@router.post("/red-flush", response_model=ProxyResponse)
async def vehicle_red_flush(
    req: VehicleRedFlushRequest,
    request: Request,
    client_id: str = Depends(require_proxy_auth),
):
    """2.2.13 机动车发票红冲。

    注：本接口已实现代码，暂不进行实际测试。
    需要测试时请提供机动车发票数据。
    """
    request.state.caller_id = client_id
    env = _get_env(request)
    tm = get_token_manager()
    access_token = await tm.get_valid_access_token(env)
    try:
        result = await kdcloud.red_flush_vehicle(req.model_dump(), access_token, req.requestId)
        return ProxyResponse(data=result, message="success")
    except Exception as e:
        log.error("[proxy] vehicle/red-flush 失败: %s", e)
        return ProxyResponse(code=500, message=f"机动车发票红冲失败: {e}")
