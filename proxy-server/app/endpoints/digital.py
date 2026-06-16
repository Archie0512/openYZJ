"""数电票查询端点。

- 4.1.03 数电票发票批量查询
- 4.1.04 数电票发票单张查询
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query, Request

from app.auth import require_proxy_auth
from app import kdcloud_client as kdcloud
from app.models import (
    DigitalBatchQueryRequest,
    DigitalSingleQueryRequest,
    ProxyResponse,
)
from app.token_manager import get_token_manager

log = logging.getLogger(__name__)

router = APIRouter()


def _get_env(request: Request) -> str:
    return request.headers.get("X-Proxy-Env", "test")


@router.post("/batch-query", response_model=ProxyResponse)
async def digital_batch_query(
    req: DigitalBatchQueryRequest,
    request: Request,
    client_id: str = Depends(require_proxy_auth),
):
    """4.1.03 数电票发票批量查询。

    按 serialNos 数组批量查询数电票发票信息。
    """
    request.state.caller_id = client_id
    env = _get_env(request)
    tm = get_token_manager()
    access_token = await tm.get_valid_access_token(env)
    try:
        result = await kdcloud.batch_query_digital(req.model_dump(), access_token, req.requestId)
        return ProxyResponse(data=result, message="success")
    except Exception as e:
        log.error("[proxy] digital/batch-query 失败: %s", e)
        return ProxyResponse(code=500, message=f"数电票批量查询失败: {e}")


@router.get("/query/{serial_no}", response_model=ProxyResponse)
async def digital_single_query(
    serial_no: str,
    request: Request,
    client_id: str = Depends(require_proxy_auth),
    requestId: str = Query(..., description="调用方生成的唯一请求 ID"),
):
    """4.1.04 数电票发票单张查询。

    按 serialNo 查询单张数电票发票信息。
    """
    request.state.caller_id = client_id
    env = _get_env(request)
    tm = get_token_manager()
    access_token = await tm.get_valid_access_token(env)
    try:
        params = {"serialNo": serial_no, **dict(request.query_params)}
        result = await kdcloud.single_query_digital(params, access_token, requestId)
        return ProxyResponse(data=result, message="success")
    except Exception as e:
        log.error("[proxy] digital/single-query 失败: %s", e)
        return ProxyResponse(code=500, message=f"数电票单张查询失败: {e}")
