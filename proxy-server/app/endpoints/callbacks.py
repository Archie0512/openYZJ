"""回调端点。

- 5.1.01 开票申请单回退接口
- 5.1.02 回调接口-按票回调
- 5.1.03 回调接口-按单回调

设计要点：
- **不使用 pydantic 解析 body**，直接读取 raw body，避免 Content-Type / 结构不符时
  在校验阶段被 FastAPI 挡回 422（那样连 body 都拿不到）。
- 回调为入站接收，不使用 HMAC 鉴权（金蝶不会携带 X-Proxy-* 头）。
- 响应必须严格按金蝶文档要求返回 ``{"message":"回调成功","errorCode":"0","success":true}``，
  否则金蝶会判定失败并反复重推（见 docs/kdcloud_md.md 5.1.03 返回示例）。

当前版本：记录日志 + 返回金蝶格式 ACK。持久化在 Commit 2/3 中引入。
"""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

log = logging.getLogger(__name__)

router = APIRouter()

# 金蝶发票云要求的回调 ACK 格式（见 docs/kdcloud_md.md 5.1.03 返回示例）
_ACK: dict[str, Any] = {"message": "回调成功", "errorCode": "0", "success": True}


async def _log_and_ack(request: Request, tag: str) -> JSONResponse:
    """读取原始 body、结构化落日志、返回金蝶要求的成功 ACK。"""
    raw = await request.body()
    content_type = request.headers.get("content-type", "")
    parsed: Any = None
    parse_err: str | None = None
    if raw:
        try:
            parsed = json.loads(raw)
        except Exception as e:  # noqa: BLE001 — 观测期不区分异常类型，全部记下来
            parse_err = f"{type(e).__name__}: {e}"

    log.info(
        "[proxy] callback/%s 收到回调 "
        "content_type=%s query=%s headers=%s raw_len=%d raw=%s parsed=%s parse_err=%s",
        tag,
        content_type,
        dict(request.query_params),
        dict(request.headers),
        len(raw),
        raw.decode("utf-8", errors="replace"),
        parsed,
        parse_err,
    )
    return JSONResponse(_ACK)


@router.post("/apply-return")
async def callback_apply_return(request: Request):
    """5.1.01 开票申请单回退接口（星瀚发起退回开票申请单）。"""
    return await _log_and_ack(request, "apply-return")


@router.post("/by-invoice")
async def callback_by_invoice(request: Request):
    """5.1.02 回调接口-按票回调（一次回调一张发票信息）。"""
    return await _log_and_ack(request, "by-invoice")


@router.post("/by-apply")
async def callback_by_apply(request: Request):
    """5.1.03 回调接口-按单回调（单据对应的所有发票开票完毕后一起回调）。"""
    return await _log_and_ack(request, "by-apply")
