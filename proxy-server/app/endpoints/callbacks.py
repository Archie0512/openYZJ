"""回调端点（存根实现）。

- 5.1.01 开票申请单回退接口
- 5.1.02 回调接口-按票回调
- 5.1.03 回调接口-按单回调

当前为存根实现：记录日志 + 返回成功响应。
后续 System A 的转发地址就绪后，增加实际转发逻辑。
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Request

from app.models import CallbackRequest, ProxyResponse

log = logging.getLogger(__name__)

router = APIRouter()


@router.post("/apply-return", response_model=ProxyResponse)
async def callback_apply_return(
    req: CallbackRequest,
    request: Request,
):
    """5.1.01 开票申请单回退接口（星瀚发起退回开票申请单）。

    回调接口为入站接收，不使用 HMAC 鉴权（金蝶不会携带 X-Proxy-* 头）。
    当前为存根实现，记录请求头 + 请求体后返回成功。
    """
    log.info("[proxy] callback/apply-return 收到回调 headers=%s body=%s", dict(request.headers), req.model_dump())
    return ProxyResponse(message="received")


@router.post("/by-invoice", response_model=ProxyResponse)
async def callback_by_invoice(
    req: CallbackRequest,
    request: Request,
):
    """5.1.02 回调接口-按票回调（一次回调一张发票信息）。

    回调接口为入站接收，不使用 HMAC 鉴权。
    """
    log.info("[proxy] callback/by-invoice 收到回调 headers=%s body=%s", dict(request.headers), req.model_dump())
    return ProxyResponse(message="received")


@router.post("/by-apply", response_model=ProxyResponse)
async def callback_by_apply(
    req: CallbackRequest,
    request: Request,
):
    """5.1.03 回调接口-按单回调（单据对应的所有发票开票完毕后一起回调）。

    回调接口为入站接收，不使用 HMAC 鉴权。
    """
    log.info("[proxy] callback/by-apply 收到回调 headers=%s body=%s", dict(request.headers), req.model_dump())
    return ProxyResponse(message="received")
